"""
Cidade em Ordem - Robô RPA + IA de triagem de ocorrências urbanas
Global Solution 2026.2 - AI for Robotic Process Automation

Ponto de entrada único:  python robo_cidade_em_ordem.py  [--offline] [--entrada PASTA] [--saida PASTA]

Fluxo de ponta a ponta (sem intervenção humana):
  1. COLETA        lê as detecções da câmera (visão computacional) e do sensor IoT do caminhão (arquivos JSON)
  2. VALIDAÇÃO     descarta registros inválidos (coordenada fora da cidade, confiança fora de 0-1...) com log
  3. AGRUPAMENTO   IA não supervisionada (DBSCAN com distância geográfica) junta detecções do mesmo buraco
  4. ENRIQUECIMENTO APIs públicas: endereço e tipo de via (OpenStreetMap/Nominatim) e chuva prevista (Open-Meteo)
  5. DECISÃO       escore de prioridade explicável + regra de confirmação (câmera e sensor, ou reincidência)
                   -> ordem de serviço (OS) ou fila de REVISÃO HUMANA quando a evidência é fraca
  6. SAÍDAS        planilha Excel (OS + revisão), JSON para o front-end, relatório HTML da execução, log
  7. IDEMPOTÊNCIA  ocorrência já emitida em execução anterior não gera OS duplicada

Toda falha previsível (arquivo ausente, JSON corrompido, API fora do ar, timeout) é registrada em log
e segue por um caminho seguro, sem interromper a execução.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")  # evita aviso do scikit-learn no Windows
import numpy as np
import requests
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from sklearn.cluster import DBSCAN

BASE = Path(__file__).resolve().parent
RAIO_MESMO_PONTO_M = 25          # detecções a até 25 m são o mesmo problema
LIMITES_CIDADE = {"lat": (-24.01, -23.35), "lon": (-46.83, -46.36)}   # município de São Paulo (aprox.)
USER_AGENT = "CidadeEmOrdem-GS2026/1.0 (prototipo academico)"

log = logging.getLogger("robo")


# ----------------------------------------------------------------------------------------------
# Configuração e utilitários
# ----------------------------------------------------------------------------------------------
def configurar_log(pasta_saida: Path):
    pasta_saida.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    log.setLevel(logging.INFO)
    log.handlers.clear()
    for h in (logging.StreamHandler(sys.stdout), logging.FileHandler(pasta_saida / "execucao.log", encoding="utf-8", mode="w")):
        h.setFormatter(fmt)
        log.addHandler(h)


def carregar_env():
    """Chaves e configurações ficam no .env (fora do código e do repositório)."""
    env = BASE / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if "=" in linha and not linha.strip().startswith("#"):
                k, v = linha.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def com_retentativa(func, tentativas=3, espera_inicial=1.0, descricao="chamada"):
    """Executa func() com retry e espera exponencial (1 s, 2 s, 4 s)."""
    espera = espera_inicial
    for i in range(1, tentativas + 1):
        try:
            return func()
        except Exception as e:  # noqa: BLE001 - qualquer falha de rede cai aqui
            log.warning("%s falhou (tentativa %d/%d): %s", descricao, i, tentativas, e)
            if i == tentativas:
                raise
            time.sleep(espera)
            espera *= 2


def distancia_m(a, b):
    r = 6371000
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


# ----------------------------------------------------------------------------------------------
# 1. Coleta e 2. Validação
# ----------------------------------------------------------------------------------------------
@dataclass
class Deteccao:
    id_origem: str
    fonte: str              # "camera" ou "sensor"
    lat: float
    lon: float
    confianca: float | None = None
    impacto_g: float | None = None
    profundidade_cm: float | None = None
    passagens: int = 1


def ler_json(caminho: Path, rotulo: str):
    if not caminho.exists():
        log.error("Arquivo de %s não encontrado: %s - seguindo sem essa fonte", rotulo, caminho)
        return []
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        if not isinstance(dados, list):
            raise ValueError("o conteúdo deveria ser uma lista")
        log.info("Lidas %d detecções de %s (%s)", len(dados), rotulo, caminho.name)
        return dados
    except (json.JSONDecodeError, ValueError) as e:
        log.error("Arquivo de %s inválido (%s) - seguindo sem essa fonte", rotulo, e)
        return []


def validar(item: dict, fonte: str) -> Deteccao:
    lat, lon = float(item["lat"]), float(item.get("lon", item.get("lng")))
    if not (LIMITES_CIDADE["lat"][0] <= lat <= LIMITES_CIDADE["lat"][1] and LIMITES_CIDADE["lon"][0] <= lon <= LIMITES_CIDADE["lon"][1]):
        raise ValueError(f"coordenada fora do município ({lat}, {lon})")
    conf = item.get("confianca")
    if conf is not None and not 0 <= float(conf) <= 1:
        raise ValueError(f"confiança fora de 0-1: {conf}")
    g = item.get("impacto_g")
    if g is not None and not 0 <= float(g) <= 16:
        raise ValueError(f"impacto fora da faixa do sensor: {g}")
    return Deteccao(
        id_origem=str(item.get("id_origem") or f"{fonte}-{lat:.6f}-{lon:.6f}"),
        fonte=fonte, lat=lat, lon=lon,
        confianca=float(conf) if conf is not None else None,
        impacto_g=float(g) if g is not None else None,
        profundidade_cm=float(item["profundidade_cm"]) if item.get("profundidade_cm") is not None else None,
        passagens=int(item.get("passagens", 1)),
    )


def coletar(pasta_entrada: Path):
    brutos = [(i, "camera") for i in ler_json(pasta_entrada / "deteccoes_visao.json", "visão computacional")]
    brutos += [(i, "sensor") for i in ler_json(pasta_entrada / "deteccoes_iot.json", "sensor IoT")]
    validas, rejeitadas, ids = [], [], set()
    for item, fonte in brutos:
        try:
            d = validar(item, fonte)
            if d.id_origem in ids:
                rejeitadas.append({"registro": item, "motivo": "id repetido no lote"})
                continue
            ids.add(d.id_origem)
            validas.append(d)
        except (KeyError, TypeError, ValueError) as e:
            log.warning("Registro rejeitado (%s): %s", e, str(item)[:120])
            rejeitadas.append({"registro": item, "motivo": str(e)})
    log.info("Validação: %d válidas, %d rejeitadas", len(validas), len(rejeitadas))
    return validas, rejeitadas


# ----------------------------------------------------------------------------------------------
# 3. Agrupamento (IA não supervisionada)
# ----------------------------------------------------------------------------------------------
@dataclass
class Ocorrencia:
    id: str
    lat: float
    lon: float
    deteccoes: list = field(default_factory=list)
    endereco: str = ""
    tipo_via: str = "local"
    chuva_mm_24h: float | None = None
    escore: int = 0
    prioridade: str = ""
    prazo: str = ""
    fatores: list = field(default_factory=list)
    decisao: str = ""
    motivo_decisao: str = ""

    @property
    def fontes(self):
        return sorted({d.fonte for d in self.deteccoes})

    @property
    def confianca_max(self):
        v = [d.confianca for d in self.deteccoes if d.confianca is not None]
        return max(v) if v else None

    @property
    def impacto_max(self):
        v = [d.impacto_g for d in self.deteccoes if d.impacto_g is not None]
        return max(v) if v else None

    @property
    def profundidade_max(self):
        v = [d.profundidade_cm for d in self.deteccoes if d.profundidade_cm is not None]
        return max(v) if v else None

    @property
    def passagens(self):
        """Evidências independentes: cada passagem do sensor conta 1; a câmera conta 1 (quadros seguidos = mesma passagem)."""
        sensor = sum(d.passagens for d in self.deteccoes if d.fonte == "sensor")
        return sensor + (1 if any(d.fonte == "camera" for d in self.deteccoes) else 0)


def agrupar(deteccoes: list[Deteccao]) -> list[Ocorrencia]:
    if not deteccoes:
        return []
    coords = np.radians([[d.lat, d.lon] for d in deteccoes])
    rotulos = DBSCAN(eps=RAIO_MESMO_PONTO_M / 6371000, min_samples=1, metric="haversine").fit_predict(coords)
    grupos: dict[int, list[Deteccao]] = {}
    for d, r in zip(deteccoes, rotulos):
        grupos.setdefault(int(r), []).append(d)
    ocorrencias = []
    for itens in grupos.values():
        lat = float(np.mean([d.lat for d in itens]))
        lon = float(np.mean([d.lon for d in itens]))
        # ID estável: mesmo ponto (grade de ~20 m) gera o mesmo ID em execuções diferentes -> idempotência
        chave = f"buraco:{round(lat / 0.0002) * 0.0002:.4f}:{round(lon / 0.0002) * 0.0002:.4f}"
        ocorrencias.append(Ocorrencia(id="OC-" + hashlib.sha1(chave.encode()).hexdigest()[:10].upper(), lat=lat, lon=lon, deteccoes=itens))
    log.info("Agrupamento DBSCAN (raio %d m): %d detecções -> %d ocorrências", RAIO_MESMO_PONTO_M, len(deteccoes), len(ocorrencias))
    return ocorrencias


# ----------------------------------------------------------------------------------------------
# 4. Enriquecimento por APIs (com cache, timeout, retry e caminho seguro)
# ----------------------------------------------------------------------------------------------
MAPA_VIA = {"motorway": "arterial", "trunk": "arterial", "primary": "arterial", "secondary": "coletora",
            "tertiary": "coletora", "residential": "local", "living_street": "local", "service": "local", "unclassified": "local"}


class Enriquecedor:
    def __init__(self, pasta_estado: Path, offline: bool):
        self.offline = offline
        self.cache_path = pasta_estado / "cache_enderecos.json"
        self.cache = json.loads(self.cache_path.read_text(encoding="utf-8")) if self.cache_path.exists() else {}
        self.sessao = requests.Session()
        self.sessao.headers["User-Agent"] = USER_AGENT
        self.falhas_api = 0

    def endereco(self, lat, lon):
        chave = f"{lat:.5f},{lon:.5f}"
        if chave in self.cache:
            return self.cache[chave]
        if self.offline:
            return {"endereco": f"Coordenadas {lat:.5f}, {lon:.5f}", "tipo_via": "local", "origem": "offline"}

        def chamar():
            r = self.sessao.get("https://nominatim.openstreetmap.org/reverse",
                                params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 17}, timeout=10)
            r.raise_for_status()
            return r.json()
        try:
            dados = com_retentativa(chamar, descricao="Nominatim (endereço)")
            end = dados.get("address", {})
            texto = ", ".join(x for x in [end.get("road"), end.get("house_number"), end.get("suburb") or end.get("city_district")] if x)
            res = {"endereco": texto or dados.get("display_name", "")[:80], "tipo_via": MAPA_VIA.get(dados.get("type"), "local"), "origem": "nominatim"}
            self.cache[chave] = res
            time.sleep(1.1)  # política de uso do Nominatim: no máximo 1 requisição por segundo
            return res
        except Exception:
            self.falhas_api += 1
            log.error("Endereço indisponível para (%.5f, %.5f) - usando coordenadas e via 'local'", lat, lon)
            return {"endereco": f"Coordenadas {lat:.5f}, {lon:.5f}", "tipo_via": "local", "origem": "falha_api"}

    def chuva_24h(self, lat, lon):
        if self.offline:
            return None
        url = os.getenv("RPA_URL_CLIMA", "https://api.open-meteo.com/v1/forecast")

        def chamar():
            r = self.sessao.get(url, params={"latitude": lat, "longitude": lon, "hourly": "precipitation",
                                             "forecast_days": 1, "timezone": "America/Sao_Paulo"}, timeout=10)
            r.raise_for_status()
            return r.json()
        try:
            dados = com_retentativa(chamar, descricao="Open-Meteo (chuva)")
            total = float(sum(v or 0 for v in dados["hourly"]["precipitation"]))
            log.info("Previsão de chuva nas próximas 24 h: %.1f mm", total)
            return total
        except Exception:
            self.falhas_api += 1
            log.error("Previsão do tempo indisponível - prioridade calculada sem o fator chuva")
            return None

    def salvar_cache(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=1), encoding="utf-8")


# ----------------------------------------------------------------------------------------------
# 5. Decisão: prioridade explicável e confirmação
# ----------------------------------------------------------------------------------------------
def priorizar(o: Ocorrencia):
    fatores = [("Buraco na via", 35)]
    if o.confianca_max is not None:
        fatores.append((f"Câmera: confiança máxima {o.confianca_max:.0%}", round(o.confianca_max * 15)))
    if o.impacto_max is not None and o.impacto_max >= 1.5:
        g = o.impacto_max
        fatores.append((f"Sensor: impacto de {g:.1f} g", 20 if g >= 3 else 12 if g >= 2.2 else 6))
    if o.profundidade_max:
        p = o.profundidade_max
        fatores.append((f"Profundidade {p:.0f} cm", 15 if p >= 10 else 8 if p >= 5 else 3))
    if o.tipo_via == "arterial":
        fatores.append(("Via arterial (alto fluxo)", 10))
    elif o.tipo_via == "coletora":
        fatores.append(("Via coletora", 5))
    if o.chuva_mm_24h and o.chuva_mm_24h >= 5:
        fatores.append((f"Chuva prevista ({o.chuva_mm_24h:.0f} mm): buraco fica escondido pela água", 8))
    if o.passagens > 1:
        fatores.append((f"{o.passagens} passagens/detecções independentes", min(o.passagens * 4, 16)))
    escore = min(100, sum(p for _, p in fatores))
    o.escore, o.fatores = escore, fatores
    o.prioridade, o.prazo = (("Crítica", "24 horas") if escore >= 80 else ("Alta", "72 horas") if escore >= 60
                             else ("Média", "7 dias") if escore >= 40 else ("Baixa", "15 dias"))

    # Regra de confirmação: duas evidências independentes, ou uma evidência forte e repetida.
    camera_forte = o.confianca_max is not None and o.confianca_max >= 0.5
    sensor_forte = o.impacto_max is not None and (o.impacto_max >= 3.0 or (o.profundidade_max or 0) >= 10)
    n_quadros = sum(1 for d in o.deteccoes if d.fonte == "camera" and (d.confianca or 0) >= 0.5)
    if "camera" in o.fontes and "sensor" in o.fontes:
        o.decisao, o.motivo_decisao = "OS", "Confirmado por câmera e sensor"
    elif sensor_forte:
        o.decisao, o.motivo_decisao = "OS", "Impacto/profundidade severos medidos pelo sensor"
    elif camera_forte and n_quadros >= 2:
        o.decisao, o.motivo_decisao = "OS", f"Câmera detectou em {n_quadros} quadros com confiança alta"
    elif o.passagens >= 2 and "sensor" in o.fontes:
        o.decisao, o.motivo_decisao = "OS", "Sensor detectou em passagens diferentes"
    else:
        o.decisao, o.motivo_decisao = "REVISAO", "Evidência única ou fraca: precisa de olhar humano antes de mobilizar equipe"


# ----------------------------------------------------------------------------------------------
# 6. Saídas
# ----------------------------------------------------------------------------------------------
def para_front(o: Ocorrencia):
    return {
        "id": o.id, "tipo": "buraco", "fonte": "camera+sensor" if len(o.fontes) == 2 else o.fontes[0],
        "lat": round(o.lat, 6), "lng": round(o.lon, 6), "endereco": o.endereco, "via": o.tipo_via,
        "confianca": o.confianca_max, "impactoG": o.impacto_max, "profundidadeCm": o.profundidade_max,
        "reincidencias": max(o.passagens - 1, 0), "chovendo": bool(o.chuva_mm_24h and o.chuva_mm_24h >= 5),
        "descricao": f"Detectado automaticamente pelo caminhão de coleta. {o.motivo_decisao}.",
        "status": "Aberta" if o.decisao == "OS" else "Em vistoria",
    }


def salvar_excel(caminho: Path, emitidas, revisao):
    wb = Workbook()
    cab = ["Ocorrência", "Endereço", "Tipo de via", "Fontes", "Detecções", "Confiança câmera", "Impacto (g)",
           "Profundidade (cm)", "Escore", "Prioridade", "Prazo", "Motivo", "Latitude", "Longitude"]
    for ws, titulo, linhas in ((wb.active, "Ordens de serviço", emitidas), (wb.create_sheet(), "Revisão humana", revisao)):
        ws.title = titulo
        ws.append(cab)
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor="0B5CAD")
        for o in linhas:
            ws.append([o.id, o.endereco, o.tipo_via, "+".join(o.fontes), len(o.deteccoes),
                       round(o.confianca_max, 2) if o.confianca_max is not None else "", o.impacto_max or "",
                       o.profundidade_max or "", o.escore, o.prioridade, o.prazo, o.motivo_decisao, round(o.lat, 6), round(o.lon, 6)])
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(45, max(12, max(len(str(c.value or "")) for c in col) + 2))
    wb.save(caminho)


def salvar_relatorio(caminho: Path, resumo, emitidas, revisao, rejeitadas):
    linhas = "".join(
        f"<tr><td>{o.id}</td><td>{o.endereco}</td><td>{o.prioridade}</td><td>{o.escore}</td><td>{'+'.join(o.fontes)}</td>"
        f"<td>{o.motivo_decisao}</td><td>{'<br>'.join(f'{m} (+{p})' for m, p in o.fatores)}</td></tr>"
        for o in sorted(emitidas, key=lambda x: -x.escore))
    rev = "".join(f"<li>{o.id} · {o.endereco} · {o.motivo_decisao}</li>" for o in revisao)
    rej = "".join(f"<li>{r['motivo']}</li>" for r in rejeitadas)
    html = f"""<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Relatório de execução - Cidade em Ordem</title>
