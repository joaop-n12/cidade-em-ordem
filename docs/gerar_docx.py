"""
Converte os relatórios .md do projeto em .docx.
- Documento de Governança: formato ABNT/FIAP (capa, folha de rosto, lista de quadros, sumário, Arial 12, 1,5,
  margens 3/2 cm, numeração de página).
- Demais relatórios: mesma formatação, com capa simples.

Uso: python docs/gerar_docx.py
Depois de abrir no Word: clique no sumário e pressione F9 para atualizar os números de página.
"""

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

RAIZ = Path(__file__).resolve().parents[1]
RELATORIOS = [
    ("09-governanca/DOCUMENTO_GOVERNANCA.md", "09-governanca/Documento_Governanca_CidadeEmOrdem.docx", True),
    ("02-iot/RELATORIO_IOT.md", "02-iot/Relatorio_IoT_CidadeEmOrdem.docx", False),
    ("04-nlp/RELATORIO_NLP.md", "04-nlp/Relatorio_NLP_CidadeEmOrdem.docx", False),
    ("03-visao-computacional/RELATORIO_VISAO.md", "03-visao-computacional/Relatorio_Visao_CidadeEmOrdem.docx", False),
    ("08-computacao-quantica/RELATORIO_QUANTICA.md", "08-computacao-quantica/Relatorio_Quantica_CidadeEmOrdem.docx", False),
    ("05-generative-ai/README.md", "05-generative-ai/Documentacao_GenAI_CidadeEmOrdem.docx", False),
    ("06-rpa/README.md", "06-rpa/Documentacao_RPA_CidadeEmOrdem.docx", False),
]


def campo(paragrafo, instrucao):
    """Insere um campo do Word (PAGE, TOC...)."""
    run = paragrafo.add_run()
    for tipo, texto in (("begin", None), (None, instrucao), ("separate", None), (None, "Atualize com F9"), ("end", None)):
        if tipo:
            el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), tipo); run._r.append(el)
        elif texto == instrucao:
            el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = instrucao; run._r.append(el)
        else:
            t = OxmlElement("w:t"); t.text = texto; run._r.append(t)


def estilo_base(doc, abnt=True):
    """ABNT (Governança): Arial 12, espaçamento 1,5. Demais relatórios: Arial 11, 1,15 (mais compactos)."""
    tam_txt, esp = (12, 1.5) if abnt else (11, 1.15)
    st = doc.styles["Normal"]
    st.font.name = "Arial"; st.font.size = Pt(tam_txt)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    pf = st.paragraph_format
    pf.line_spacing = esp; pf.space_after = Pt(6 if abnt else 4); pf.first_line_indent = Cm(1.25 if abnt else 0)
    for nome, tam in (("Heading 1", 12), ("Heading 2", 12), ("Heading 3", 12)):
        h = doc.styles[nome]
        h.font.name = "Arial"; h.font.size = Pt(tam); h.font.bold = True; h.font.color.rgb = None
        h.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
        h.paragraph_format.first_line_indent = Cm(0); h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.line_spacing = esp
        if not abnt:
            h.paragraph_format.space_before = Pt(8)
    for s in doc.sections:
        s.top_margin = Cm(3 if abnt else 2); s.left_margin = Cm(3 if abnt else 2.5)
        s.bottom_margin = Cm(2); s.right_margin = Cm(2)


def texto_rico(paragrafo, texto):
    """Suporta **negrito**, *itálico* e `código`."""
    for parte in re.split(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)", texto):
        if not parte:
            continue
        if parte.startswith("**"):
            paragrafo.add_run(parte[2:-2]).bold = True
        elif parte.startswith("`"):
            r = paragrafo.add_run(parte[1:-1]); r.font.name = "Consolas"; r.font.size = Pt(10)
        elif parte.startswith("*") and len(parte) > 2:
            paragrafo.add_run(parte[1:-1]).italic = True
        else:
            paragrafo.add_run(parte)


