"""Base de conhecimento do RAG: corpus limpo e anonimizado gerado na disciplina de PLN."""

import json
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

RAIZ = Path(__file__).resolve().parents[2]
CORPUS = RAIZ / "04-pln" / "corpus"
INDICE = Path(__file__).resolve().parents[1] / "indice_faiss"

# Modelo de embeddings multilíngue, gratuito, roda localmente (sem enviar o texto para a nuvem).
MODELO_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

NOMES_FONTES = {
    "cartilha_calcadas_sp_2024.pdf": "Cartilha de Calçadas - Prefeitura de SP (2024)",
    "ctb_lei_9503_1997.html": "Código de Trânsito Brasileiro (Lei 9.503/1997)",
    "lbi_lei_13146_2015.html": "Lei Brasileira de Inclusão (Lei 13.146/2015)",
    "sp_lei_15442_2011.docx": "Lei Municipal de SP 15.442/2011 (calçadas e terrenos)",
    "pnrs_lei_12305_2010.txt": "Política Nacional de Resíduos Sólidos (Lei 12.305/2010)",
}


def embeddings():
    return HuggingFaceEmbeddings(model_name=MODELO_EMBEDDINGS, encode_kwargs={"normalize_embeddings": True})


def carregar_documentos():
    docs = []
    # 1) trechos de texto puro (256-512 tokens): contexto amplo
    for linha in (CORPUS / "corpus_texto.jsonl").read_text(encoding="utf-8").splitlines():
        item = json.loads(linha)
        docs.append(Document(page_content=item["text"], metadata={"fonte": item["fonte"], "tipo": "trecho"}))
    # 2) pares pergunta-resposta revisados: respostas curtas e fiéis
    for linha in (CORPUS / "corpus_qa.jsonl").read_text(encoding="utf-8").splitlines():
        item = json.loads(linha)
        if item["fonte"] == "politica_do_assistente":
            continue
        docs.append(Document(page_content=f"Pergunta: {item['instruction']}\nResposta: {item['output']}",
                             metadata={"fonte": item["fonte"], "tipo": "qa", "resposta": item["output"]}))
    return docs


def obter_indice(reconstruir=False):
    """Cria (ou carrega) o índice vetorial. Serializamos em bytes pelo Python porque o FAISS em C++ não abre
    caminhos com acentos no Windows (ex.: C:\\Users\\João)."""
    emb = embeddings()
    arquivo = INDICE.with_suffix(".bin")
    if arquivo.exists() and not reconstruir:
        return FAISS.deserialize_from_bytes(arquivo.read_bytes(), emb, allow_dangerous_deserialization=True,
                                            distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT)
    docs = carregar_documentos()
    indice = FAISS.from_documents(docs, emb, distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT)
    arquivo.write_bytes(indice.serialize_to_bytes())
    return indice