<style>body{{font-family:system-ui;margin:2rem;color:#1d2433}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ccd;padding:6px;font-size:14px;vertical-align:top}}th{{background:#0b5cad;color:#fff}}.k{{display:inline-block;margin:0 1rem 1rem 0;padding:.6rem 1rem;border:1px solid #ccd;border-radius:8px}}</style>
<h1>Robô Cidade em Ordem: relatório de execução</h1><p>{resumo['inicio']} → {resumo['fim']} ({resumo['duracao_s']} s) · modo {'offline' if resumo['offline'] else 'online'}</p>
{''.join(f'<span class="k"><b>{v}</b><br>{k}</span>' for k, v in resumo['numeros'].items())}
<h2>Ordens de serviço emitidas</h2><table><tr><th>ID</th><th>Endereço</th><th>Prioridade</th><th>Escore</th><th>Fontes</th><th>Motivo</th><th>Fatores</th></tr>{linhas}</table>
<h2>Fila de revisão humana</h2><ul>{rev or '<li>vazia</li>'}</ul><h2>Registros rejeitados na validação</h2><ul>{rej or '<li>nenhum</li>'}</ul></html>"""
    caminho.write_text(html, encoding="utf-8")


# ----------------------------------------------------------------------------------------------
# Execução principal
# ----------------------------------------------------------------------------------------------
def executar(pasta_entrada: Path, pasta_saida: Path, offline: bool = False):
    inicio = datetime.now()
    configurar_log(pasta_saida)
    carregar_env()
    log.info("=== Robô Cidade em Ordem iniciado (entrada=%s, offline=%s) ===", pasta_entrada, offline)
    pasta_estado = pasta_saida / "estado"
    pasta_estado.mkdir(parents=True, exist_ok=True)
    estado_path = pasta_estado / "ocorrencias_emitidas.json"
    try:
        emitidas_antes = set(json.loads(estado_path.read_text(encoding="utf-8"))) if estado_path.exists() else set()
    except json.JSONDecodeError:
        log.error("Estado de execuções anteriores corrompido - recriando (pode haver OS repetida para revisão)")
        emitidas_antes = set()

    validas, rejeitadas = coletar(pasta_entrada)
    if not validas:
        log.warning("Nenhuma detecção válida para processar. Encerrando com relatório vazio.")
    ocorrencias = agrupar(validas)

    enr = Enriquecedor(pasta_estado, offline)
    chuva = enr.chuva_24h(*(ocorrencias[0].lat, ocorrencias[0].lon)) if ocorrencias else None
    for o in ocorrencias:
        try:
            info = enr.endereco(o.lat, o.lon)
            o.endereco, o.tipo_via, o.chuva_mm_24h = info["endereco"], info["tipo_via"], chuva
            priorizar(o)
        except Exception as e:  # noqa: BLE001 - nenhuma ocorrência derruba o lote
            o.decisao, o.motivo_decisao = "REVISAO", f"Erro inesperado no processamento ({e})"
            log.exception("Falha ao processar %s - enviada para revisão humana", o.id)
    enr.salvar_cache()

    novas = [o for o in ocorrencias if o.decisao == "OS" and o.id not in emitidas_antes]
    repetidas = [o for o in ocorrencias if o.decisao == "OS" and o.id in emitidas_antes]
    revisao = [o for o in ocorrencias if o.decisao == "REVISAO"]
    for o in repetidas:
        log.info("%s já tinha OS emitida em execução anterior - não duplicada (idempotência)", o.id)
    for o in sorted(novas, key=lambda x: -x.escore):
        log.info("OS emitida: %s | %s | %s (%d) | %s", o.id, o.endereco, o.prioridade, o.escore, o.motivo_decisao)

    pasta_saida.mkdir(parents=True, exist_ok=True)
    (pasta_saida / "ordens_servico.json").write_text(
        json.dumps([para_front(o) for o in novas + repetidas + revisao], ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        salvar_excel(pasta_saida / "ordens_servico.xlsx", novas + repetidas, revisao)
    except PermissionError:
        alt = pasta_saida / f"ordens_servico_{inicio:%H%M%S}.xlsx"
        log.error("Planilha aberta em outro programa - salvando como %s", alt.name)
        salvar_excel(alt, novas + repetidas, revisao)
    with open(pasta_saida / "fila_revisao_humana.csv", "w", encoding="utf-8-sig") as f:
        f.write("ocorrencia;endereco;fontes;confianca;impacto_g;motivo\n")
        for o in revisao:
            f.write(f"{o.id};{o.endereco};{'+'.join(o.fontes)};{o.confianca_max or ''};{o.impacto_max or ''};{o.motivo_decisao}\n")
    estado_path.write_text(json.dumps(sorted(emitidas_antes | {o.id for o in novas}), indent=1), encoding="utf-8")

    fim = datetime.now()
    resumo = {
        "inicio": f"{inicio:%d/%m/%Y %H:%M:%S}", "fim": f"{fim:%H:%M:%S}", "duracao_s": round((fim - inicio).total_seconds(), 1),
        "offline": offline,
        "numeros": {"detecções lidas": len(validas) + len(rejeitadas), "rejeitadas": len(rejeitadas),
                    "ocorrências após agrupamento": len(ocorrencias), "OS novas": len(novas),
                    "OS já emitidas (não duplicadas)": len(repetidas), "revisão humana": len(revisao),
                    "falhas de API tratadas": enr.falhas_api},
    }
    salvar_relatorio(pasta_saida / "relatorio_execucao.html", resumo, novas + repetidas, revisao, rejeitadas)
    log.info("=== Fim: %s ===", json.dumps(resumo["numeros"], ensure_ascii=False))
    return resumo, ocorrencias


def main():
    ap = argparse.ArgumentParser(description="Robô RPA Cidade em Ordem")
    ap.add_argument("--entrada", default=str(BASE / "entrada"))
    ap.add_argument("--saida", default=str(BASE / "saida"))
    ap.add_argument("--offline", action="store_true", help="não chama APIs externas (para testes)")
    a = ap.parse_args()
    executar(Path(a.entrada), Path(a.saida), a.offline)


if __name__ == "__main__":
    main()
