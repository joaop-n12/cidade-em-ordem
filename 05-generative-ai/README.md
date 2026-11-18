# Cidade em Ordem: Assistente generativo do cidadão

**Generative AI and Advanced Nets** · Global Solution 2026.2 · CitizenTech

| Integrante | RM |
|---|---|
| João Pedro de Souza Nunes | RM567318 |
| Guilherme Nakamura | RM567460 |

## 1. Problema, público e funcionalidade
**Problema:** em 2025 a Prefeitura de São Paulo recebeu 113,1 mil pedidos de tapa-buraco. O Cidade em Ordem
detecta buracos automaticamente pelo caminhão de coleta, mas o cidadão continua com dúvidas que ninguém responde
com clareza: *de quem é a calçada? a prefeitura paga o meu pneu? quando vão arrumar a minha rua?* As respostas
estão espalhadas em leis longas e em linguagem jurídica.

**Público:** cidadãos de São Paulo, especialmente idosos e pessoas com deficiência (persona: *Dona Cida, 67 anos,
tropeçou numa calçada quebrada*), com pouca familiaridade com termos técnicos.

**Funcionalidade desenvolvida:** um assistente que
1. responde dúvidas **com base em leis e cartilhas oficiais**, citando a fonte (RAG);
2. consulta o **status real** das ordens de serviço geradas pelo robô RPA (ferramenta / agente);
3. **protege o cidadão**: mascara dados pessoais antes do LLM, reconhece emergências e recusa assuntos fora do tema.

**Benefício:** a orientação passa a ser imediata, em linguagem simples e verificável (cada resposta mostra de qual
lei veio), sem depender do atendimento telefônico.

## 2. Abordagem de IA e justificativa
| Abordagem | Por que |
|---|---|
| **RAG (Retrieval-Augmented Generation)** | A resposta precisa ser fiel à lei. Um LLM sozinho alucina artigos e prazos. Com RAG, o modelo só escreve a partir de trechos recuperados, e a resposta cita a fonte |
| **Transformers / foundation models** | Embeddings `paraphrase-multilingual-MiniLM-L12-v2` (Transformer, português, roda localmente). LLM Gemini 2.5 Flash ou Llama 3.3 70B (Groq), ambos com camada gratuita |
| **Prompt engineering** | Prompt de sistema com 6 regras: só usar o contexto, citar [n], linguagem simples, no máximo 6 frases, não dar aconselhamento individual, não inventar números |
| **Arquitetura agêntica (simples)** | Um roteador decide entre a ferramenta `consultar_ordens` (dados vivos do robô RPA) e o RAG (conhecimento estático). Os guardrails agem antes e depois do modelo |

**Não é um chatbot genérico:** a base de conhecimento é o **corpus limpo e anonimizado construído na disciplina de
NLP** (5 documentos oficiais, 287 trechos e 183 pares de pergunta e resposta revisados), e a ferramenta lê as
ordens de serviço reais do robô.

## 3. Arquitetura e fluxo
```
Cidadão (Gradio ou front-end React via POST /perguntar)
   │
   ▼
[Guardrail de entrada] mascara CPF, e-mail, telefone, placa, nome ("meu nome é ...")
   │
   ├── emergência? ("sangrando", "fio no chão") ──> orientação SAMU 192 / Bombeiros 193 / Defesa Civil 199
   ├── status de rua? ("quando vão arrumar a Rua X") ──> FERRAMENTA consultar_ordens(06-rpa/saida/ordens_servico.json)
   └── RAG:
         busca híbrida (FAISS vetorial + BM25, fusão RRF) → 4 trechos
         relevância vetorial < 0,45 ──> "fora do tema" (o LLM nem é chamado)
         prompt (regras + contexto numerado) → LLM (LangChain: Gemini ou Groq)
         [Guardrail de saída] erro ou resposta vazia → modo extrativo (resposta revisada do corpus)
                              número na resposta que não existe no contexto → aviso de verificação
   ▼
Resposta + fontes + trechos (painel técnico no Gradio)
```

| Componente | Arquivo | Papel |
|---|---|---|
| Base de conhecimento | `assistente/base_conhecimento.py` | Carrega `04-nlp/corpus/*.jsonl`, gera embeddings e o índice FAISS |
| Recuperação híbrida e orquestração | `assistente/rag.py` | Roteador, busca híbrida, prompt, LLM, fallback e verificação |
| Guardrails | `assistente/guardrails.py` | Mascaramento LGPD, emergência, fora do tema, números sem suporte |
| Ferramenta | `assistente/ferramentas.py` | Consulta as OS do robô RPA |
| Aplicação | `app.py` | FastAPI (`POST /perguntar`, usado pelo front-end) e Gradio (`/`) |
| Avaliação | `avaliacao/avaliar.py` | 24 perguntas de teste com métricas |

