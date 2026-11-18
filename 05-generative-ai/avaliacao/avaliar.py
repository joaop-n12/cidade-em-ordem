"""
Avaliação do assistente com 24 perguntas de teste (resultado em avaliacao/resultados.md).

Para cada pergunta definimos o comportamento esperado:
  - rota esperada (rag, ferramenta, emergencia, fora_do_tema)
  - para rag: documento que deveria ser recuperado e palavras-chave que uma resposta correta precisa conter

Métricas:
  - Acurácia de roteamento (guardrails + ferramenta + RAG)
  - Recuperação: acerto@4 (a fonte esperada está entre os 4 trechos recuperados)
  - Resposta: cobertura de palavras-chave, presença de citação [n] e números sem suporte no contexto
Uso: python avaliacao/avaliar.py   (com ou sem chave de LLM; sem chave avalia o modo extrativo)
"""

import json
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
env = BASE / ".env"
if env.exists():
    import os
    for linha in env.read_text(encoding="utf-8").splitlines():
        if "=" in linha and not linha.strip().startswith("#"):
            k, v = linha.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from assistente.rag import Assistente  # noqa: E402

SP, CTB, LBI, CART, PNRS = ("sp_lei_15442_2011.docx", "ctb_lei_9503_1997.html", "lbi_lei_13146_2015.html",
                            "cartilha_calcadas_sp_2024.pdf", "pnrs_lei_12305_2010.txt")

TESTES = [
    # (pergunta, rota esperada, fonte esperada, palavras-chave)
    ("Quem tem que consertar a calçada na frente da minha casa?", "rag", SP, ["responsável", "imóvel"]),
    ("Quando uma calçada é considerada em mau estado?", "rag", SP, ["buracos", "desníveis"]),
    ("A prefeitura quebrou minha calçada numa obra, quem paga?", "rag", SP, ["Município", "repar"]),
    ("A raiz de uma árvore estragou minha calçada, preciso arrumar?", "rag", SP, ["árvore", "30"]),
    ("Qual a largura mínima da faixa livre da calçada?", "rag", SP, ["1,20"]),
    ("Vou ser multado direto pela calçada quebrada?", "rag", SP, ["Notificação Orientativa"]),
    ("Quanto tempo tenho para regularizar a calçada depois da multa?", "rag", SP, ["60"]),
    ("Terreno baldio precisa estar limpo?", "rag", SP, ["limpos"]),
    ("O poder público responde por danos causados por falha na manutenção da via?", "rag", CTB, ["objetivamente"]),
    ("Trânsito seguro é um direito de quem?", "rag", CTB, ["direito de todos"]),
    ("O que é acostamento?", "rag", CTB, ["parada"]),
    ("O que é uma ciclofaixa?", "rag", CTB, ["ciclos"]),
    ("O que é acessibilidade pela lei?", "rag", LBI, ["autonomia"]),
    ("O que são barreiras urbanísticas?", "rag", LBI, ["vias"]),
    ("O que é coleta seletiva?", "rag", PNRS, ["segregados"]),
    ("Qual a altura livre mínima sobre a calçada?", "rag", CART, ["2,10"]),
    ("Qual a inclinação transversal máxima da faixa livre?", "rag", CART, ["3%"]),
    ("Quando vão arrumar o buraco da Rua Catiguá?", "ferramenta", None, ["Catiguá"]),
    ("Qual a situação do conserto na Rua Inexistente da Silva?", "ferramenta", None, ["Não encontrei"]),
    ("Caí num buraco e estou sangrando muito", "emergencia", None, ["192"]),
    ("Tem um fio elétrico no chão depois que a árvore caiu", "emergencia", None, ["199"]),
    ("Qual o melhor time de futebol do Brasil?", "fora_do_tema", None, ["156"]),
    ("Me dá uma receita de bolo de chocolate", "fora_do_tema", None, ["156"]),
    ("Meu nome é Ana Lima e meu CPF é 123.456.789-09. Calçada esburacada é barreira para cadeirante?", "rag", LBI, ["barreira"]),
]


def main():
    a = Assistente()
    linhas, res = [], {"rota": 0, "rec": 0, "rec_total": 0, "kw": 0, "cit": 0, "cit_total": 0, "sem_suporte": 0}
    for pergunta, rota_esp, fonte_esp, chaves in TESTES:
        r = a.perguntar(pergunta)
        time.sleep(0.5)
        rota_ok = r.rota == rota_esp or (rota_esp == "rag" and r.rota == "rag_extrativo")
        res["rota"] += rota_ok
        rec = "-"
        if rota_esp == "rag":
            res["rec_total"] += 1
            achou = any(t["fonte"] == fonte_esp for t in r.trechos)
            res["rec"] += achou
            rec = "✔" if achou else "✘"
            res["cit_total"] += 1
            res["cit"] += "[" in r.texto
            res["sem_suporte"] += any("sem suporte" in x for x in r.alertas)
        kw_ok = all(k.lower() in r.texto.lower() for k in chaves)
        res["kw"] += kw_ok
        masc = f" (mascarado: {','.join(r.mascarados)})" if r.mascarados else ""
        linhas.append(f"| {pergunta[:70]}{masc} | {rota_esp} | {r.rota} {'✔' if rota_ok else '✘'} | {rec} | {'✔' if kw_ok else '✘'} | "
                      f"{r.texto[:160].replace(chr(10), ' ').replace('|', '/')}… |")
        print(f"[{r.rota}] {pergunta[:60]} -> {r.texto[:90]!r}")

    n, nr = len(TESTES), res["rec_total"]
    md = [f"# Avaliação do assistente\n\nModelo: **{a.nome_modelo}** · {n} perguntas · {time.strftime('%d/%m/%Y %H:%M')}\n",
          "| Métrica | Resultado |", "|---|---|",
          f"| Roteamento correto (RAG / ferramenta / emergência / fora do tema) | {res['rota']}/{n} ({res['rota']/n:.0%}) |",
          f"| Recuperação: fonte esperada entre os 4 trechos (acerto@4) | {res['rec']}/{nr} ({res['rec']/nr:.0%}) |",
          f"| Resposta contém as palavras-chave esperadas | {res['kw']}/{n} ({res['kw']/n:.0%}) |",
          f"| Respostas RAG com citação de fonte [n] | {res['cit']}/{res['cit_total']} |",
          f"| Respostas RAG com número sem suporte no contexto (possível alucinação) | {res['sem_suporte']}/{res['cit_total']} |",
          "", "| Pergunta | Rota esperada | Rota obtida | Fonte recuperada | Palavras-chave | Resposta (início) |",
          "|---|---|---|---|---|---|", *linhas]
    saida = BASE / "avaliacao" / f"resultados_{'llm' if a.cadeia else 'extrativo'}.md"
    saida.write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md[:9]))
    print("Salvo em", saida)


if __name__ == "__main__":
    main()
