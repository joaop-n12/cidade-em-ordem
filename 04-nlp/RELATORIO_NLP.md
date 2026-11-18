# Fábrica de Corpus CitizenTech: Cidade em Ordem

**Processamento de Linguagem Natural** · Global Solution 2026.2

| Integrante | RM |
|---|---|
| João Pedro de Souza Nunes | RM567318 |
| Guilherme Nakamura | RM567460 |

## 1. Problema e persona
**Persona: Dona Cida, 67 anos, moradora do Tatuapé (SP).** Tropeçou numa calçada quebrada perto de casa. Não sabe
se a culpa é do vizinho, da prefeitura ou da companhia de água que fez uma obra ali. Também não sabe se pode pedir
indenização ou se vai ser multada pela calçada da própria casa. As respostas existem, mas estão em leis longas,
com linguagem jurídica, espalhadas em sites diferentes.

**Por que um modelo pequeno e local:** prefeituras lidam com relatos de cidadãos que contêm dados pessoais. Um SLM
especializado, rodando nos servidores da prefeitura, responde sem enviar esses dados para a nuvem. A Fábrica de
Corpus prepara os dados de treino desse modelo. O mesmo corpus já é usado como base do assistente RAG
(disciplina de Generative AI) do projeto Cidade em Ordem.

**ODS:** **11** (cidades inclusivas e seguras, meta 11.2: acesso a sistemas de transporte seguros, com atenção a
idosos e pessoas com deficiência), **10** (redução das desigualdades: informação acessível a quem tem pouca
familiaridade com termos jurídicos) e **9** (infraestrutura de qualidade).

## 2. Fontes (públicas e oficiais)
| Documento | Formato de entrada | Tamanho | Origem |
|---|---|---|---|
| Cartilha "Calçadas e Vias Exclusivas de Pedestres" (SMPED/CPA, 2024) | PDF | 24 páginas | prefeitura.sp.gov.br |
| Código de Trânsito Brasileiro (Lei 9.503/1997, compilado) | HTML | ~119 páginas* | planalto.gov.br |
| Lei Brasileira de Inclusão (Lei 13.146/2015) | HTML | ~43 páginas* | planalto.gov.br |
| Lei Municipal 15.442/2011 (limpeza, fechamento de terrenos e calçadas) | DOCX** | ~6 páginas* | legislacao.prefeitura.sp.gov.br |
| Política Nacional de Resíduos Sólidos (Lei 12.305/2010) | TXT** | ~23 páginas* | planalto.gov.br |
| Relato fictício colado (com CPF, e-mail, telefone e nomes inventados) | texto colado | 1 parágrafo | criado pelo grupo para testar a anonimização |

\* estimado em 3.000 caracteres por página. Total: mais de 200 páginas.
\*\* publicados originalmente em HTML. Salvamos o texto em DOCX e em TXT (este em codificação Windows-1252, de
propósito) para testar todos os formatos e a conversão para UTF-8. O conteúdo não foi alterado.

A ferramenta (Colab + Gradio) aceita PDF, TXT, DOCX, HTML e texto colado, e registra o arquivo de origem de cada
trecho no campo `fonte`.

## 3. Decisões de limpeza e normalização
Todas as decisões vieram da inspeção dos documentos reais:

