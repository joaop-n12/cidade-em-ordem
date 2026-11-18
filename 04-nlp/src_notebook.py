# %% [markdown]
# # Fábrica de Corpus CitizenTech: Cidade em Ordem
# **Global Solution 2026.2 · Processamento de Linguagem Natural**
#
# | Integrante | RM |
# |---|---|
# | João Pedro de Souza Nunes | RM567318 |
# | Guilherme Nakamura | RM567460 |
#
# **Objetivo:** transformar leis e cartilhas públicas sobre **vias, calçadas e limpeza urbana** em três corpus
# (texto puro, perguntas e respostas, conversacional) prontos para o *fine-tuning* de um modelo de linguagem
# pequeno (SLM). Esse modelo pode rodar **localmente** na prefeitura e atender o cidadão sem enviar dados para a nuvem.
#
# **Persona:** *Dona Cida, 67 anos, moradora do Tatuapé (SP).* Tropeçou numa calçada quebrada e não sabe de quem
# é a responsabilidade pelo conserto nem quais são seus direitos. Tem pouca familiaridade com termos jurídicos.
#
# **ODS:** 11 (cidades inclusivas e seguras, meta 11.2), 10 (redução das desigualdades, acessibilidade) e 9 (infraestrutura).
#
# **Como rodar:** no Colab, *Executar tudo*. A última célula abre a interface Gradio com upload de arquivos.

# %% [markdown]
# ## 0. Instalação

# %%
import os, sys
NO_COLAB = "google.colab" in sys.modules
SEM_INTERFACE = os.getenv("NLP_SEM_INTERFACE") == "1"
if NO_COLAB:
    !pip -q install pypdf python-docx beautifulsoup4 tiktoken gradio spacy
    !python -m spacy download pt_core_news_sm -q

# %%
import hashlib, html, io, json, random, re, unicodedata
from collections import Counter
from pathlib import Path
import urllib.request

import tiktoken
from bs4 import BeautifulSoup
from docx import Document
from pypdf import PdfReader

random.seed(42)
ENC = tiktoken.get_encoding("cl100k_base")
def n_tokens(t): return len(ENC.encode(t))

PASTA_DOCS = Path("documentos"); PASTA_DOCS.mkdir(exist_ok=True)
PASTA_SAIDA = Path("corpus"); PASTA_SAIDA.mkdir(exist_ok=True)

# %% [markdown]
# ## 1. Documentos de entrada (fontes oficiais)
#
# | Arquivo | Documento | Formato | Fonte |
# |---|---|---|---|
# | `cartilha_calcadas_sp_2024.pdf` | Cartilha "Calçadas e Vias Exclusivas de Pedestres" (SMPED/CPA, Prefeitura de SP) | PDF | prefeitura.sp.gov.br |
# | `ctb_lei_9503_1997.html` | Código de Trânsito Brasileiro (Lei 9.503/1997, texto compilado) | HTML | planalto.gov.br |
# | `lbi_lei_13146_2015.html` | Lei Brasileira de Inclusão (Lei 13.146/2015) | HTML | planalto.gov.br |
# | `sp_lei_15442_2011.docx` | Lei Municipal 15.442/2011 (limpeza de imóveis, fechamento de terrenos e **calçadas**) | DOCX* | legislacao.prefeitura.sp.gov.br |
# | `pnrs_lei_12305_2010.txt` | Política Nacional de Resíduos Sólidos (Lei 12.305/2010) | TXT* | planalto.gov.br |
#
# \* A Lei 15.442 e a PNRS são publicadas em HTML. Salvamos o texto como DOCX e TXT para testar todos os formatos
# de entrada exigidos, sem alterar o conteúdo. A célula abaixo baixa tudo das fontes oficiais. Se os arquivos já
# estiverem na pasta `documentos/`, ela não baixa de novo.

# %%
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
FONTES = {
    "cartilha_calcadas_sp_2024.pdf": "https://www.prefeitura.sp.gov.br/cidade/secretarias/upload/mobilidade/Livreto%20Cartilha%20de%20Calcadas%202024_5mb.pdf",
    "ctb_lei_9503_1997.html": "http://www.planalto.gov.br/ccivil_03/leis/l9503compilado.htm",
    "lbi_lei_13146_2015.html": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm",
    "sp_lei_15442_2011.html": "https://legislacao.prefeitura.sp.gov.br/leis/lei-15442-de-09-de-setembro-de-2011",
    "pnrs_lei_12305_2010.html": "https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2010/lei/l12305.htm",
}

def baixar(nome, url):
    destino = PASTA_DOCS / nome
    if destino.exists() and destino.stat().st_size > 1000:
        return destino
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        destino.write_bytes(r.read())
    return destino

def decodificar(raw: bytes) -> str:
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue

def html_para_texto(raw: bytes) -> str:
    sopa = BeautifulSoup(decodificar(raw), "html.parser")
    for t in sopa(["script", "style", "strike", "s", "del", "nav", "header", "footer"]):
        t.decompose()  # <strike> no Planalto = dispositivo revogado
    return sopa.get_text("\n")

for nome, url in FONTES.items():
    try:
        baixar(nome, url)
    except Exception as e:
        print(f"Não foi possível baixar {nome}: {e}. Coloque o arquivo manualmente em documentos/.")

# Conversão para DOCX e TXT (demonstração de formatos)
if (PASTA_DOCS / "sp_lei_15442_2011.html").exists() and not (PASTA_DOCS / "sp_lei_15442_2011.docx").exists():
    d = Document()
    for linha in html_para_texto((PASTA_DOCS / "sp_lei_15442_2011.html").read_bytes()).split("\n"):
        if linha.strip():
            d.add_paragraph(linha.strip())
    d.save(PASTA_DOCS / "sp_lei_15442_2011.docx")
if (PASTA_DOCS / "pnrs_lei_12305_2010.html").exists() and not (PASTA_DOCS / "pnrs_lei_12305_2010.txt").exists():
    (PASTA_DOCS / "pnrs_lei_12305_2010.txt").write_text(
        html_para_texto((PASTA_DOCS / "pnrs_lei_12305_2010.html").read_bytes()), encoding="cp1252", errors="ignore")
    # salvo em cp1252 de propósito: a etapa de normalização precisa converter para UTF-8

ENTRADA = [PASTA_DOCS / n for n in ["cartilha_calcadas_sp_2024.pdf", "ctb_lei_9503_1997.html", "lbi_lei_13146_2015.html",
                                     "sp_lei_15442_2011.docx", "pnrs_lei_12305_2010.txt"] if (PASTA_DOCS / n).exists()]
for p in ENTRADA:
    print(f"{p.name:35s} {p.stat().st_size/1024:8.0f} KB")

