"""
Orquestração do assistente (arquitetura agêntica simples):

  pergunta
    -> guardrails de entrada (mascara dados pessoais, detecta emergência)
    -> roteador:  status de uma rua?  -> FERRAMENTA consultar_ordens (dados reais do robô RPA)
                  senão               -> RAG
    -> RAG: recupera 4 trechos (FAISS + embeddings multilíngues)
            relevância baixa -> resposta "fora do tema" (não chama o LLM)
            prompt com regras + contexto numerado -> LLM (Gemini ou Groq, via LangChain)
    -> guardrails de saída: resposta vazia/erro -> modo extrativo; números sem suporte no contexto -> aviso
    -> resposta + fontes citadas
"""

import logging
import os
import re
import time
from dataclasses import dataclass, field

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .base_conhecimento import NOMES_FONTES, obter_indice
from .ferramentas import consultar_ordens, formatar_resultado, quer_status
from .guardrails import (RESPOSTA_EMERGENCIA, RESPOSTA_FORA_DO_TEMA, detectar_emergencia,
                         mascarar_dados_pessoais, numeros_sem_suporte)

log = logging.getLogger("assistente")
LIMIAR_RELEVANCIA = float(os.getenv("LIMIAR_RELEVANCIA", "0.45"))
K = 4

PROMPT_SISTEMA = """Você é o assistente do Cidade em Ordem, um serviço público de zeladoria urbana de São Paulo.
Seu público são cidadãos comuns, muitos idosos e com pouca familiaridade com termos jurídicos.

REGRAS:
1. Responda SOMENTE com base nos trechos do CONTEXTO. Não use conhecimento externo.
2. Se o contexto não tiver a resposta, diga: "Não encontrei essa informação nas leis e cartilhas que consulto." e
   sugira a Central 156 da Prefeitura.
3. Cite as fontes usando os números entre colchetes, por exemplo [1] ou [2][3].
4. Use linguagem simples, frases curtas, no máximo 6 frases. Explique termos técnicos.
5. Não dê aconselhamento jurídico ou médico individual: para um caso concreto, indique a Defensoria Pública, um
   advogado ou um serviço de saúde.
6. Nunca invente números, prazos, valores ou artigos de lei."""

PROMPT_USUARIO = """CONTEXTO:
{contexto}

PERGUNTA DO CIDADÃO: {pergunta}

Resposta (em português, simples, com citações):"""


@dataclass
class Resposta:
    texto: str
    rota: str                      # rag | rag_extrativo | ferramenta | emergencia | fora_do_tema
    fontes: list = field(default_factory=list)
    trechos: list = field(default_factory=list)
    mascarados: list = field(default_factory=list)
    alertas: list = field(default_factory=list)
    modelo: str = ""
    ms: int = 0


def criar_llm():
    """Escolhe o provedor pela chave disponível no ambiente (.env). Sem chave -> modo extrativo."""
    try:
        if os.getenv("GOOGLE_API_KEY"):
            from langchain_google_genai import ChatGoogleGenerativeAI
            modelo = os.getenv("LLM_MODELO", "gemini-2.5-flash")
            return ChatGoogleGenerativeAI(model=modelo, temperature=0.2, timeout=30, max_retries=2), f"Gemini ({modelo})"
        if os.getenv("GROQ_API_KEY"):
            from langchain_groq import ChatGroq
            modelo = os.getenv("LLM_MODELO", "llama-3.3-70b-versatile")
            return ChatGroq(model=modelo, temperature=0.2, timeout=30, max_retries=2), f"Groq ({modelo})"
    except Exception as e:  # pacote ausente, chave inválida etc.
        log.error("Não foi possível iniciar o LLM: %s", e)
    return None, "sem LLM (modo extrativo)"