| Problema encontrado | Decisão |
|---|---|
| A fonte da cartilha transforma "ti" em `�` ("garan�r", "caracterís�cas") e "fi" em `ﬁ` | Normalização NFKC (ligaduras) e troca de `�` entre letras por "ti" |
| Cabeçalhos e rodapés do PDF ("CALÇADAS E VIAS EXCLUSIVAS DE PEDESTRES \| 03", "04 \| SMPED E CPA") | Removidos linhas que se repetem em mais de 30% das páginas e linhas no padrão `texto \| número` |
| Rótulos de desenho repetidos ("Altura MínimaAltura MínimaAltura Mínima") | Repetição interna reduzida a uma ocorrência |
| Palavras quebradas no fim da linha ("des-\nníveis") | Hífen de quebra removido e palavra unida |
| Anotações do Planalto ("(Redação dada pela Lei nº ...)", "(Incluído pela ...)", "(Vide ...)") | Removidas, porque não ensinam conteúdo ao cidadão |
| Dispositivos revogados (riscados com `<strike>` no Planalto) | Excluídos na extração do HTML |
| Mesmo artigo com redação antiga e nova (ex.: art. 11 da Lei 15.442: "30 dias" e "60 dias") | Mantida só a última versão (5 versões antigas removidas no total) |
| Incisos revogados vazios ("VII -; VIII -;") | Removidos |
| Ordinais do Planalto ("§ 1o", "Lei n o 10.650") | Padronizados para "§ 1º" e "Lei nº 10.650" |
| URLs soltas, caracteres de controle, marcadores gráficos | Removidos |
| Codificação mista (UTF-8 e Windows-1252) | Tudo convertido para UTF-8 (NFC). Aspas curvas viram retas, travessões viram hífen, espaços e quebras de linha unificados |

**Mantidos:** acentos, pontuação e maiúsculas. **Não** removemos stop words nem fizemos stemming, porque o modelo
de linguagem precisa do texto natural.

**Antes** (cartilha, página 3):
> Para garan�r a acessibilidade em calçadas, é necessário observar as seguintes caracterís�cas: Material de
> reves�mento do piso; inclinações (longitudinal e transversal); des-níveis; [...] 02 | SMPED E CPA

**Depois:**
> Para garantir a acessibilidade em calçadas, é necessário observar as seguintes características: Material de
> revestimento do piso; inclinações (longitudinal e transversal); desníveis; [...]

**Decisão revista durante o projeto:** na primeira versão, removíamos todos os parágrafos repetidos e 361 linhas do
CTB foram apagadas. Ao inspecionar, vimos que eram linhas como "Infração - grave; Penalidade - multa;", que se
repetem em vários artigos mas **pertencem a cada um**. Removê-las mudaria o sentido da lei. Passamos a deduplicar
apenas parágrafos com 80 caracteres ou mais (29 removidos no total).

## 4. Anonimização (LGPD)
Executada antes de gerar qualquer corpus: expressões regulares para CPF, CNPJ, e-mail e telefone; regras para
"meu nome é ..." e pronomes de tratamento (Sr., Dra.); NER do spaCy (`pt_core_news_sm`) para nomes de pessoas; e
mascaramento do bloco de assinaturas no fim das leis (presidente, prefeito, ministros).

**Antes:**
> Meu nome é Maria Aparecida Souza, CPF 123.456.789-09, telefone (11) 98765-4321 e e-mail maria.souza@exemplo.com.br.
> [...] O vizinho, Sr. José Carlos Pereira, também já caiu no mesmo lugar.

**Depois:**
> Meu nome é [NOME], CPF [CPF], telefone [TELEFONE] e e-mail [EMAIL]. [...] O vizinho, Sr. [NOME], também já caiu no mesmo lugar.

**Dificuldade e solução:** o NER do spaCy marcou como pessoa termos jurídicos como "Certificado de Registro",
"Distrito Federal" e "Pessoa com Deficiência" (87 mascaramentos de "nome" nos documentos oficiais na primeira versão, quase todos indevidos). Criamos um filtro:
só aceitamos como nome uma sequência de 2 ou mais palavras com inicial maiúscula em que **nenhuma palavra apareça em
minúscula em outro ponto do documento**. "registro", "federal" e "pessoa" aparecem em minúscula, então não são nomes.
O número de mascaramentos nos documentos oficiais caiu para 6 (assinaturas). Restam poucos casos de excesso de
mascaramento, o que é o lado seguro do erro para a LGPD.

