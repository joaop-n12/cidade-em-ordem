"""
Validação do robô com um conjunto de teste ROTULADO (dados sintéticos, sem dados pessoais).

Gabarito: 10 buracos reais em ruas do Tatuapé (SP) e 4 falsos alarmes (sombra, tampa de bueiro, lombada).
Para cada buraco geramos detecções com ruído de GPS de até ~8 m, como aconteceria com o caminhão passando:
  - alguns vistos só pela câmera (vários quadros), outros só pelo sensor, outros pelos dois;
Também injetamos 3 registros inválidos (coordenada fora da cidade, confiança 1.7, campo faltando).

Medimos:
  1. Agrupamento: o robô encontrou o mesmo número de pontos do gabarito? (pureza dos grupos)
  2. Decisão: buraco real -> OS; falso alarme -> revisão humana (matriz de confusão, precisão, recall)
  3. Validação de entrada: os 3 inválidos foram rejeitados?
  4. Falhas tratadas: arquivo ausente, JSON corrompido, API fora do ar (URL inválida) e idempotência.

Uso: python validacao/validar.py
"""

import json
import random
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))
import robo_cidade_em_ordem as robo  # noqa: E402

rnd = random.Random(2026)
M = 1 / 111_000  # ~1 metro em graus de latitude

# (id, lat, lon, real?, cenário)
GABARITO = [
    ("B01", -23.54020, -46.57630, True, "câmera(5 quadros, conf alta) + sensor 2,4 g"),
    ("B02", -23.54310, -46.57120, True, "sensor severo 3,4 g / 13 cm"),
    ("B03", -23.53870, -46.57940, True, "câmera 4 quadros conf 0,7-0,9"),
    ("B04", -23.54500, -46.57900, True, "sensor 2 passagens 2,1 g"),
    ("B05", -23.54150, -46.57400, True, "câmera 3 quadros + sensor 1,9 g"),
    ("B06", -23.53700, -46.57500, True, "câmera 6 quadros conf alta"),
    ("B07", -23.54600, -46.57300, True, "sensor 3,1 g"),
    ("B08", -23.53950, -46.57100, True, "câmera 2 quadros + sensor 2,6 g"),
    ("B09", -23.54420, -46.57610, True, "sensor 2 passagens 1,8 g / 6 cm"),
    ("B10", -23.53800, -46.57250, True, "câmera 3 quadros conf 0,55-0,65"),
    ("F01", -23.54080, -46.57520, False, "sombra: câmera 1 quadro conf 0,41"),
    ("F02", -23.54230, -46.57280, False, "tampa de bueiro: sensor 1 passagem 1,7 g"),
    ("F03", -23.53650, -46.57800, False, "mancha no asfalto: câmera 1 quadro conf 0,62"),
    ("F04", -23.54700, -46.57650, False, "lombada: sensor 1 passagem 1,6 g, 0 cm"),
]


def ruido():
    return rnd.uniform(-8, 8) * M


def gerar():
    cam, sen = [], []
    def c(gid, lat, lon, confs):
        for i, cf in enumerate(confs):
            cam.append({"id_origem": f"cv-{gid}-{i}", "lat": lat + ruido(), "lon": lon + ruido(), "confianca": cf})
    def s(gid, lat, lon, g, prof, passagens=1):
        sen.append({"id_origem": f"iot-{gid}", "lat": lat + ruido(), "lon": lon + ruido(), "impacto_g": g,
                    "profundidade_cm": prof, "passagens": passagens})
    g = {x[0]: x for x in GABARITO}
    c("B01", *g["B01"][1:3], [0.82, 0.88, 0.91, 0.79, 0.85]); s("B01", *g["B01"][1:3], 2.4, 6.5)
    s("B02", *g["B02"][1:3], 3.4, 13.0)
    c("B03", *g["B03"][1:3], [0.71, 0.84, 0.9, 0.77])
    s("B04", *g["B04"][1:3], 2.1, 5.0, passagens=2)
    c("B05", *g["B05"][1:3], [0.66, 0.72, 0.58]); s("B05", *g["B05"][1:3], 1.9, 4.5)
    c("B06", *g["B06"][1:3], [0.9, 0.93, 0.88, 0.91, 0.86, 0.9])
    s("B07", *g["B07"][1:3], 3.1, 9.0)
    c("B08", *g["B08"][1:3], [0.74, 0.69]); s("B08", *g["B08"][1:3], 2.6, 7.0)
    s("B09", *g["B09"][1:3], 1.8, 6.0, passagens=2)
    c("B10", *g["B10"][1:3], [0.55, 0.61, 0.65])
    c("F01", *g["F01"][1:3], [0.41])
    s("F02", *g["F02"][1:3], 1.7, 0.5)
    c("F03", *g["F03"][1:3], [0.62])
    s("F04", *g["F04"][1:3], 1.6, 0.0)
    # registros inválidos
    cam.append({"id_origem": "cv-invalido-1", "lat": -22.9, "lon": -43.2, "confianca": 0.9})       # Rio de Janeiro
    cam.append({"id_origem": "cv-invalido-2", "lat": -23.54, "lon": -46.57, "confianca": 1.7})     # confiança > 1
    sen.append({"id_origem": "iot-invalido-3", "lon": -46.57, "impacto_g": 2.0})                    # sem latitude
    return cam, sen


