# Cidade em Ordem
**A cidade encontra o buraco antes de você precisar reclamar.**

Global Solution 2026.2 · FIAP · Tecnologia em Inteligência Artificial · Tema **CitizenTech**

| Integrante | RM |
|---|---|
| João Pedro de Souza Nunes | RM567318 |
| Guilherme Nakamura | RM567460 |

## O problema
Em 2025 a Prefeitura de São Paulo recebeu **113,1 mil pedidos de tapa-buraco**, quase 300 por dia, e reconhece que
um mesmo buraco gera vários chamados. Aplicativos como a Zeladoria do Poupatempo/SP156 **dependem do cidadão parar
e reclamar**. Bairros que reclamam menos ficam esquecidos, e buracos causam quedas de motociclistas, danos a
veículos e riscos a pedestres, idosos e pessoas com deficiência. *(Fontes em [docs/dados_do_problema.md](docs/dados_do_problema.md).)*

## A solução
Os **caminhões de coleta de lixo já passam por todas as ruas** várias vezes por semana. Com uma câmera e um sensor
de baixo custo, eles passam a detectar buracos automaticamente. Um robô junta as detecções, elimina repetições,
calcula a prioridade e abre a ordem de serviço. O cidadão acompanha pelo app e tira dúvidas com um assistente que
responde com base nas leis.

```
 Caminhão de coleta                         Central                                   Cidadão / Prefeitura
┌───────────────────┐   detecções   ┌───────────────────────────┐   OS (JSON/Excel)   ┌──────────────────────┐
│ Câmera → YOLO11n  │──────────────>│ Robô RPA                  │────────────────────>│ Front-end React       │
│ (03-visao)        │               │ DBSCAN + APIs + prioridade│                     │ mapa, status, triagem │
│ ESP32 + MPU6050 + │──MQTT────────>│ (06-rpa)                  │                     │ (01-front-end)        │
│ HC-SR04 (02-iot)  │<─comando LED──│ Receptor + SQLite (02-iot)│                     │        │ POST         │
└───────────────────┘               └───────────────────────────┘                     │        ▼              │
                                     Leis e cartilhas → Fábrica de Corpus (04-nlp) ──>│ Assistente RAG        │
                                                                                      │ (05-generative-ai)    │
                                                                                      └──────────────────────┘
 Estudos de evolução: memristor para registrar impactos (07) · otimização quântica de rotas e PQC (08)
```

## Estrutura do repositório
| Pasta | Disciplina | O que tem |
|---|---|---|
| [01-front-end](01-front-end) | Front End & Mobile Development | App React + Vite: login local, cadastro e consulta de ocorrências, mapa, IA de triagem, assistente |
| [02-iot](02-iot) | Physical Computing, Embedded AI & Cognitive IoT | ESP32 no Wokwi (2 sensores), MQTT, receptor Python, SQLite, relatório |
| [03-visao-computacional](03-visao-computacional) | Visão Computacional | Notebook YOLO11n (transfer learning), métricas, robustez, FPS, vídeo, Gradio |
| [04-nlp](04-nlp) | Processamento de Linguagem Natural | Fábrica de Corpus: 5 documentos oficiais → 3 corpus JSONL anonimizados |
| [05-generative-ai](05-generative-ai) | Generative AI and Advanced Nets | Assistente RAG híbrido (LangChain), ferramenta de OS, guardrails, Gradio/FastAPI |
| [06-rpa](06-rpa) | AI for Robotic Process Automation | Robô de ponta a ponta: validação, DBSCAN, APIs, Excel, idempotência, revisão humana |
| [07-cluster-memristor](07-cluster-memristor) | Cluster, Computação Neuromórfica e Supercomputadores | Simulação de memristor no Falstad para registrar impactos |
| [08-computacao-quantica](08-computacao-quantica) | Computação Quântica & IA | Gargalo, capacidade quântica (otimização) e roadmap realista |
| [09-governanca](09-governanca) | Governança em IA e Business Analytics | Documento de integração (ABNT) e roteiro do vídeo |

## Como rodar a demonstração integrada
```bash
# 1. IoT: receptor MQTT (terminal 1) e simulador ou Wokwi (terminal 2)
cd 02-iot/receptor && pip install -r requirements.txt && python receptor_mqtt.py
python simulador_esp32.py

# 2. Robô RPA: lê câmera + sensor e gera as ordens de serviço
cd 06-rpa && pip install -r requirements.txt && python robo_cidade_em_ordem.py

# 3. Assistente generativo (opcional: chave Gemini no .env)
cd 05-generative-ai && pip install -r requirements.txt && python app.py

# 4. Front-end (crie 01-front-end/.env com VITE_RAG_URL=http://localhost:8000/perguntar)
cd 01-front-end && npm install && npm run dev
```
No front-end, entre como **Gestor**, vá em **Importar detecções** e envie `06-rpa/saida/ordens_servico.json`.

## ODS
**11** Cidades e comunidades sustentáveis (meta 11.2) · **9** Indústria, inovação e infraestrutura (meta 9.1) ·
**10** Redução das desigualdades · **13** Ação climática (prioridade maior com chuva prevista)

## Links
- Vídeo de integração (Governança): ⬜
- Vídeo de Generative AI: https://www.youtube.com/watch?v=jW51bMjhIdI
- Vídeo de Visão Computacional: https://youtu.be/sp4HV_C52s8
- Repositório: https://github.com/joaop-n12/cidade-em-ordem
