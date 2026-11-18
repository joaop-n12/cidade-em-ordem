# Fábrica de Corpus CitizenTech: Cidade em Ordem (NLP)

**Integrantes:** João Pedro de Souza Nunes (RM567318) · Guilherme Nakamura (RM567460)

Ferramenta que transforma leis e cartilhas públicas sobre calçadas, vias e limpeza urbana em três corpus JSONL
(texto puro, perguntas e respostas, conversacional) para fine-tuning de um modelo de linguagem pequeno.
Relatório completo: [RELATORIO_NLP.md](RELATORIO_NLP.md).

## Como executar
**Colab (recomendado):** abra `fabrica_corpus.ipynb` no Google Colab e use *Executar tudo*. A primeira célula instala
as bibliotecas, a segunda baixa os documentos das fontes oficiais e a última abre a interface Gradio (link público).

**Local:**
```bash
pip install pypdf python-docx beautifulsoup4 tiktoken gradio spacy
python -m spacy download pt_core_news_sm
jupyter notebook fabrica_corpus.ipynb
```

## Bibliotecas
pypdf (PDF), python-docx (DOCX), BeautifulSoup (HTML), tiktoken (contagem de tokens), spaCy `pt_core_news_sm`
(nomes de pessoas), Gradio (interface).

## Saídas
`corpus/corpus_texto.jsonl` (287) · `corpus/corpus_qa.jsonl` (183) · `corpus/corpus_chat.jsonl` (46) ·
`corpus/estatisticas.json`