## 4. Integração com a solução CitizenTech
- **NLP → GenAI:** o corpus produzido pela Fábrica de Corpus é a base do RAG. O mesmo corpus serviria para o fine-tuning
  de um modelo local no futuro.
- **RPA → GenAI:** a ferramenta lê `06-rpa/saida/ordens_servico.json`, gerado a partir das detecções da câmera e do sensor.
- **GenAI → Front-end:** a tela **Assistente** do app React chama `POST /perguntar` quando `VITE_RAG_URL` está configurada.
  Se a API estiver fora do ar, o front usa uma base local (caminho seguro).

## 5. Testes e avaliação
24 perguntas com resposta esperada: 18 de conteúdo (5 documentos), 2 de status de rua, 2 de emergência, 2 fora do
tema e 1 com dados pessoais. Resultados completos em `avaliacao/`.

| Métrica | v1: só vetorial | **v2: híbrida (vetorial + BM25)** |
|---|---|---|
| Roteamento correto | 24/24 (100%) | **24/24 (100%)** |
| Fonte certa entre os 4 trechos (acerto@4) | 16/18 (89%) | **18/18 (100%)** |
| Resposta com as palavras-chave esperadas | 20/24 (83%) | **23/24 (96%)** |
| Respostas RAG com citação [n] | 18/18 | 18/18 |
| Número sem suporte no contexto | 0/18 | 0/18 |

*Medido no modo extrativo (sem LLM), que isola a qualidade da recuperação e do roteamento.* ⬜ **Rodar
`python avaliacao/avaliar.py` com a chave do Gemini no `.env` e colar aqui a coluna "com LLM"** (arquivo
`avaliacao/resultados_llm.md`).

**Análise dos erros da v1:** para "O que é acessibilidade pela lei?", a busca vetorial trouxe um trecho do CTB
sobre "recusar-se a entregar documentos à autoridade". O modelo de embedding pequeno aproximou "acessibilidade"
de "acesso/entrega". O mesmo ocorreu com "barreiras urbanísticas", que puxou "via urbana". **Correção:** busca
híbrida. O BM25 garante que termos exatos da lei ("acessibilidade", "barreiras") pesem na recuperação.
A única pergunta que ainda "falha" na v2 ("O que é coleta seletiva?") recupera a fonte certa e responde
corretamente, mas em linguagem simplificada: "resíduos **separados**" em vez do termo da lei "resíduos
**segregados**". Isso mostra um limite da métrica por palavra-chave. Ela não reconhece paráfrases, e por isso
os resultados também foram revisados manualmente.

## 6. Limitações, riscos e mitigação
| Risco | Mitigação |
|---|---|
| **Alucinação** (inventar prazo, valor ou artigo) | RAG obrigatório. Prompt proíbe conhecimento externo. Verificação automática de números. Citação [n] para o cidadão conferir |
| **Recuperação errada** | Busca híbrida, resposta "não encontrei" quando a relevância é baixa e painel com os trechos usados |
| **Privacidade (LGPD)** | Dados pessoais mascarados antes de qualquer chamada externa. O corpus já é anonimizado. Embeddings rodam localmente |
| **Viés e desatualização** | Base limitada a 5 documentos de SP e federais. Leis mudam, por isso o corpus é reprocessado pela Fábrica de Corpus. Outras cidades exigiriam outros documentos |
| **API do LLM indisponível** | Timeout de 30 s, 2 retentativas e modo extrativo como caminho seguro |
| **Segurança** | Chaves no `.env` (fora do Git), CORS restrito ao front, entrada limitada a 1.000 caracteres |

**Exige validação humana:** pedidos de indenização (cada caso é analisado pela prefeitura ou pela Justiça), qualquer
orientação jurídica individual e a gravidade real de um buraco (vistoria presencial). O assistente informa e
encaminha. Ele não decide.

## 7. Como executar
```bash
cd 05-generative-ai
pip install -r requirements.txt
cp .env.example .env        # coloque GOOGLE_API_KEY (grátis em https://aistudio.google.com/apikey) ou GROQ_API_KEY
python app.py               # abre http://localhost:8000
python avaliacao/avaliar.py # avaliação
```
Sem chave, o app funciona no **modo extrativo** (recuperação, ferramenta e guardrails ativos, sem redação pelo LLM).
Para ligar ao front-end: em `01-front-end/.env`, coloque `VITE_RAG_URL=http://localhost:8000/perguntar`.

Vídeo de demonstração: ⬜ link