def centro(doc, texto, negrito=False, antes=0, tam=12):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0); p.paragraph_format.space_before = Pt(antes)
    r = p.add_run(texto); r.bold = negrito; r.font.size = Pt(tam)
    return p


def quebra(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def capa_abnt(doc, meta, quadros):
    centro(doc, meta["instituicao"].upper(), True)
    centro(doc, meta["curso"].upper(), True)
    for nome in meta["integrantes"].split(";"):
        centro(doc, nome.strip().upper(), antes=6 if nome is meta["integrantes"].split(";")[0] else 0)
    centro(doc, meta["titulo"], True, antes=150, tam=14)
    centro(doc, meta["subtitulo"])
    centro(doc, meta["local"].upper(), antes=200)
    centro(doc, meta["ano"])
    quebra(doc)
    # folha de rosto
    for nome in meta["integrantes"].split(";"):
        centro(doc, nome.strip().upper())
    centro(doc, meta["titulo"], True, antes=120, tam=14)
    centro(doc, meta["subtitulo"])
    p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(8); p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(60); p.paragraph_format.line_spacing = 1.0
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(meta["natureza"]); r.font.size = Pt(10)
    centro(doc, meta["local"].upper(), antes=150)
    centro(doc, meta["ano"])
    quebra(doc)
    # lista de quadros e figuras
    centro(doc, "LISTA DE QUADROS E FIGURAS", True)
    for q in quadros:
        p = doc.add_paragraph(q); p.paragraph_format.first_line_indent = Cm(0)
    quebra(doc)
    centro(doc, "SUMÁRIO", True)
    p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Cm(0)
    campo(p, 'TOC \\o "1-3" \\h \\z \\u')
    quebra(doc)


DISCIPLINAS = {
    "02-iot": "Physical Computing, Embedded AI, Robotics & Cognitive IoT",
    "03-visao-computacional": "Visão Computacional",
    "04-nlp": "Processamento de Linguagem Natural",
    "05-generative-ai": "Generative AI and Advanced Nets",
    "06-rpa": "AI for Robotic Process Automation",
    "07-cluster-memristor": "Cluster Computing, Computação Neuromórfica e Supercomputadores",
    "08-computacao-quantica": "Computação Quântica & IA",
}
INTEGRANTES = [("João Pedro de Souza Nunes", "RM567318"), ("Guilherme Nakamura", "RM567460")]


def linha_cor(doc, cor="0B5CAD", espessura=12):
    """Linha horizontal colorida (borda inferior de um parágrafo vazio)."""
    p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Cm(0)
    pPr = p._p.get_or_add_pPr(); bdr = OxmlElement("w:pBdr"); b = OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", str(espessura)), ("w:space", "1"), ("w:color", cor)):
        b.set(qn(k), v)
    bdr.append(b); pPr.append(bdr)


def capa_completa(doc, titulo, disciplina):
    from docx.shared import RGBColor
    azul = RGBColor(0x0B, 0x5C, 0xAD)
    def linha(texto, tam=12, negrito=False, cor=None, antes=0, depois=0):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf = p.paragraph_format; pf.first_line_indent = Cm(0); pf.space_before = Pt(antes); pf.space_after = Pt(depois)
        pf.line_spacing = 1.15
        r = p.add_run(texto); r.font.size = Pt(tam); r.bold = negrito
        if cor:
            r.font.color.rgb = cor
        return p
    linha("FIAP - FACULDADE DE INFORMÁTICA E ADMINISTRAÇÃO PAULISTA", 12, True)
    linha("Tecnologia em Inteligência Artificial", 11)
    linha("Global Solution 2026.2 · CitizenTech", 11, depois=6)
    linha_cor(doc)
    linha(disciplina.upper(), 11, True, azul, antes=60)
    linha("CIDADE EM ORDEM", 28, True, azul, antes=40)
    linha("A cidade encontra o buraco antes de você precisar reclamar", 12, cor=RGBColor(0x4A, 0x55, 0x68), depois=30)
    linha(titulo, 15, True, antes=10)
    linha("Integrantes", 11, True, antes=90, depois=4)
    for nome, rm in INTEGRANTES:
        linha(f"{nome} · {rm}", 11)
    linha("São Paulo", 11, antes=110)
    linha("2026", 11)
    quebra(doc)


def capa_simples(doc, titulo):
    centro(doc, "FIAP - TECNOLOGIA EM INTELIGÊNCIA ARTIFICIAL", True)
    centro(doc, "Global Solution 2026.2 - CitizenTech - Cidade em Ordem")
    centro(doc, titulo, True, antes=24, tam=14)


def tabela(doc, linhas, com_fonte=False):
    cab = [c.strip() for c in linhas[0].strip("|").split("|")]
    corpo = [[c.strip() for c in l.strip().strip("|").split("|")] for l in linhas[2:]]
    t = doc.add_table(rows=1, cols=len(cab)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, c in enumerate(cab):
        cel = t.rows[0].cells[i]; cel.text = ""
        p = cel.paragraphs[0]; p.paragraph_format.first_line_indent = Cm(0); p.paragraph_format.line_spacing = 1.0
        r = p.add_run(c.replace("**", "")); r.bold = True; r.font.size = Pt(10)
    for linha in corpo:
        row = t.add_row().cells
        for i in range(len(cab)):
            p = row[i].paragraphs[0]; p.paragraph_format.first_line_indent = Cm(0); p.paragraph_format.line_spacing = 1.0
            texto_rico(p, linha[i] if i < len(linha) else "")
            for r in p.runs:
                r.font.size = Pt(10)
    if com_fonte:  # só nos quadros numerados (ABNT)
        fonte = doc.add_paragraph("Fonte: elaborado pelos autores (2026).")
        fonte.paragraph_format.first_line_indent = Cm(0); fonte.runs[0].font.size = Pt(10)


def inicia_bloco(l):
    """A linha começa um novo bloco (título, lista, tabela, imagem...)?"""
    s = l.strip()
    return (not s or s.startswith(("#", "|", "```", ">", "![", "[QUADRO", "[FIGURA", "---"))
            or re.match(r"^[-*] ", s) or re.match(r"^\d+\. ", s))


def juntar(linhas, i, texto, so_indentadas=False):
    """Junta as linhas seguintes do mesmo parágrafo (o Markdown quebra linhas longas)."""
    while i + 1 < len(linhas):
        prox = linhas[i + 1]
        if inicia_bloco(prox) or (so_indentadas and not prox.startswith((" ", "\t"))):
            break
        i += 1
        texto += " " + prox.strip()
    return texto, i


def converter(md_path, docx_path, abnt):
    texto = md_path.read_text(encoding="utf-8")
    meta = {}
    if texto.startswith("---"):
        _, fm, texto = texto.split("---", 2)
        for l in fm.strip().splitlines():
            k, v = l.split(":", 1); meta[k.strip()] = v.strip()
    doc = Document(); estilo_base(doc, abnt)
    linhas = texto.strip().splitlines()
    quadros = [l.strip("[] ").replace(" - ", " – ", 1) for l in linhas if re.match(r"\[(QUADRO|FIGURA) \d+", l)]
    if abnt:
        capa_abnt(doc, meta, quadros)
    else:
        titulo = next((l.lstrip("# ").strip() for l in linhas if l.startswith("# ")), md_path.stem)
        titulo_capa = titulo
        if titulo_capa.startswith("Cidade em Ordem:"):  # o nome do projeto já aparece em destaque na capa
            resto = titulo_capa[len("Cidade em Ordem:"):].strip()
            titulo_capa = resto[:1].upper() + resto[1:]
        capa_completa(doc, titulo_capa, DISCIPLINAS.get(md_path.parent.name, ""))
        # remove o título e o bloco de identificação (disciplina, integrantes) que já estão na capa
        ini = next(k for k, l in enumerate(linhas) if l.startswith("# "))
        fim = next((k for k, l in enumerate(linhas) if k > ini and l.startswith("## ")), ini + 1)
        linhas = linhas[:ini] + linhas[fim:]
    i = 0
    while i < len(linhas):
        l = linhas[i]
        if l.startswith("```"):
            bloco = []; i += 1
            while i < len(linhas) and not linhas[i].startswith("```"):
                bloco.append(linhas[i]); i += 1
            p = doc.add_paragraph(); p.paragraph_format.first_line_indent = Cm(0); p.paragraph_format.line_spacing = 1.0
            r = p.add_run("\n".join(bloco)); r.font.name = "Consolas"; r.font.size = Pt(8)
        elif l.startswith("|") and i + 1 < len(linhas) and re.match(r"^\|[\s:|-]+\|$", linhas[i + 1].strip()):
            bloco = []
            while i < len(linhas) and linhas[i].startswith("|"):
                bloco.append(linhas[i]); i += 1
            anterior = next((x for x in reversed(linhas[:i - len(bloco)]) if x.strip()), "")
            tabela(doc, bloco, com_fonte=bool(re.match(r"\[QUADRO \d+", anterior))); continue
        elif re.match(r"!\[[^\]]*\]\(([^)]+)\)", l.strip()):
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", l.strip())
            img = md_path.parent / m.group(2)
            if img.exists():
                from PIL import Image as _I; doc.add_picture(str(img), width=Cm(9 if _I.open(img).width < 1000 else 13))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap = doc.add_paragraph(); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER; cap.paragraph_format.first_line_indent = Cm(0)
            r = cap.add_run(m.group(1) if img.exists() else f"[inserir imagem: {m.group(2)}]"); r.font.size = Pt(10)
        elif re.match(r"\[(QUADRO|FIGURA) \d+", l):
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.first_line_indent = Cm(0)
            r = p.add_run(l.strip("[] ")); r.bold = True; r.font.size = Pt(10)
        elif l.startswith("#"):
            nivel = min(len(l) - len(l.lstrip("#")), 3)
            titulo = re.sub(r"\*+|`", "", l.lstrip("# ").strip())  # títulos sem marcas de negrito/itálico
            if abnt and nivel == 1:
                quebra(doc) if titulo not in ("1 INTRODUÇÃO",) else None
            doc.add_heading(titulo.upper() if nivel == 1 else titulo, level=nivel)
        elif re.match(r"^\s*[-*] ", l):
            texto, i = juntar(linhas, i, re.sub(r"^\s*[-*] ", "", l), so_indentadas=True)
            p = doc.add_paragraph(style="List Bullet"); p.paragraph_format.first_line_indent = Cm(0)
            texto_rico(p, texto)
        elif re.match(r"^\d+\. ", l):
            texto, i = juntar(linhas, i, re.sub(r"^\d+\. ", "", l), so_indentadas=True)
            p = doc.add_paragraph(style="List Number"); p.paragraph_format.first_line_indent = Cm(0)
            texto_rico(p, texto)
        elif l.startswith(">"):
            texto = l.lstrip("> ")
            while i + 1 < len(linhas) and linhas[i + 1].startswith(">"):
                i += 1; texto += " " + linhas[i].lstrip("> ")
            p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(4); p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.line_spacing = 1.0
            texto_rico(p, texto); [setattr(r.font, "size", Pt(10)) for r in p.runs]
        elif l.strip() and not l.startswith("---"):
            texto, i = juntar(linhas, i, l.strip())
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            texto_rico(p, texto)
        i += 1
    # numeração de página no canto superior direito (ABNT)
    for s in doc.sections:
        s.different_first_page_header_footer = True  # sem número na capa
        p = s.header.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.RIGHT; campo(p, "PAGE")
    doc.save(docx_path)
    print("gerado:", Path(docx_path).resolve().relative_to(RAIZ))


if __name__ == "__main__":
    for md, dx, abnt in RELATORIOS:
        origem = RAIZ / md
        if origem.exists():
            converter(origem, RAIZ / dx, abnt)
        else:
            print("ainda não existe:", md)
