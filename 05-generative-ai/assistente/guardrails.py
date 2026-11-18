"""Proteções aplicadas antes e depois do modelo generativo."""

import re

RE_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
RE_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
RE_TEL = re.compile(r"(?:\+?55\s?)?\(?\b\d{2}\)?\s?9?\d{4}[-\s]?\d{4}\b")
RE_PLACA = re.compile(r"\b[A-Z]{3}-?\d[A-Z0-9]\d{2}\b", re.I)
RE_NOME = re.compile(r"(?i:meu nome é|me chamo|sou o|sou a)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)*)")


def mascarar_dados_pessoais(texto: str):
    """LGPD: dados pessoais do cidadão nunca são enviados para a API do LLM."""
    mascarados = []
    for regex, rotulo in ((RE_EMAIL, "EMAIL"), (RE_CPF, "CPF"), (RE_TEL, "TELEFONE"), (RE_PLACA, "PLACA")):
        if regex.search(texto):
            mascarados.append(rotulo)
            texto = regex.sub(f"[{rotulo}]", texto)
    m = RE_NOME.search(texto)
    if m:
        mascarados.append("NOME")
        texto = texto.replace(m.group(1), "[NOME]")
    return texto, mascarados


EMERGENCIA = ["sangrando", "sangue", "desmaiou", "inconsciente", "ferido", "fratura", "quebrei", "fio caído", "fio no chão",
              "fio elétrico", "desabou", "desabamento", "cratera abriu", "incêndio", "incendio", "atropelad", "não respira"]


def detectar_emergencia(texto: str) -> bool:
    t = texto.lower()
    return any(p in t for p in EMERGENCIA)


RESPOSTA_EMERGENCIA = (
    "Isso parece uma emergência. Ligue agora: **SAMU 192** (pessoa ferida), **Bombeiros 193** ou **Defesa Civil 199** "
    "(fio caído, desabamento, cratera). Não se aproxime de fios elétricos. Quando estiver em segurança, posso explicar "
    "como registrar o problema da via."
)

RESPOSTA_FORA_DO_TEMA = (
    "Desculpe, só consigo ajudar com assuntos de ruas, calçadas, buracos, lixo nas vias, acessibilidade e os direitos do "
    "cidadão sobre esses problemas. Para outros assuntos, procure a Central 156 da Prefeitura."
)


def numeros_sem_suporte(resposta: str, contexto: str):
    """Verificação simples de alucinação: números citados na resposta precisam existir no contexto recuperado."""
    nums = set(re.findall(r"\d+(?:[.,]\d+)?", resposta))
    nums = {n for n in nums if not re.fullmatch(r"[1-9]", n)}  # ignora índices de citação [1]..[9]
    ctx = contexto.replace(" ", "")
    return sorted(n for n in nums if n not in ctx)
