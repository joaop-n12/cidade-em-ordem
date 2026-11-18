"""
Cidade em Ordem - Assistente generativo do cidadão (RAG + ferramenta + guardrails)

Execução:
    pip install -r requirements.txt
    copie .env.example para .env e coloque GOOGLE_API_KEY (ou GROQ_API_KEY)
    python app.py
Abre:
    http://localhost:8000/          interface Gradio (demonstração)
    POST http://localhost:8000/perguntar   {"pergunta": "..."}  -> usado pelo front-end React (VITE_RAG_URL)
"""

import logging
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
env = BASE / ".env"
if env.exists():
    for linha in env.read_text(encoding="utf-8").splitlines():
        if "=" in linha and not linha.strip().startswith("#"):
            k, v = linha.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

import gradio as gr  # noqa: E402
import uvicorn  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from assistente.rag import Assistente  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
assistente = Assistente()
logging.info("Assistente pronto. Modelo: %s", assistente.nome_modelo)

api = FastAPI(title="Cidade em Ordem - Assistente")
api.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["POST"], allow_headers=["*"])


class Pergunta(BaseModel):
    pergunta: str


@api.post("/perguntar")
def perguntar(p: Pergunta):
    r = assistente.perguntar(p.pergunta[:1000])
    return {"resposta": r.texto, "rota": r.rota, "fontes": r.fontes, "alertas": r.alertas}


ROTULOS = {"rag": "RAG + LLM", "rag_extrativo": "RAG extrativo (sem LLM)", "ferramenta": "Ferramenta: ordens de serviço",
           "emergencia": "Guardrail: emergência", "fora_do_tema": "Guardrail: fora do tema", "vazia": "-"}


def responder(msg, historico):
    r = assistente.perguntar(msg)
    detalhes = f"**Rota:** {ROTULOS.get(r.rota, r.rota)} · **Modelo:** {r.modelo or '-'} · {r.ms} ms"
    if r.mascarados:
        detalhes += f"\n\n🔒 Dados pessoais mascarados antes do envio ao modelo: {', '.join(r.mascarados)}"
    if r.fontes:
        detalhes += "\n\n**Fontes:** " + "; ".join(f"[{i}] {f}" for i, f in enumerate(r.fontes, 1))
    if r.trechos:
        detalhes += "\n\n**Trechos recuperados:**\n" + "\n".join(
            f"- ({t['score']}) *{t['fonte']}*: {t['texto'][:160]}…" for t in r.trechos)
    if r.alertas:
        detalhes += "\n\n⚠️ " + " | ".join(r.alertas)
    historico = historico + [{"role": "user", "content": msg}, {"role": "assistant", "content": r.texto}]
    return "", historico, detalhes


EXEMPLOS = [
    "Meu pneu estourou num buraco. A prefeitura tem responsabilidade?",
    "De quem é a obrigação de consertar a calçada em frente à minha casa?",
    "A raiz da árvore quebrou minha calçada, sou obrigado a arrumar?",
    "Quando vão arrumar o buraco da Rua Catiguá?",
    "Qual a largura mínima da faixa livre da calçada?",
    "Meu nome é Ana Lima, CPF 123.456.789-09. Calçada esburacada é barreira para cadeirante?",
    "Caí num buraco e estou sangrando",
    "Qual o melhor time do Brasileirão?",
]

with gr.Blocks(title="Cidade em Ordem - Assistente") as demo:
    gr.Markdown("# Cidade em Ordem: assistente do cidadão\nRespostas baseadas em leis e cartilhas oficiais (RAG), "
                f"status real das ordens de serviço e proteções de privacidade. Modelo: **{assistente.nome_modelo}**")
    with gr.Row():
        with gr.Column(scale=3):
            chat = gr.Chatbot(height=430, label="Conversa")
            caixa = gr.Textbox(placeholder="Digite sua pergunta", label="Pergunta")
            gr.Examples(EXEMPLOS, inputs=caixa)
        with gr.Column(scale=2):
            painel = gr.Markdown("Os detalhes técnicos da resposta aparecem aqui.")
    caixa.submit(responder, [caixa, chat], [caixa, chat, painel])

app = gr.mount_gradio_app(api, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORTA", "8000")))
