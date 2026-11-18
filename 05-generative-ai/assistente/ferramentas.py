"""Ferramenta do agente: consulta as ordens de serviço reais geradas pelo robô RPA."""

import json
import re
import unicodedata
from pathlib import Path

ARQUIVO_OS = Path(__file__).resolve().parents[2] / "06-rpa" / "saida" / "ordens_servico.json"

PADRAO_STATUS = re.compile(r"\b(quando|status|situação|situacao|andamento|prazo|já|ja|vão|vao|vai)\b.*\b(arrum|consert|tapar|reparo|ordem|buraco)", re.I)
PADRAO_RUA = re.compile(r"\b(?:rua|r\.|avenida|av\.|travessa|tv\.|alameda|praça)\s+([A-Za-zÀ-ÿ0-9 ]{3,40}?)(?=[,.?!]|\s+(?:n[º°o]|tem|está|esta|vai|vão|já|ja)\b|$)", re.I)


def sem_acento(t):
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")


def quer_status(pergunta: str):
    """Roteador: a pergunta é sobre o andamento de um problema numa rua específica?"""
    rua = PADRAO_RUA.search(pergunta)
    return rua.group(1).strip() if rua and PADRAO_STATUS.search(pergunta) else None


def consultar_ordens(rua: str):
    if not ARQUIVO_OS.exists():
        return None, "A base de ordens de serviço ainda não foi gerada (rode o robô em 06-rpa)."
    try:
        ordens = json.loads(ARQUIVO_OS.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "A base de ordens de serviço está indisponível no momento."
    alvo = sem_acento(rua)
    achadas = [o for o in ordens if alvo and alvo in sem_acento(o.get("endereco", ""))]
    return achadas, None


def formatar_resultado(rua, achadas, erro):
    if erro:
        return erro
    if not achadas:
        return (f"Não encontrei ocorrências registradas automaticamente em '{rua}'. Se você viu um problema lá, "
                "registre na tela \"Registrar\" do app ou na Central 156. O caminhão de coleta também passa pela rua "
                "e pode detectar o problema nas próximas rotas.")
    linhas = [f"Encontrei {len(achadas)} ocorrência(s) em '{rua}':"]
    for o in achadas:
        linhas.append(f"- **{o['id']}**: buraco em {o['endereco']}. Status: **{o['status']}**. "
                      f"{o.get('descricao', '')}")
    linhas.append("Os prazos dependem da prioridade calculada (Crítica 24 h, Alta 72 h, Média 7 dias, Baixa 15 dias).")
    return "\n".join(linhas)