# %% [markdown]
# ## 2. Ingestão e extração de texto
# Cada formato tem seu leitor. O resultado é uma lista de **páginas** (ou blocos), sempre com o arquivo de origem
# registrado no campo `fonte`.

# %%
def extrair(nome: str, dados: bytes):
    ext = nome.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        leitor = PdfReader(io.BytesIO(dados))
        return [p.extract_text() or "" for p in leitor.pages]
    if ext == "docx":
        return ["\n".join(p.text for p in Document(io.BytesIO(dados)).paragraphs)]
    if ext in ("html", "htm"):
        return [html_para_texto(dados)]
    if ext == "txt":
        return [decodificar(dados)]
    raise ValueError(f"Formato não suportado: {ext}")

def ingerir(arquivos, texto_colado=None):
    """arquivos: lista de (nome, bytes). Devolve lista de documentos {fonte, formato, paginas}."""
    docs = []
    for nome, dados in arquivos:
        try:
            paginas = extrair(nome, dados)
            docs.append({"fonte": nome, "formato": nome.rsplit(".", 1)[-1].upper(), "paginas": paginas})
        except Exception as e:
            print(f"[ERRO] {nome}: {e}")
    if texto_colado and texto_colado.strip():
        docs.append({"fonte": "texto_colado", "formato": "TEXTO", "paginas": [texto_colado]})
    return docs

# Exemplo de texto colado (fictício) com dados pessoais, para demonstrar a anonimização
TEXTO_COLADO_EXEMPLO = """Relato recebido pela ouvidoria (exemplo fictício):
Meu nome é Maria Aparecida Souza, CPF 123.456.789-09, telefone (11) 98765-4321 e e-mail maria.souza@exemplo.com.br.
No dia 3 de março tropecei num buraco da calçada da Rua Tuiuti e machuquei o joelho. A calçada está em mau estado
há meses, com desníveis e raízes de árvore. O vizinho, Sr. José Carlos Pereira, também já caiu no mesmo lugar.
Gostaria de saber de quem é a responsabilidade pelo conserto."""