## 5. Segmentação
Divisão em frases (sem quebrar depois de abreviações como "Art.", "arts.", "Sr.") e agrupamento até 512 tokens
(tokenizador `cl100k_base`), fechando o trecho só com pelo menos 256 tokens. **282 de 287 trechos (98%) ficaram entre 256 e
512 tokens.** Os poucos menores são finais de documento que não cabiam no trecho anterior.

## 6. Os três corpus: estatísticas
| Corpus | Exemplos | Mínimo | Média de tokens | Duplicatas removidas |
|---|---|---|---|---|
| `corpus_texto.jsonl` | **287** | 50 | 480 | 0 no corpus final (29 parágrafos e 5 versões antigas de artigos removidos na limpeza) |
| `corpus_qa.jsonl` | **183** | 100 | 89 | 0 |
| `corpus_chat.jsonl` | **46** (todos com 2 ou mais trocas) | 30 | 230 | 0 |

**Como os pares de pergunta e resposta foram criados (sem LLM):**
- **153 por regras**, extraídos das definições oficiais: Anexo I do CTB ("ACOSTAMENTO - parte da via...") e art. 3º da
  LBI e da PNRS ("V - coleta seletiva: ..."). A resposta é o texto da lei, então a **fidelidade é garantida**.
- **24 escritos pelo grupo** sobre os pontos centrais para a persona (responsabilidade pela calçada, prazos,
  notificação, árvore, faixa livre de 1,20 m). Cada resposta resume um artigo citado. Uma verificação automática
  confere se todos os números da resposta (1,20; 60 dias; 3%...) existem no documento de origem. **Resultado: nenhum
  número sem suporte.**
- **6 recusas** no corpus de perguntas e respostas e **12 diálogos de recusa ou encaminhamento** no corpus
  conversacional (receita, remédio, processo judicial, CPF de terceiro, política, fio caído, previsão do tempo...),
  que indicam SAMU, Defesa Civil, Defensoria Pública ou a Central 156.

Como não usamos LLM para gerar exemplos, não há prompt a relatar. Todos os pares escritos à mão foram revisados
(100%).

**Linguagem acessível:** as respostas escritas pelo grupo usam frases curtas e explicam termos ("quem tem a posse
do imóvel" em vez de "possuidor a qualquer título"). As respostas extraídas das definições mantêm o texto da lei,
com uma frase de abertura simples. Isso é um limite discutido abaixo.

Cinco exemplos aleatórios de cada corpus aparecem na saída do notebook (seção 10) e na interface Gradio.

## 7. Dificuldades e limites
1. **PDF com layout de cartilha:** legendas de desenhos ("Faixa de Acesso Faixa Livre Metade da largura...") viram texto
   corrido sem pontuação. A limpeza reduz o ruído, mas não reconstrói o layout.
2. **NER em texto jurídico:** exigiu o filtro de palavras em minúscula descrito na seção 4.
3. **Definições do CTB são técnicas** ("veículo conjugado", "etilômetro"): fiéis, mas pouco relevantes para a persona e
   em linguagem difícil. Um próximo passo seria reescrevê-las em linguagem simples com revisão humana.
4. **Peso do CTB:** 57% dos trechos vêm do CTB por ser o documento maior. Para o fine-tuning, seria bom balancear
   (subamostrar o CTB ou adicionar mais cartilhas municipais).

## 8. Entregáveis
- Código: `fabrica_corpus.ipynb` (Colab, roda do início ao fim, com interface Gradio na última célula)
- Documentos de entrada: `documentos/` (e os links oficiais acima)
- Corpus: `corpus/corpus_texto.jsonl`, `corpus/corpus_qa.jsonl`, `corpus/corpus_chat.jsonl` e `corpus/estatisticas.json`
- Log da execução: `corpus/log_execucao.txt`
- Vídeo (até 5 min, do upload até a geração dos corpus): ⬜ link