class Assistente:
    def __init__(self, hibrido=True):
        self.indice = obter_indice()
        self.hibrido = hibrido
        if hibrido:
            from langchain_community.retrievers import BM25Retriever
            docs = list(self.indice.docstore._dict.values())
            self.bm25 = BM25Retriever.from_documents(docs, k=8, preprocess_func=lambda t: re.findall(r"\w+", t.lower()))
        self.llm, self.nome_modelo = criar_llm()
        prompt = ChatPromptTemplate.from_messages([("system", PROMPT_SISTEMA), ("human", PROMPT_USUARIO)])
        self.cadeia = (prompt | self.llm | StrOutputParser()) if self.llm else None

    def recuperar(self, pergunta):
        """Busca híbrida: vetorial (sentido) + BM25 (palavras exatas, como 'acessibilidade'), fundidas por
        Reciprocal Rank Fusion. Devolve (documento, similaridade vetorial) dos K melhores."""
        vet = self.indice.similarity_search_with_score(pergunta, k=8)
        if not self.hibrido:
            return vet[:K]
        chave = lambda d: d.page_content[:200]  # noqa: E731
        pontos, docs, score_vet = {}, {}, {}
        for pos, (d, s) in enumerate(vet):
            pontos[chave(d)] = pontos.get(chave(d), 0) + 1 / (60 + pos)
            docs[chave(d)], score_vet[chave(d)] = d, float(s)
        for pos, d in enumerate(self.bm25.invoke(pergunta)):
            pontos[chave(d)] = pontos.get(chave(d), 0) + 1 / (60 + pos)
            docs.setdefault(chave(d), d)
        melhores = sorted(pontos, key=pontos.get, reverse=True)[:K]
        # relevância máxima (para o guardrail de "fora do tema") vem sempre da busca vetorial
        self.relevancia_max = float(vet[0][1]) if vet else 0.0
        return [(docs[c], score_vet.get(c, 0.0)) for c in melhores]

    @staticmethod
    def montar_contexto(resultados):
        partes = []
        for i, (doc, _) in enumerate(resultados, 1):
            nome = NOMES_FONTES.get(doc.metadata["fonte"], doc.metadata["fonte"])
            partes.append(f"[{i}] ({nome})\n{doc.page_content}")
        return "\n\n".join(partes)

    @staticmethod
    def extrativo(resultados):
        """Caminho seguro sem LLM: devolve a resposta revisada do par QA mais próximo, ou o trecho mais relevante."""
        for doc, _ in resultados:
            if doc.metadata.get("tipo") == "qa":
                return doc.metadata["resposta"] + " [1]"
        doc = resultados[0][0]
        frases = re.split(r"(?<=[.;])\s+", doc.page_content)
        return " ".join(frases[:3]) + " [1]"

    def perguntar(self, pergunta: str) -> Resposta:
        t0 = time.perf_counter()
        pergunta = (pergunta or "").strip()
        if not pergunta:
            return Resposta("Digite uma pergunta.", "vazia")
        pergunta_segura, mascarados = mascarar_dados_pessoais(pergunta)

        if detectar_emergencia(pergunta_segura):
            return Resposta(RESPOSTA_EMERGENCIA, "emergencia", mascarados=mascarados, ms=int((time.perf_counter() - t0) * 1000))

        rua = quer_status(pergunta_segura)
        if rua:
            achadas, erro = consultar_ordens(rua)
            return Resposta(formatar_resultado(rua, achadas, erro), "ferramenta", fontes=["Ordens de serviço do robô RPA"],
                            mascarados=mascarados, ms=int((time.perf_counter() - t0) * 1000))

        self.relevancia_max = 0.0
        resultados = self.recuperar(pergunta_segura)
        melhor = self.relevancia_max if self.hibrido else (resultados[0][1] if resultados else 0)
        if melhor < LIMIAR_RELEVANCIA:
            return Resposta(RESPOSTA_FORA_DO_TEMA, "fora_do_tema", mascarados=mascarados,
                            alertas=[f"relevância máxima {melhor:.2f} < {LIMIAR_RELEVANCIA}"], ms=int((time.perf_counter() - t0) * 1000))

        contexto = self.montar_contexto(resultados)
        fontes = list(dict.fromkeys(NOMES_FONTES.get(d.metadata["fonte"], d.metadata["fonte"]) for d, _ in resultados))
        trechos = [{"fonte": d.metadata["fonte"], "score": round(float(s), 3), "texto": d.page_content[:300]} for d, s in resultados]
        alertas, rota, texto = [], "rag", ""

        if self.cadeia:
            try:
                texto = self.cadeia.invoke({"contexto": contexto, "pergunta": pergunta_segura}).strip()
            except Exception as e:
                alertas.append(f"falha no LLM: {type(e).__name__}")
                log.error("Falha na chamada ao LLM: %s", e)
        if not texto:
            texto, rota = self.extrativo(resultados), "rag_extrativo"
            if self.cadeia:
                alertas.append("resposta do LLM vazia ou com erro: usado o modo extrativo")

        sem_suporte = numeros_sem_suporte(texto, contexto)
        if sem_suporte and rota == "rag":
            alertas.append(f"números sem suporte no contexto: {sem_suporte}")
            texto += "\n\n⚠️ Confira os números acima na fonte oficial: nem todos aparecem nos trechos consultados."

        return Resposta(texto, rota, fontes, trechos, mascarados, alertas, self.nome_modelo, int((time.perf_counter() - t0) * 1000))