documentos = ingerir([(p.name, p.read_bytes()) for p in ENTRADA], TEXTO_COLADO_EXEMPLO)
total_paginas = 0
for d in documentos:
    n = len(d["paginas"]) if d["formato"] == "PDF" else max(1, sum(len(p) for p in d["paginas"]) // 3000)
    total_paginas += n
    print(f"{d['fonte']:35s} {d['formato']:6s} ~{n} páginas  {sum(len(p) for p in d['paginas']):>8} caracteres")
print(f"Total aproximado: {total_paginas} páginas (páginas de PDF reais; para os demais, 3.000 caracteres = 1 página)")

# %% [markdown]
# ## 3. Limpeza
# Decisões tomadas a partir da inspeção dos documentos:
# 1. **Ligaduras do PDF:** a fonte da cartilha transforma "ti" em `�` (ex.: `Des�na-se`) e "fi" em `ﬁ`. Corrigimos.
# 2. **Cabeçalhos e rodapés:** linhas que se repetem em várias páginas do PDF e linhas do tipo
#    `CALÇADAS E VIAS EXCLUSIVAS DE PEDESTRES | 03` ou `04 | SMPED E CPA` são removidas.
# 3. **Numeração de páginas** isolada e **URLs soltas** são removidas.
# 4. **Anotações legislativas** como `(Redação dada pela Lei nº ...)`, `(Incluído pela ...)` e `(Vide ...)` são removidas.
#    Elas não ensinam conteúdo ao cidadão. Dispositivos revogados (`<strike>` no Planalto) já saíram na extração.
# 5. **Versões duplicadas de artigos:** quando o mesmo artigo aparece duas vezes (antiga e nova redação), fica só a última.
# 6. **Linhas repetidas** (ex.: `Altura MínimaAltura MínimaAltura Mínima`) e caracteres de controle são removidos.
# 7. **Hifenização:** `infra-\nestrutura` vira `infraestrutura`. Linhas quebradas no meio da frase são unidas.
#
# **Não** removemos *stop words* nem fazemos *stemming*: o modelo de linguagem precisa do texto natural.

# %%
RE_ANOTACAO = re.compile(r"\((?:Redação dada|Incluíd[oa]|Revogad[oa]|Vide|Vigência|Regulamento|Promulgação|Renumerad[oa]|Acrescid[oa])[^)]*\)", re.I)
RE_URL = re.compile(r"(?<!@)\b(?:https?://|www\.)\S+", re.I)
RE_CABECALHO = re.compile(r"^\s*(?:\d{1,3}\s*\|.*|.*\|\s*\d{1,3})\s*$")
RE_NUM_PAGINA = re.compile(r"^\s*(?:página\s*)?\d{1,3}(?:\s*(?:de|/)\s*\d{1,3})?\s*$", re.I)

def corrigir_ligaduras(t):
    t = unicodedata.normalize("NFKC", t)               # ﬁ -> fi, ﬂ -> fl
    return re.sub(r"(?<=[A-Za-zÀ-ÿ])�|�(?=[A-Za-zÀ-ÿ])", "ti", t)

def remover_repeticao_interna(linha):
    m = re.fullmatch(r"(.{3,}?)\1+", linha.strip())
    return m.group(1) if m else linha

def limpar_documento(doc):
    paginas = [corrigir_ligaduras(p) for p in doc["paginas"]]
    # linhas que aparecem em mais de 30% das páginas = cabeçalho/rodapé
    repetidas = set()
    if len(paginas) >= 4:
        cont = Counter(l.strip() for p in paginas for l in set(p.split("\n")) if l.strip())
        repetidas = {l for l, c in cont.items() if c / len(paginas) > 0.3 and len(l) < 80}
    linhas = []
    for p in paginas:
        for l in p.split("\n"):
            l = l.replace("\t", " ").strip()
            if not l or l in repetidas or RE_CABECALHO.match(l) or RE_NUM_PAGINA.match(l):
                continue
            l = remover_repeticao_interna(l)
            linhas.append(l)
        linhas.append("")  # quebra de página = quebra de parágrafo
    texto = "\n".join(linhas)
    texto = RE_ANOTACAO.sub("", texto)
    texto = RE_URL.sub("", texto)
    texto = "".join(c for c in texto if c in "\n" or unicodedata.category(c)[0] != "C")  # controle
    texto = re.sub(r"[■□▪●◆◇►▶✓✔→←↑↓]", " ", texto)
    texto = re.sub(r"(\w)-\n\s*(\w)", r"\1\2", texto)                     # hifenização
    texto = re.sub(r"([a-zà-ÿ]) -\n\s*([a-zà-ÿ])", r"\1\2", texto)       # "conside -\nrar"
    texto = re.sub(r"\b[IVXLC]+\s*-\s*;\s*", "", texto)                   # incisos revogados vazios ("VII -;")
    # une linhas quebradas no meio da frase
    texto = re.sub(r"(?<![.:;!?\n])\n(?!\n|\s*(?:Art\.|§|[IVXLC]+\s*[-–]|[a-z]\)|[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{3,}[A-ZÁÉÍÓÚÂÊÔÃÕÇ \-/]* - ))", " ", texto)
    texto = re.sub(r"(§)\s*\n\s*", r"\1 ", texto)                         # "§\n1º" -> "§ 1º"
    texto = re.sub(r"Art\.\s*(\d+)\s*\n?\s*[oº°]\b", r"Art. \1º", texto)  # "Art. 3\no" -> "Art. 3º"
    # duplicatas de artigo (antiga e nova redação): mantém a última
    paragrafos = [p.strip() for p in re.split(r"\n+", texto) if p.strip()]
    vistos, finais = {}, []
    for par in paragrafos:
        m = re.match(r"(Art\. \d+[º°]?(?:-[A-Z])?\.?)\s", par)
        if m and m.group(1) in vistos:
            finais[vistos[m.group(1)]] = None
        if m:
            vistos[m.group(1)] = len(finais)
        finais.append(par)
    versoes_antigas = sum(1 for p in finais if p is None)
    paragrafos = [p for p in finais if p]
    # remove parágrafos idênticos repetidos. Linhas curtas como "Infração - grave;" se repetem em vários
    # artigos do CTB e fazem parte de cada um, por isso só deduplicamos parágrafos com 80+ caracteres.
    unicos, ja = [], set()
    for par in paragrafos:
        if par not in ja or len(par) < 80:
            unicos.append(par); ja.add(par)
    DUPLICATAS_LIMPEZA[doc.get("fonte", "?")] = {"paragrafos_repetidos": len(paragrafos) - len(unicos),
                                                  "versoes_antigas_de_artigos": versoes_antigas}
    return "\n\n".join(unicos)

DUPLICATAS_LIMPEZA = {}

# %% [markdown]
# ## 4. Normalização
# Codificação UTF-8 (forma NFC), espaços (inclusive não separáveis) unificados, no máximo uma linha em branco
# entre parágrafos, aspas curvas convertidas em retas e travessões padronizados. **Acentos, pontuação e
# maiúsculas são mantidos.**

# %%
def normalizar(t):
    t = unicodedata.normalize("NFC", t)
    t = t.replace(" ", " ").replace(" ", " ").replace("​", "")
    t = re.sub(r"[“”„‟″]", '"', t)
    t = re.sub(r"[‘’‚‛′`´]", "'", t)
    t = re.sub(r"[–—―]", "-", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r" ([,.;:!?])", r"\1", t)
    t = re.sub(r"((?:Art\.|§)\s?\d+)\s?o\b", r"\1º", t)   # "§ 1o" -> "§ 1º" (ordinal do Planalto)
    t = re.sub(r"(?<=\s)(\d{1,3})o(?=[\s,.;)])", r"\1º", t)  # "1o de abril", "2o graus"
    t = re.sub(r"\bn\s?o\s(?=\d)", "nº ", t)              # "Lei n o 10.650" -> "Lei nº 10.650"
    t = re.sub(r"([a-zà-ÿ]) - ([a-zà-ÿ]{1,4}\b)", r"\1\2", t)  # "conside - rar" (quebra do PDF)
    return t.strip()

# %% [markdown]
# ## 5. Anonimização (LGPD)
# Executada **antes** de gerar qualquer corpus:
# - **CPF e CNPJ**, **e-mails** e **telefones**, por expressões regulares;
# - **nomes de pessoas**, pelo reconhecimento de entidades (NER) do spaCy `pt_core_news_sm`, mais regras para
#   pronomes de tratamento (`Sr.`, `Dra.`...), "meu nome é ..." e o **bloco de assinaturas** no fim das leis
#   (presidente, prefeito e ministros, logo após "Brasília, ... de ..." ou "PREFEITURA DO MUNICÍPIO DE SÃO PAULO").
#
# **Decisão importante:** na primeira versão, o NER marcou como pessoa termos como "Certificado de Registro",
# "Distrito Federal" e "Pessoa com Deficiência". Criamos um filtro: uma entidade só é aceita como nome se tem
# 2 ou mais palavras com inicial maiúscula e **nenhuma delas aparece escrita em minúscula em outro ponto do
# documento**. "registro", "federal" e "pessoa" aparecem em minúscula no texto, então são palavras comuns. Nomes
# próprios como "Maria" e "Pereira" não aparecem.

# %%
try:
    import spacy
    NLP = spacy.load("pt_core_news_sm", disable=["parser", "lemmatizer"])
    NLP.max_length = 3_000_000
except Exception as e:
    NLP = None
    print("spaCy indisponível, usando só regras para nomes:", e)

RE_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
RE_CNPJ = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")
RE_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
RE_TEL = re.compile(r"(?:\+?55\s?)?\(?\b\d{2}\)?\s?9?\d{4}[-\s]?\d{4}\b")
NOME_PROPRIO = r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s(?:de|da|do|dos|das|e)\s[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+|\s[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+){0,4}"
RE_TRATAMENTO = re.compile(r"\b(?:Sr\.|Sra\.|Srta\.|Dr\.|Dra\.|Senhor|Senhora|Dona)\s+(" + NOME_PROPRIO + ")")
RE_MEU_NOME = re.compile(r"(?i:meu nome é|me chamo)\s+(" + NOME_PROPRIO + ")")
RE_FIM_LEI = re.compile(r"(?:Brasília,\s*\d{1,2}\s+de\s+\w+\s+de\s+\d{4}|PREFEITURA DO MUNIC[IÍ]PIO DE S[AÃ]O PAULO,\s*aos)[^\n]*\n+")
CONECTIVOS = {"de", "da", "do", "dos", "das", "e"}

def eh_nome(trecho, minusculas):
    palavras = [p.strip(".,;:()") for p in trecho.split()]
    principais = [p for p in palavras if p.lower() not in CONECTIVOS]
    return (len(principais) >= 2 and all(p[:1].isupper() and not p.isupper() for p in principais)
            and not any(p.lower() in minusculas for p in principais))

def mascarar_assinaturas(t, contagem):
    """Após a data de assinatura da lei, os parágrafos curtos seguintes são nomes de autoridades."""
    ms = list(RE_FIM_LEI.finditer(t))
    if not ms:
        return t
    inicio = ms[-1].end()
    partes = t[inicio:].split("\n\n")
    novas = []
    def parece_lista_de_nomes(par):
        palavras = [p for p in re.findall(r"[A-Za-zÀ-ÿ]+", par) if p.lower() not in CONECTIVOS]
        return palavras and len(par) < 300 and sum(p[0].isupper() for p in palavras) / len(palavras) >= 0.8
    for i, par in enumerate(partes):
        if i < 3 and parece_lista_de_nomes(par) and "Art." not in par and not par.lower().startswith(("este texto", "anexo")):
            contagem["NOME"] += 1
            novas.append("[NOME]")
        else:
            novas.append(par)
    return t[:inicio] + "\n\n".join(novas)

def anonimizar(t):
    contagem = Counter()
    minusculas = set(re.findall(r"\b[a-záéíóúâêôãõç]{3,}\b", t))   # palavras que aparecem em minúscula
    def sub(regex, rotulo, texto, grupo=0):
        def f(m):
            contagem[rotulo] += 1
            return m.group(0).replace(m.group(grupo), f"[{rotulo}]") if grupo else f"[{rotulo}]"
        return regex.sub(f, texto)
    t = sub(RE_EMAIL, "EMAIL", t)
    t = sub(RE_CNPJ, "CNPJ", t)
    t = sub(RE_CPF, "CPF", t)
    t = sub(RE_TEL, "TELEFONE", t)
    t = sub(RE_MEU_NOME, "NOME", t, 1)
    t = sub(RE_TRATAMENTO, "NOME", t, 1)
    t = mascarar_assinaturas(t, contagem)
    if NLP is not None:
        nomes = set()
        for bloco in [t[i:i + 500_000] for i in range(0, len(t), 500_000)]:
            for ent in NLP(bloco).ents:
                if ent.label_ == "PER" and eh_nome(ent.text.strip(), minusculas):
                    nomes.add(ent.text.strip())
        for n in sorted(nomes, key=len, reverse=True):
            qtd = len(re.findall(re.escape(n), t))
            t = re.sub(r"\b" + re.escape(n) + r"\b", "[NOME]", t)
            contagem["NOME"] += qtd
    t = re.sub(r"\[NOME\](?:\s+\[NOME\])+", "[NOME]", t)
    return t, contagem

# Exemplo antes e depois
limpo_exemplo = normalizar(limpar_documento({"paginas": [TEXTO_COLADO_EXEMPLO]}))
anon_exemplo, cont_exemplo = anonimizar(limpo_exemplo)
print("ANTES:\n", limpo_exemplo, "\n\nDEPOIS:\n", anon_exemplo, "\n\nItens mascarados:", dict(cont_exemplo))

# %% [markdown]
# ### Processamento completo dos documentos

# %%
def processar(documentos):
    saida, relatorio = [], []
    for d in documentos:
        bruto = "\n".join(d["paginas"])
        limpo = normalizar(limpar_documento(d))
        anon, cont = anonimizar(limpo)
        saida.append({"fonte": d["fonte"], "texto": anon})
        relatorio.append({"fonte": d["fonte"], "caracteres_brutos": len(bruto), "caracteres_limpos": len(anon),
                          "reducao_%": round(100 * (1 - len(anon) / max(len(bruto), 1)), 1), "mascarados": dict(cont)})
    return saida, relatorio

textos, rel_limpeza = processar(documentos)
for r in rel_limpeza:
    print(r)

cartilha = next((d for d in documentos if d["fonte"].endswith(".pdf")), None)
if cartilha:
    print("\n--- Trecho da cartilha ANTES da limpeza ---\n", cartilha["paginas"][3][:700])
    print("\n--- DEPOIS ---\n", next(t["texto"] for t in textos if t["fonte"] == cartilha["fonte"])[1500:2300])

# %% [markdown]
# ## 6. Segmentação (256 a 512 tokens)
# Dividimos o texto em frases, sem quebrar frases e respeitando os parágrafos, e juntamos as frases até chegar
# perto de 512 tokens (tokenizador `cl100k_base`). Um trecho só é fechado quando tem pelo menos 256 tokens. O
# último trecho de cada documento, se ficar curto, é juntado ao anterior quando cabe.

# %%
# não quebra depois de abreviações ("Art. 280", "arts. 7º", "Sr. José", "nº.")
RE_FRASE = re.compile(r"(?<!Art\.)(?<!art\.)(?<!rts\.)(?<!\bSr\.)(?<!\bDr\.)(?<!inc\.)(?<!\bn\.)(?<!nº\.)(?<=[.!?;:])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ\"(§0-9IVX])")

def dividir_frases(texto):
    frases = []
    for par in texto.split("\n\n"):
        partes = [f.strip() for f in RE_FRASE.split(par) if f.strip()]
        for f in partes:
            if n_tokens(f) <= 512:
                frases.append(f)
            else:  # frase gigante: quebra nas vírgulas
                atual = ""
                for pedaco in re.split(r"(?<=,)\s+", f):
                    if atual and n_tokens(atual + " " + pedaco) > 512:
                        frases.append(atual); atual = pedaco
                    else:
                        atual = (atual + " " + pedaco).strip()
                if atual:
                    frases.append(atual)
    return frases

def segmentar(texto, minimo=256, maximo=512):
    trechos, atual, tok_atual = [], [], 0
    for f in dividir_frases(texto):
        tf = n_tokens(f)
        if tok_atual + tf > maximo and tok_atual >= minimo:
            trechos.append(" ".join(atual)); atual, tok_atual = [], 0
        elif tok_atual + tf > maximo:  # ainda abaixo do mínimo, mas não cabe: fecha mesmo assim
            if atual:
                trechos.append(" ".join(atual)); atual, tok_atual = [], 0
        atual.append(f); tok_atual += tf
    if atual:
        resto = " ".join(atual)
        if trechos and n_tokens(trechos[-1] + " " + resto) <= maximo:
            trechos[-1] = trechos[-1] + " " + resto
        else:
            trechos.append(resto)
    return trechos

corpus_texto = []
for t in textos:
    if t["fonte"] == "texto_colado":
        continue  # relato do cidadão: só demonstra a anonimização, não entra no corpus
    for trecho in segmentar(t["texto"]):
        corpus_texto.append({"text": trecho, "fonte": t["fonte"]})
toks = [n_tokens(c["text"]) for c in corpus_texto]
print(f"{len(corpus_texto)} trechos | média {sum(toks)/len(toks):.0f} tokens | mín {min(toks)} | máx {max(toks)}")
print(f"Dentro de 256-512: {sum(256 <= x <= 512 for x in toks)} ({100*sum(256 <= x <= 512 for x in toks)/len(toks):.0f}%)")

# %% [markdown]
# ## 7. Corpus de perguntas e respostas
# Para garantir **fidelidade** (nenhuma resposta inventada), os pares são criados de duas formas, sem LLM:
# 1. **Extração por regras das definições oficiais:** Anexo I do CTB ("ACOSTAMENTO - parte da via..."),
#    art. 3º da LBI e art. 3º da PNRS ("I - coleta seletiva: ..."). A resposta é o próprio texto da lei, com uma
#    frase de abertura simples.
# 2. **Pares escritos pelo grupo** sobre os pontos mais importantes para a persona (calçada, buraco,
#    responsabilidade, prazos, multas). Cada resposta resume um trecho específico, citado no campo `fonte`,
#    em linguagem simples.
#
# Inclui também **perguntas fora do tema ou que exigem um profissional**, com recusa educada e encaminhamento.

# %%
NOMES_LEI = {"ctb_lei_9503_1997.html": "o Código de Trânsito Brasileiro", "lbi_lei_13146_2015.html": "a Lei Brasileira de Inclusão",
             "pnrs_lei_12305_2010.txt": "a Política Nacional de Resíduos Sólidos"}
TEXTO_POR_FONTE = {t["fonte"]: t["texto"] for t in textos}

def simplificar_final(s):
    s = s.strip().rstrip(";").strip()
    return s if s.endswith(".") else s + "."

qa_regras = []
# (a) CTB - Anexo I: "TERMO - definição"
ctb = TEXTO_POR_FONTE.get("ctb_lei_9503_1997.html", "")
anexo = ctb[ctb.find("DOS CONCEITOS E DEFINIÇÕES"):]
anexo = anexo[: anexo.find("ANEXO II")] if "ANEXO II" in anexo else anexo
for m in re.finditer(r"^([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9 ,/()\-]{2,80}?) - (.{20,1200}?)$", anexo, re.M):
    termo, definicao = m.group(1).strip(), m.group(2).strip()
    if len(termo.split()) > 8:
        continue
    t = termo.capitalize()
    qa_regras.append({"instruction": f"O que é {termo.lower()} segundo o Código de Trânsito Brasileiro?", "input": "",
                      "output": f"Pelo Código de Trânsito Brasileiro (Anexo I), {t.lower()} é: {simplificar_final(definicao)}",
                      "fonte": "ctb_lei_9503_1997.html"})
# (b) LBI e PNRS - art. 3º: "I - termo: definição;"
for fonte in ("lbi_lei_13146_2015.html", "pnrs_lei_12305_2010.txt"):
    txt = TEXTO_POR_FONTE.get(fonte, "")
    ini = txt.find("Art. 3º")
    fim = txt.find("Art. 4º", ini)
    bloco = txt[ini:fim if fim > 0 else ini + 15000]
    for m in re.finditer(r"(?:^|\s)([IVXLC]+) - ([^:;\n]{3,90}): (.{15,1500}?)(?=;\s+[IVXLC]+ - |;?\s*$|\.\s*$)", bloco, re.M):
        termo, definicao = m.group(2).strip(), m.group(3).strip()
        qa_regras.append({"instruction": f"O que significa {termo} para {NOMES_LEI[fonte]}?", "input": "",
                          "output": f"Segundo {NOMES_LEI[fonte]} (art. 3º, inciso {m.group(1)}), {termo} é: {simplificar_final(definicao)}",
                          "fonte": fonte})
print(f"Pares extraídos por regras: {len(qa_regras)}")
print(Counter(q["fonte"] for q in qa_regras))

# %%
SP, CTB, LBI, CART, PNRS = ("sp_lei_15442_2011.docx", "ctb_lei_9503_1997.html", "lbi_lei_13146_2015.html",
                            "cartilha_calcadas_sp_2024.pdf", "pnrs_lei_12305_2010.txt")
QA_MANUAL = [
    ("Quem é responsável por consertar a calçada em frente à minha casa?",
     "Em São Paulo, quem cuida da calçada é o responsável pelo imóvel em frente a ela: proprietário, condomínio ou quem tem a posse do imóvel. Ele deve construir, manter e conservar a calçada na largura da frente do terreno (Lei Municipal 15.442/2011, arts. 7º e 10).", SP),
    ("Quando a calçada é considerada em mau estado?",
     "Quando tem buracos, ondulações, desníveis que a rua não exige ou obstáculos que impeçam as pessoas de andar com segurança. Consertos feitos sem combinar com o resto da calçada também contam (Lei 15.442/2011, art. 7º, § 2º, II).", SP),
    ("A prefeitura também tem que cuidar de calçada?",
     "Sim. A União, o Estado e o Município são responsáveis pelas calçadas dos imóveis que são deles ou que estão sob sua guarda ou administração (Lei 15.442/2011, art. 10, II).", SP),
    ("Se a prefeitura quebrar minha calçada numa obra, quem paga o conserto?",
     "O Município deve reparar os danos que causar às calçadas quando fizer obras e melhorias públicas de sua responsabilidade (Lei 15.442/2011, art. 10, § 1º).", SP),
    ("E se a empresa de água, luz ou telefone quebrar a calçada?",
     "As empresas que usam as vias públicas para instalar equipamentos, como redes de água, energia ou telefonia, devem reparar os danos que causarem às calçadas, conforme a legislação específica (Lei 15.442/2011, art. 10, § 2º).", SP),
    ("A raiz de uma árvore estragou a calçada. Eu sou obrigado a arrumar?",
     "Enquanto a prefeitura não fizer o corte ou a retirada da árvore, você fica dispensado de consertar a calçada. Depois do corte, você tem 30 dias para regularizar a calçada (Lei 15.442/2011, art. 9º, §§ 1º e 2º).", SP),
    ("Qual a largura mínima livre que a calçada precisa ter para as pessoas passarem?",
     "Qualquer que seja a largura da calçada, deve existir uma faixa livre de no mínimo 1,20 metro, só para a circulação de pedestres (Lei 15.442/2011, art. 8º, parágrafo único).", SP),
    ("Posso colocar lixeira ou outro objeto no meio da calçada?",
     "Não se isso atrapalhar a passagem. Mobiliário como lixeiras, telefones públicos e caixas de correio não pode bloquear a circulação de pedestres, principalmente de pessoas com deficiência, nem a visibilidade nas esquinas. Quem descumprir pode ser multado (Lei 15.442/2011, art. 8º).", SP),
    ("Vou ser multado direto se minha calçada estiver quebrada?",
     "Não. Antes de qualquer multa, o responsável recebe uma Notificação Orientativa (Lei 15.442/2011, art. 10-A).", SP),
    ("Quanto tempo eu tenho para arrumar a calçada depois de ser autuado?",
     "Depois da autuação, o prazo para regularizar é de 60 dias. Se o problema for objeto bloqueando a calçada (art. 8º), o prazo cai para 20 dias (Lei 15.442/2011, art. 11).", SP),
    ("O dono de terreno baldio tem que manter o terreno limpo?",
     "Sim. Os responsáveis por imóveis, com construção ou não, de frente para a rua, devem mantê-los limpos, capinados e drenados, e respondem se o terreno for usado como depósito de lixo ou entulho (Lei 15.442/2011, art. 1º).", SP),
    ("Terreno baldio precisa ter muro?",
     "Sim, se a rua tiver pavimentação ou guias e sarjetas. O responsável deve fazer e conservar muro, gradil ou outro fechamento adequado. O fechamento deve ter 1,20 metro de altura em relação à rua e ter portão (Lei 15.442/2011, art. 2º e § 1º).", SP),
    ("O trânsito seguro é um direito meu?",
     "Sim. O Código de Trânsito diz que o trânsito em condições seguras é um direito de todos e um dever dos órgãos e entidades do Sistema Nacional de Trânsito (CTB, art. 1º, § 2º).", CTB),
    ("Se eu tiver prejuízo por causa de um buraco na rua, o poder público responde?",
     "O Código de Trânsito diz que os órgãos e entidades do Sistema Nacional de Trânsito respondem objetivamente por danos causados aos cidadãos por ação, omissão ou erro na execução e manutenção de programas, projetos e serviços que garantam o trânsito seguro (CTB, art. 1º, § 3º). Para pedir reparação no seu caso concreto, procure a prefeitura, a Defensoria Pública ou um advogado.", CTB),
    ("O que os órgãos de trânsito devem priorizar?",
     "Eles devem dar prioridade à defesa da vida, incluindo a preservação da saúde e do meio ambiente (CTB, art. 1º, § 5º).", CTB),
    ("O que o Código de Trânsito considera como trânsito?",
     "É o uso das vias por pessoas, veículos e animais, sozinhos ou em grupos, conduzidos ou não, para circular, parar, estacionar ou carregar e descarregar (CTB, art. 1º, § 1º).", CTB),
    ("Qual a altura livre mínima que a calçada deve ter?",
     "A faixa livre deve ter altura livre de pelo menos 2,10 metros sem placas, toldos ou coberturas, e de pelo menos 3,00 metros sem partes de construções, medida a partir do nível da calçada (Cartilha de Calçadas da Prefeitura de SP).", CART),
    ("Qual a inclinação máxima de lado (transversal) da calçada?",
     "A faixa livre deve ter inclinação transversal constante e não superior a 3% (Cartilha de Calçadas da Prefeitura de SP).", CART),
    ("A faixa livre da calçada pode ter obstáculos?",
     "Não. A faixa livre deve ser livre de barreiras e obstáculos, como equipamentos, mobiliário, vegetação ou rebaixamento de guia para carros, sejam permanentes ou temporários (Cartilha de Calçadas da Prefeitura de SP).", CART),
    ("Para que serve a faixa livre da calçada?",
     "A faixa livre é destinada exclusivamente à circulação de pedestres (Cartilha de Calçadas da Prefeitura de SP).", CART),
    ("O que é acessibilidade?",
     "É a possibilidade de usar, com segurança e autonomia, espaços, mobiliário, equipamentos urbanos, edificações, transportes, informação e comunicação, por pessoa com deficiência ou com mobilidade reduzida (Lei Brasileira de Inclusão, art. 3º, I).", LBI),
    ("Calçada esburacada pode ser considerada uma barreira para pessoa com deficiência?",
     "A Lei Brasileira de Inclusão chama de barreira qualquer obstáculo que limite ou impeça a participação social da pessoa, incluindo as barreiras urbanísticas, que são as existentes nas vias e espaços públicos (LBI, art. 3º, IV). Uma calçada que impede a passagem segura se encaixa nesse conceito.", LBI),
    ("Quem tem que dar destino certo ao lixo da cidade?",
     "A Política Nacional de Resíduos Sólidos estabelece a responsabilidade compartilhada pelo ciclo de vida dos produtos, envolvendo fabricantes, importadores, distribuidores, comerciantes, consumidores e os serviços públicos de limpeza urbana (Lei 12.305/2010).", PNRS),
    ("O que é coleta seletiva?",
     "É a coleta de resíduos sólidos que já foram separados de acordo com sua composição, como papel, plástico, vidro e metal (Lei 12.305/2010, art. 3º, V).", PNRS),
]
RECUSAS = [
    ("Me passa uma receita de bolo de cenoura?", "Desculpe, só posso ajudar com assuntos de vias, calçadas, buracos, lixo nas ruas e acessibilidade. Para outros assuntos, procure um serviço adequado."),
    ("Tenho dor no joelho desde que caí na calçada, que remédio eu tomo?", "Não posso indicar remédios nem fazer diagnóstico. Procure uma Unidade Básica de Saúde ou um médico. Em caso de emergência, ligue 192 (SAMU)."),
    ("Você pode entrar com o processo contra a prefeitura para mim?", "Não posso representar você na Justiça. Para entrar com uma ação, procure a Defensoria Pública, que atende gratuitamente quem não pode pagar advogado, ou um advogado de sua confiança."),
    ("Qual o CPF do dono do imóvel da esquina?", "Não posso fornecer dados pessoais de ninguém. Se a calçada está em mau estado, registre a ocorrência na prefeitura pela Central 156, que identifica o responsável."),
    ("Em quem eu devo votar para prefeito?", "Não dou opiniões políticas. Posso ajudar com dúvidas sobre calçadas, buracos, lixo nas ruas e acessibilidade."),
    ("Uma árvore caiu e tem fio elétrico no chão, o que eu faço?", "Isso é uma emergência: mantenha distância do fio e ligue agora para a Defesa Civil (199) ou para os Bombeiros (193). Não tente mexer no fio."),
]
qa_manual = [{"instruction": q, "input": "", "output": a, "fonte": f} for q, a, f in QA_MANUAL]
qa_recusa = [{"instruction": q, "input": "", "output": a, "fonte": "politica_do_assistente"} for q, a in RECUSAS]

# %% [markdown]
# ### Verificação automática de fidelidade
# Para os pares escritos pelo grupo, conferimos se os **números e trechos-chave** da resposta (ex.: "1,20",
# "60 dias", "art. 10-A") existem de fato no documento de origem. Pares que falham são exibidos para revisão.

# %%
def numeros_chave(texto):
    return set(re.findall(r"\d+(?:,\d+)?\s?%|\d+,\d+|\b\d{2,3}\b(?= dias)", texto))

falhas = []
for q in qa_manual:
    doc = TEXTO_POR_FONTE.get(q["fonte"], "")
    faltando = [n for n in numeros_chave(q["output"]) if n.replace(" ", "") not in doc.replace(" ", "")]
    if faltando:
        falhas.append((q["instruction"], faltando))
print("Pares com números não encontrados no documento:", falhas or "nenhum")

# %% [markdown]
# ## 8. Corpus conversacional
# Formato de mensagens com papéis `system`, `user` e `assistant`. Montamos:
# - **diálogos temáticos** com 2 ou 3 trocas, encadeando perguntas relacionadas da mesma fonte;
# - **diálogos sobre definições**, com o cidadão pedindo um termo e depois outro ("E o que é...?");
# - **diálogos de recusa ou encaminhamento** (pelo menos 10), em que o assistente recusa um pedido fora do tema
#   ou indica um profissional e depois volta a ajudar no tema.

# %%
SISTEMA = ("Você é o assistente do Cidade em Ordem, serviço público de zeladoria urbana. Responda de forma simples e "
           "educada, usando apenas as leis e cartilhas oficiais. Se a pergunta estiver fora do tema ou exigir um "
           "profissional, diga isso e indique onde procurar ajuda.")

def dialogo(trocas, fonte):
    msgs = [{"role": "system", "content": SISTEMA}]
    for u, a in trocas:
        msgs += [{"role": "user", "content": u}, {"role": "assistant", "content": a}]
    return {"messages": msgs, "fonte": fonte}

def reformular(pergunta):
    return "E " + pergunta[0].lower() + pergunta[1:] if not pergunta.lower().startswith(("e ", "o que")) else pergunta

corpus_chat = []
# (a) temáticos: blocos de 2-3 perguntas manuais da mesma fonte
por_fonte = {}
for q in qa_manual:
    por_fonte.setdefault(q["fonte"], []).append(q)
for fonte, itens in por_fonte.items():
    for i in range(0, len(itens) - 1, 2):
        bloco = itens[i:i + 3] if len(itens) - i == 3 else itens[i:i + 2]
        trocas = [(bloco[0]["instruction"], bloco[0]["output"])] + [(reformular(b["instruction"]), b["output"]) for b in bloco[1:]]
        corpus_chat.append(dialogo(trocas, fonte))
# (b) definições encadeadas
defs = [q for q in qa_regras]
random.Random(7).shuffle(defs)
usados = 0
for i in range(0, len(defs) - 1, 2):
    a, b = defs[i], defs[i + 1]
    if a["fonte"] != b["fonte"]:
        continue
    termo_b = re.search(r"(?:é|significa) (.+?) (?:segundo|para)", b["instruction"])
    seguinte = f"E o que é {termo_b.group(1)}?" if termo_b else b["instruction"]
    corpus_chat.append(dialogo([(a["instruction"], a["output"]), (seguinte, b["output"])], a["fonte"]))
    usados += 1
    if usados >= 22:
        break
# (c) recusas e encaminhamentos (12)
retornos = [
    ("Tudo bem. E de quem é a responsabilidade pela calçada da minha rua?", QA_MANUAL[0][1], SP),
    ("Entendi. Quando uma calçada é considerada em mau estado?", QA_MANUAL[1][1], SP),
    ("Certo. A prefeitura responde por danos causados por buracos?", QA_MANUAL[13][1], CTB),
    ("Ok. Qual a largura mínima livre da calçada?", QA_MANUAL[6][1], SP),
    ("Tá. E a calçada pode ter obstáculos?", QA_MANUAL[18][1], CART),
    ("Certo. E se a raiz de árvore quebrou a calçada?", QA_MANUAL[5][1], SP),
]
extras = [
    ("Qual vai ser a previsão do tempo amanhã?", "Não tenho informações de previsão do tempo. Consulte o site do INMET ou um serviço de meteorologia. Posso ajudar com calçadas, buracos e lixo nas ruas."),
    ("Escreve um trabalho da escola pra mim sobre a Revolução Francesa?", "Esse assunto está fora do que posso ajudar. Sou um assistente sobre zeladoria urbana: calçadas, vias, buracos, lixo e acessibilidade."),
    ("Meu vizinho jogou entulho na calçada, posso ir lá brigar com ele?", "Não recomendo confronto. Registre a ocorrência na Central 156 da prefeitura, que pode fiscalizar e notificar o responsável."),
    ("Caí num buraco e quebrei o braço, estou sangrando.", "Procure atendimento médico imediatamente. Ligue 192 (SAMU) se precisar de socorro. Depois, se quiser, posso explicar como registrar o problema da via."),
    ("Quanto eu vou receber de indenização se processar a prefeitura?", "Não consigo dizer valores: cada caso é analisado pela prefeitura ou pela Justiça. Para orientação jurídica gratuita, procure a Defensoria Pública."),
    ("Me ensina a consertar o buraco da rua eu mesmo com cimento?", "Não oriente consertos por conta própria em via pública: isso pode causar acidentes e é serviço da prefeitura. Registre o buraco na Central 156 para que a equipe responsável faça o reparo."),
]
todas_recusas = RECUSAS + extras
for i, (u, a) in enumerate(todas_recusas):
    u2, a2, f2 = retornos[i % len(retornos)]
    corpus_chat.append(dialogo([(u, a), (u2, a2)], f"politica_do_assistente; {f2}"))
print(f"Diálogos: {len(corpus_chat)} (recusas/encaminhamentos: {len(todas_recusas)})")

# %% [markdown]
# ## 9. Remoção de duplicatas e gravação dos arquivos JSONL

# %%
def chave(texto):
    return hashlib.md5(re.sub(r"\W+", "", texto.lower()).encode()).hexdigest()

def deduplicar(itens, campo, manter="primeiro"):
    vistos, saida = {}, []
    seq = itens if manter == "primeiro" else list(reversed(itens))
    for it in seq:
        k = chave(campo(it))
        if k in vistos:
            continue
        vistos[k] = True
        saida.append(it)
    if manter != "primeiro":
        saida.reverse()
    return saida, len(itens) - len(saida)

corpus_texto, dup_texto = deduplicar(corpus_texto, lambda x: x["text"])
# nas definições, a última ocorrência é a redação mais recente da lei
corpus_qa_bruto = qa_regras + qa_manual + qa_recusa
corpus_qa, dup_qa = deduplicar(corpus_qa_bruto, lambda x: x["instruction"], manter="ultimo")
corpus_chat, dup_chat = deduplicar(corpus_chat, lambda x: " ".join(m["content"] for m in x["messages"][1:]))

def salvar(nome, itens):
    with open(PASTA_SAIDA / nome, "w", encoding="utf-8") as f:
        for it in itens:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

salvar("corpus_texto.jsonl", corpus_texto)
salvar("corpus_qa.jsonl", corpus_qa)
salvar("corpus_chat.jsonl", corpus_chat)
print("Arquivos gravados em", PASTA_SAIDA.resolve())

# %% [markdown]
# ## 10. Relatório de qualidade

# %%
def media_tokens(itens, f):
    return round(sum(n_tokens(f(i)) for i in itens) / max(len(itens), 1), 1)

estatisticas = {
    "corpus_texto.jsonl": {"exemplos": len(corpus_texto), "minimo_exigido": 50, "media_tokens": media_tokens(corpus_texto, lambda x: x["text"]), "duplicatas_removidas": dup_texto},
    "corpus_qa.jsonl": {"exemplos": len(corpus_qa), "minimo_exigido": 100, "media_tokens": media_tokens(corpus_qa, lambda x: x["instruction"] + " " + x["output"]), "duplicatas_removidas": dup_qa},
    "corpus_chat.jsonl": {"exemplos": len(corpus_chat), "minimo_exigido": 30, "media_tokens": media_tokens(corpus_chat, lambda x: " ".join(m["content"] for m in x["messages"])), "duplicatas_removidas": dup_chat,
                          "dialogos_com_2_ou_mais_trocas": sum(1 for d in corpus_chat if sum(m["role"] == "user" for m in d["messages"]) >= 2)},
}
for nome, e in estatisticas.items():
    ok = "OK" if e["exemplos"] >= e["minimo_exigido"] else "ABAIXO DO MÍNIMO"
    print(f"{nome:20s} {e}  -> {ok}")
print("\nDuplicatas removidas já na limpeza (antes da segmentação):")
for fonte, d in DUPLICATAS_LIMPEZA.items():
    if fonte != "?":
        print(f"  {fonte:35s} {d}")
estatisticas["duplicatas_na_limpeza"] = DUPLICATAS_LIMPEZA
print("\nExemplos por fonte (texto):", dict(Counter(c["fonte"] for c in corpus_texto)))
print("Exemplos por fonte (QA):", dict(Counter(c["fonte"] for c in corpus_qa)))
(PASTA_SAIDA / "estatisticas.json").write_text(json.dumps({"estatisticas": estatisticas, "limpeza": rel_limpeza,
    "anonimizacao_exemplo": {"antes": limpo_exemplo, "depois": anon_exemplo}}, ensure_ascii=False, indent=1), encoding="utf-8")

for nome, itens in (("TEXTO", corpus_texto), ("QA", corpus_qa), ("CHAT", corpus_chat)):
    print(f"\n===== 5 exemplos aleatórios: {nome} =====")
    for it in random.Random(1).sample(itens, 5):
        print(json.dumps(it, ensure_ascii=False)[:600], "\n")

# %% [markdown]
# ## 11. Interface (Gradio): do upload até os corpus
# Envie arquivos PDF, TXT, DOCX ou HTML e/ou cole um texto. A ferramenta executa todas as etapas e devolve os
# três arquivos `.jsonl` e o relatório de qualidade.

# %%
import gradio as gr

def pipeline_interface(arquivos, texto):
    lista = []
    for a in arquivos or []:
        caminho = a if isinstance(a, str) else a.name
        lista.append((Path(caminho).name, Path(caminho).read_bytes()))
    docs = ingerir(lista, texto)
    if not docs:
        return "Envie pelo menos um arquivo ou cole um texto.", None, None, None
    txts, rel = processar(docs)
    ct = [{"text": tr, "fonte": t["fonte"]} for t in txts for tr in segmentar(t["texto"])]
    ct, d1 = deduplicar(ct, lambda x: x["text"])
    globais = {t["fonte"]: t["texto"] for t in txts}
    # pares por regras (definições) quando os documentos permitirem + pares do grupo cujas fontes foram enviadas
    qa = [q for q in qa_regras if q["fonte"] in globais] + [q for q in qa_manual if q["fonte"] in globais] + qa_recusa
    qa, d2 = deduplicar(qa, lambda x: x["instruction"], manter="ultimo")
    ch = [c for c in corpus_chat if any(f.strip() in globais or f.startswith("politica") for f in c["fonte"].split(";"))]
    pasta = Path("corpus_interface"); pasta.mkdir(exist_ok=True)
    caminhos = []
    for nome, itens in (("corpus_texto.jsonl", ct), ("corpus_qa.jsonl", qa), ("corpus_chat.jsonl", ch)):
        p = pasta / nome
        p.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in itens), encoding="utf-8")
        caminhos.append(str(p))
    md = "### Relatório\n| Corpus | Exemplos | Média de tokens | Duplicatas removidas |\n|---|---|---|---|\n"
    md += f"| Texto puro | {len(ct)} | {media_tokens(ct, lambda x: x['text'])} | {d1} |\n"
    md += f"| Perguntas e respostas | {len(qa)} | {media_tokens(qa, lambda x: x['instruction'] + x['output'])} | {d2} |\n"
    md += f"| Conversacional | {len(ch)} | {media_tokens(ch, lambda x: ' '.join(m['content'] for m in x['messages']))} | 0 |\n\n"
    md += "### Limpeza e anonimização por documento\n" + "\n".join(
        f"- **{r['fonte']}**: {r['caracteres_brutos']} → {r['caracteres_limpos']} caracteres ({r['reducao_%']}% de ruído removido); mascarados: {r['mascarados'] or 'nenhum'}" for r in rel)
    md += "\n\n### 5 trechos aleatórios\n" + "\n".join(f"> {c['text'][:300]}... *({c['fonte']})*\n" for c in random.sample(ct, min(5, len(ct))))
    return md, *caminhos

with gr.Blocks(title="Fábrica de Corpus - Cidade em Ordem") as app:
    gr.Markdown("# Fábrica de Corpus CitizenTech: Cidade em Ordem\nPDF, TXT, DOCX, HTML ou texto colado → corpus limpos e anonimizados para fine-tuning de SLM")
    with gr.Row():
        arqs = gr.File(file_count="multiple", file_types=[".pdf", ".txt", ".docx", ".html", ".htm"], label="Documentos")
        texto = gr.Textbox(lines=8, label="Ou cole um texto", value=TEXTO_COLADO_EXEMPLO)
    botao = gr.Button("Gerar corpus", variant="primary")
    rel_md = gr.Markdown()
    with gr.Row():
        f1, f2, f3 = gr.File(label="corpus_texto.jsonl"), gr.File(label="corpus_qa.jsonl"), gr.File(label="corpus_chat.jsonl")
    botao.click(pipeline_interface, [arqs, texto], [rel_md, f1, f2, f3])

if not SEM_INTERFACE:
    app.launch(share=NO_COLAB)