def mais_proximo(o):
    return min(GABARITO, key=lambda g: robo.distancia_m((o.lat, o.lon), (g[1], g[2])))


def main():
    pasta = BASE / "execucao_teste"
    if pasta.exists():
        shutil.rmtree(pasta)
    entrada, saida = pasta / "entrada", pasta / "saida"
    entrada.mkdir(parents=True)
    cam, sen = gerar()
    (entrada / "deteccoes_visao.json").write_text(json.dumps(cam, indent=1), encoding="utf-8")
    (entrada / "deteccoes_iot.json").write_text(json.dumps(sen, indent=1), encoding="utf-8")

    print("\n######## TESTE 1: lote rotulado ########")
    resumo, ocs = robo.executar(entrada, saida, offline=True)

    # 1. agrupamento
    grupos_por_gab = {}
    for o in ocs:
        grupos_por_gab.setdefault(mais_proximo(o)[0], []).append(o)
    puros = sum(1 for o in ocs if len({d.id_origem.split("-")[1] for d in o.deteccoes}) == 1)

    # 2. decisão
    vp = fp = vn = fn = 0
    linhas = []
    for gid, lat, lon, real, cen in GABARITO:
        os_ = grupos_por_gab.get(gid, [])
        decisao = "OS" if any(o.decisao == "OS" for o in os_) else ("REVISAO" if os_ else "NÃO ENCONTRADO")
        acerto = (decisao == "OS") == real
        vp += real and decisao == "OS"; fn += real and decisao != "OS"
        fp += (not real) and decisao == "OS"; vn += (not real) and decisao != "OS"
        linhas.append(f"| {gid} | {'buraco' if real else 'falso alarme'} | {cen} | {decisao} | {'✔' if acerto else '✘'} |")

    print("\n## Resultado da validação\n")
    print(f"- Detecções geradas: {len(cam) + len(sen)} (3 inválidas)")
    print(f"- Rejeitadas na validação: {resumo['numeros']['rejeitadas']} (esperado 3)")
    print(f"- Pontos no gabarito: {len(GABARITO)} | ocorrências encontradas pelo robô: {len(ocs)} | grupos puros: {puros}/{len(ocs)}")
    print("\n| Ponto | Verdade | Cenário | Decisão do robô | Acerto |\n|---|---|---|---|---|")
    print("\n".join(linhas))
    precisao = vp / (vp + fp) if vp + fp else 0
    recall = vp / (vp + fn) if vp + fn else 0
    print(f"\nMatriz de confusão (OS = positivo): VP={vp} FP={fp} FN={fn} VN={vn}")
    print(f"Precisão = {precisao:.2f} | Recall = {recall:.2f} | Acurácia = {(vp + vn) / len(GABARITO):.2f}")

    print("\n######## TESTE 2: idempotência (rodar de novo o mesmo lote) ########")
    r2, _ = robo.executar(entrada, saida, offline=True)
    print(f"OS novas na 2ª execução: {r2['numeros']['OS novas']} (esperado 0) | já emitidas: {r2['numeros']['OS já emitidas (não duplicadas)']}")

    print("\n######## TESTE 3: arquivo do sensor ausente + JSON da câmera corrompido ########")
    e3 = pasta / "entrada_falha"
    e3.mkdir()
    (e3 / "deteccoes_visao.json").write_text("{isto não é json", encoding="utf-8")
    r3, _ = robo.executar(e3, pasta / "saida_falha", offline=True)
    print(f"Execução terminou sem exceção. Ocorrências: {r3['numeros']['ocorrências após agrupamento']}")

    print("\n######## TESTE 4: API de clima fora do ar (URL inválida) ########")
    import os
    os.environ["RPA_URL_CLIMA"] = "https://api-inexistente.cidadeemordem.invalid/forecast"
    robo.Enriquecedor.endereco = lambda self, lat, lon: {"endereco": "teste", "tipo_via": "local", "origem": "teste"}
    r4, _ = robo.executar(entrada, pasta / "saida_api", offline=False)
    print(f"Falhas de API tratadas: {r4['numeros']['falhas de API tratadas']} | OS geradas mesmo assim: {r4['numeros']['OS novas']}")


if __name__ == "__main__":
    main()
