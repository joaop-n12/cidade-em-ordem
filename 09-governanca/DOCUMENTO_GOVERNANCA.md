---
titulo: CIDADE EM ORDEM
subtitulo: Detecção automática de buracos para a zeladoria urbana de São Paulo
instituicao: FIAP - Faculdade de Informática e Administração Paulista
curso: Tecnologia em Inteligência Artificial
disciplina: Governança em IA e Business Analytics
integrantes: João Pedro de Souza Nunes - RM567318; Guilherme Nakamura - RM567460
local: São Paulo
ano: 2026
natureza: Relatório apresentado à disciplina de Governança em IA e Business Analytics como parte da Global Solution 2026.2 (CitizenTech).
---

# 1 INTRODUÇÃO

Este relatório descreve a integração dos módulos desenvolvidos na Global Solution 2026.2, cujo tema é CitizenTech: tecnologia criada a partir de necessidades reais dos cidadãos.

O problema escolhido foi a manutenção de vias e calçadas em São Paulo. Em 2025 a Prefeitura recebeu 113,1 mil pedidos de tapa-buraco, cerca de 300 por dia, e a própria Secretaria das Subprefeituras reconhece que um mesmo buraco pode gerar vários chamados. Os canais que existem hoje, como o SP156 e a Zeladoria do aplicativo Poupatempo, dependem de o cidadão perceber o problema, parar e registrar a reclamação. Bairros onde as pessoas reclamam menos acabam com menos atendimento.

A proposta do grupo, chamada Cidade em Ordem, parte de um fato simples: os caminhões de coleta de lixo já passam por todas as ruas da cidade várias vezes por semana. Instalando neles uma câmera e um sensor de baixo custo, a prefeitura passa a encontrar os buracos sem esperar reclamações. Um robô de software junta as detecções repetidas, calcula a prioridade e abre a ordem de serviço. O cidadão acompanha pelo aplicativo e tira dúvidas com um assistente que responde com base nas leis.

O objetivo deste documento é mostrar como cada disciplina contribuiu para essa solução, como os módulos se comunicam e, na parte de Governança, quais materiais foram ou não integrados e quais regras de governança de IA foram aplicadas.

A solução se relaciona com os Objetivos de Desenvolvimento Sustentável 11 (cidades seguras e inclusivas, meta 11.2), 9 (infraestrutura de qualidade, meta 9.1), 10 (redução das desigualdades) e 13 (ação climática, pois a prioridade sobe quando há chuva prevista).

# 2 DESENVOLVIMENTO

## 2.1 Visão geral da arquitetura

A solução tem quatro camadas: coleta de dados no caminhão (câmera e sensor), processamento na central (receptor MQTT e robô RPA), interface com o cidadão e o gestor (aplicativo web e assistente) e estudos de evolução (memristor e computação quântica). O Quadro 1 resume o fluxo de dados entre os módulos.

[QUADRO 1 - Fluxo de dados entre os módulos]
| Origem | Dado | Destino | Formato |
|---|---|---|---|
| Câmera (Visão Computacional) | Buracos detectados com confiança e posição | Robô RPA | deteccoes_visao.json |
| ESP32 (IoT) | Impacto (g), profundidade (cm) e posição | Receptor MQTT e depois robô RPA | MQTT e deteccoes_iot.json |
| Leis e cartilhas (NLP) | Corpus limpo e anonimizado | Assistente (Generative AI) | corpus_texto.jsonl e corpus_qa.jsonl |
| Robô RPA | Ordens de serviço priorizadas | Front-end e assistente | ordens_servico.json e .xlsx |
| Front-end | Pergunta do cidadão | Assistente | POST /perguntar |

[FIGURA 1 - Arquitetura da solução (inserir print do diagrama do README do repositório)]

## 2.2 Front End & Mobile Development

O aplicativo foi feito em React com Vite. Ele tem login local, com senha guardada como hash SHA-256 com sal, e dois perfis: cidadão e gestor da prefeitura. As telas são painel com mapa, consulta de ocorrências com filtros, registro de ocorrência, detalhe com histórico, assistente e importação das detecções automáticas. Os dados ficam no localStorage do navegador.

O processamento inteligente está no módulo de classificação. Ele recebe a confiança da câmera, o impacto e a profundidade do sensor, o tipo de via, a previsão de chuva, as detecções anteriores e a descrição em texto, e devolve um escore de 0 a 100, a prioridade, o prazo, a secretaria responsável e a ação a tomar. Cada ponto do escore aparece na tela com o motivo, para que o gestor entenda a decisão. Quando a evidência é fraca, a ação gerada é uma vistoria, e não a ordem de serviço.

Foram tratados acessibilidade (HTML semântico, rótulos em todos os campos, navegação por teclado, link para pular ao conteúdo e botão para aumentar a fonte) e proteção de dados (só nome e e-mail, consentimento no cadastro e botão para apagar a conta).

## 2.3 Physical Computing, Embedded AI, Robotics & Cognitive IoT

O módulo IoT foi simulado no Wokwi com um ESP32, um acelerômetro MPU6050 e um sensor ultrassônico HC-SR04 apontado para o asfalto. O acelerômetro mede o impacto quando o caminhão passa por um buraco, e o ultrassônico estima a profundidade pela diferença em relação à distância calibrada.

O ESP32 publica telemetria a cada 3 segundos e um evento imediato quando os sensores indicam buraco. A comunicação usa MQTT com quatro tópicos: telemetria, evento, status (com Last Will) e comando. Um receptor em Python valida as mensagens, grava tudo em SQLite e junta eventos a menos de 25 metros como o mesmo buraco. Quando o buraco é confirmado, o receptor envia um comando de volta e o LED vermelho do ESP32 acende.

Os testes com o broker público mostraram seis situações: rua em bom estado, buraco moderado, segunda passagem no mesmo buraco (confirmação), buraco severo, mensagem corrompida e leitura fora da faixa. As duas últimas foram rejeitadas sem parar o receptor.

[QUADRO 2 - Testes do módulo IoT]
| Entrada | Resultado |
|---|---|
| 1,01 g e 0,1 cm | Gravado, sem alerta |
| 2,2 g e 6 cm | Buraco registrado como suspeito |
| 2,4 g e 6,5 cm no mesmo ponto | Buraco confirmado e comando enviado ao ESP32 |
| 3,4 g e 13 cm | Confirmado na primeira passagem |
| Texto inválido | Descartado com registro no log |
| 99 g | Rejeitado pela validação |

## 2.4 Visão Computacional

O nicho escolhido foi infraestrutura e pavimentação, com a detecção de buracos por caixas delimitadoras. Usamos uma base pública com 819 imagens anotadas e treinamos o YOLO11n com transferência de aprendizado a partir dos pesos do COCO.

Ao analisar a base, vimos que as 819 imagens vinham de apenas 269 fotos originais, porque a ferramenta de anotação gera variações de cada foto. Se a divisão fosse feita por imagem, variações da mesma foto ficariam no treino e no teste, e as métricas sairiam infladas. Por isso agrupamos por foto original antes de dividir em 70% treino, 15% validação e 15% teste.

[QUADRO 3 - Resultados no conjunto de teste]
| Métrica | Valor |
|---|---|
| Precisão | 0,611 |
| Recall | 0,456 |
| F1 | 0,523 |
| mAP@0,5 | 0,442 |
| mAP@0,5:0,95 | 0,221 |
| Limiar de confiança escolhido | 0,30 |
| Latência média por imagem (CPU, 640×640) | 32,7 ms (30 FPS) |

O resultado é suficiente para triagem com confirmação, mas não para decidir sozinho. Os buracos do teste são menores que os da validação (área mediana de 1,9% contra 4,9% da imagem), e o modelo perde principalmente buracos pequenos e distantes e buracos no meio de asfalto trincado. No teste de robustez, o recall caiu 6% com desfoque, 11% com sombra, 28% com luz estourada e 56% com obstrução parcial. A obstrução pesa menos na prática, porque o caminhão passa pela mesma rua várias vezes por semana.

Processamos também uma sequência de imagens como se fosse o vídeo do trajeto do caminhão. Cada detecção recebe a posição GPS simulada e vai para o robô RPA.

## 2.5 Processamento de Linguagem Natural

Construímos uma ferramenta que transforma documentos públicos em corpus para o ajuste fino de um modelo de linguagem pequeno, que poderia rodar nos servidores da prefeitura sem enviar dados para a nuvem. Foram usados cinco documentos oficiais: a cartilha de calçadas da Prefeitura de São Paulo (PDF), o Código de Trânsito Brasileiro e a Lei Brasileira de Inclusão (HTML), a Lei Municipal 15.442/2011 sobre calçadas (DOCX) e a Política Nacional de Resíduos Sólidos (TXT).

A limpeza corrigiu problemas reais dos arquivos, como letras trocadas pela fonte do PDF, cabeçalhos com número de página, anotações de alteração das leis e versões antigas de artigos. A anonimização mascara CPF, e-mail, telefone e nomes. Na primeira versão, o reconhecimento de nomes marcou termos como "Distrito Federal" como pessoa. Criamos um filtro para corrigir isso.

Foram gerados 287 trechos de texto, 183 pares de pergunta e resposta e 46 diálogos, todos acima dos mínimos pedidos. As respostas foram extraídas das definições das leis ou escritas pelo grupo, e uma verificação automática confirmou que todos os números citados existem nos documentos.

## 2.6 Generative AI and Advanced Nets

O assistente do cidadão usa RAG (geração aumentada por recuperação) com LangChain. A base de conhecimento é o corpus produzido em NLP. A busca combina vetores (embeddings multilíngues que rodam no próprio computador) e palavras-chave (BM25). Um roteador decide se a pergunta é sobre uma lei, quando usa o RAG, ou sobre o andamento de um buraco numa rua, quando consulta as ordens de serviço geradas pelo robô RPA.

Antes de qualquer chamada ao modelo, o texto passa por proteções: dados pessoais são mascarados, mensagens de emergência recebem os telefones do SAMU, Bombeiros e Defesa Civil, e perguntas fora do tema são recusadas sem chamar o modelo. Depois da resposta, o sistema confere se os números citados aparecem nos trechos recuperados.

[QUADRO 4 - Avaliação do assistente com 24 perguntas]
| Métrica | Só vetorial | Busca híbrida |
|---|---|---|
| Roteamento correto | 24/24 | 24/24 |
| Fonte correta entre os 4 trechos | 16/18 | 18/18 |
| Resposta com as palavras-chave esperadas | 20/24 | 23/24 |
| Números sem suporte no contexto | 0/18 | 0/18 |

## 2.7 AI for Robotic Process Automation

O robô roda de ponta a ponta a partir de um único script. Ele lê as detecções da câmera e do sensor, rejeita registros inválidos, agrupa as detecções do mesmo buraco com o algoritmo DBSCAN (raio de 25 metros), busca o endereço e o tipo de via no OpenStreetMap e a previsão de chuva no Open-Meteo, calcula a prioridade e decide entre abrir uma ordem de serviço ou mandar o caso para revisão humana. As saídas são uma planilha Excel, um relatório HTML, um arquivo para o front-end e um log.

O robô trata falhas previsíveis: arquivo ausente, JSON corrompido, API fora do ar (com até três tentativas e espera crescente) e planilha aberta. Ele também é idempotente: uma ocorrência que já gerou ordem de serviço não gera outra na execução seguinte.

Num lote de teste rotulado com 10 buracos e 4 falsos alarmes, o robô acertou as 14 decisões e rejeitou os 3 registros inválidos. Como o lote é sintético, esse resultado mostra que a lógica funciona como foi projetada, e não a precisão em campo.

## 2.8 Cluster Computing, Computação Neuromórfica e Supercomputadores

Investigamos, por simulação no Falstad, se um memristor poderia guardar o registro de impactos repetidos no mesmo trecho de rua. Um pulso positivo representa um impacto e reduz a resistência. Sem tensão, a resistência deve permanecer. Um pulso negativo representaria o reparo e devolve a resistência ao valor alto.

⬜ Resumir aqui o que foi observado na simulação (valores de resistência nas duas condições de estímulo e se o estado se manteve após retirar a tensão).

A ideia para o projeto é ter um contador de impactos que não perde o registro se o equipamento do caminhão desligar. Isso continua no nível de estudo: não foi construído hardware.

## 2.9 Computação Quântica & IA

O gargalo identificado aparece quando a solução atende a cidade inteira: distribuir centenas de ordens de serviço por dia entre dezenas de equipes, com prazos, chuva e equilíbrio entre bairros, é um problema de roteamento de veículos, que é NP-difícil. A capacidade quântica que se aplica é a otimização, escrevendo o problema no formato QUBO para algoritmos como o QAOA.

O roadmap é conservador. Hoje a solução usa apenas métodos clássicos, que resolvem bem o problema por subprefeitura. Entre 2027 e 2029 seriam feitos testes comparativos com solvers híbridos em problemas pequenos. O uso real só aconteceria depois de 2030 e apenas se os testes mostrarem vantagem. A contribuição imediata da área é a criptografia pós-quântica (padrões ML-KEM e ML-DSA do NIST) para proteger os dados da cidade.

## 2.10 Governança em IA e Business Analytics

### 2.10.1 Materiais integrados e não integrados

[QUADRO 5 - Situação de integração de cada material]
| Disciplina | Material | Integrado? | Como |
|---|---|---|---|
| Front End | Aplicativo React | Sim | Importa as ordens de serviço do RPA e chama o assistente pela API |
| IoT | ESP32, MQTT e receptor | Sim | O receptor gera deteccoes_iot.json, lido pelo robô RPA |
| Visão Computacional | Modelo YOLO11n | Sim | O notebook gera deteccoes_visao.json, lido pelo robô RPA |
| NLP | Corpus JSONL | Sim | É a base de conhecimento do assistente |
| Generative AI | Assistente RAG | Sim | Responde no aplicativo e consulta as ordens do RPA |
| RPA | Robô de triagem | Sim | Junta câmera e sensor e alimenta o aplicativo e o assistente |
| Cluster | Simulação de memristor | Não (estudo) | Proposta de uso no ESP32, sem implementação |
| Computação Quântica | Roadmap | Não (estudo) | Plano de evolução, sem implementação |
| Todas | Integração em tempo real | Parcial | A troca entre módulos é feita por arquivos. O ideal seria uma fila de mensagens ou uma API única |

### 2.10.2 Princípios de governança de IA aplicados

[QUADRO 6 - Princípios e como foram aplicados]
| Princípio | Aplicação no projeto |
|---|---|
| Transparência e explicabilidade | Escore de prioridade com o motivo de cada ponto. O assistente mostra a fonte da resposta |
| Supervisão humana | Casos com evidência fraca vão para revisão humana. A IA não decide sozinha sobre indenização nem sobre a gravidade real do buraco |
| Privacidade (LGPD) | Minimização dos dados, anonimização do corpus, mascaramento antes do LLM, direito de apagar a conta. Rostos e placas não são guardados |
| Equidade | O caminhão passa em todas as ruas, então a detecção não depende de quem reclama. O roadmap quântico prevê uma restrição de equilíbrio entre bairros |
| Segurança e robustez | Validação de entradas, tratamento de falhas, chaves fora do código, teste de robustez da visão a sombra e pouca luz |
| Responsabilização | Log de cada execução do robô e histórico de cada ocorrência no aplicativo |

### 2.10.3 Riscos e controles

[QUADRO 7 - Matriz de riscos]
| Risco | Probabilidade | Impacto | Controle |
|---|---|---|---|
| Falso positivo da câmera (sombra, mancha) | Média | Baixo | Confirmação por sensor ou por mais de um quadro. Revisão humana |
| Buraco não detectado | Média | Alto | Câmera e sensor são independentes. O cidadão ainda pode registrar manualmente |
| Resposta errada do assistente | Baixa | Médio | RAG, citação da fonte, verificação de números e recusa fora do tema |
| Vazamento de dados pessoais | Baixa | Alto | Anonimização e mascaramento. Nenhum dado pessoal no robô |
| Queda de API externa | Média | Baixo | Retentativas e caminho seguro sem o dado externo |
| Modelo desatualizado (piso, clima, câmera nova) | Média | Médio | Monitorar a precisão com as vistorias e retreinar periodicamente |

### 2.10.4 Indicadores para Business Analytics

A prefeitura poderia acompanhar a solução com os seguintes indicadores:

- tempo médio entre a detecção e o reparo, por prioridade e por subprefeitura;
- percentual de buracos encontrados sem reclamação do cidadão;
- taxa de falsos positivos confirmada nas vistorias, para medir a precisão real da câmera;
- cobertura das rotas: percentual de ruas percorridas por semana;
- diferença do tempo de atendimento entre bairros, para acompanhar a equidade;
- chamados duplicados evitados pelo agrupamento do robô.

# 3 CONCLUSÃO

⬜ ESTA SEÇÃO DEVE SER ESCRITA PELO GRUPO, COM AS PRÓPRIAS PALAVRAS (o professor avisou que, se for feita com IA, a nota do documento cai pela metade). Sugestão de pontos para comentar: o que vocês aprenderam integrando as disciplinas, o que funcionou melhor, o que ficou faltando (por exemplo, a integração em tempo real e o hardware físico), se a ideia seria viável numa prefeitura de verdade e o que fariam em seguida.

# 4 LINKS

- Vídeo de demonstração (YouTube, não listado): ⬜
- Repositório GitHub: https://github.com/joaop-n12/cidade-em-ordem

# REFERÊNCIAS

BRASIL. Lei nº 9.503, de 23 de setembro de 1997. Institui o Código de Trânsito Brasileiro. Brasília, DF: Presidência da República, 1997.

BRASIL. Lei nº 12.305, de 2 de agosto de 2010. Institui a Política Nacional de Resíduos Sólidos. Brasília, DF: Presidência da República, 2010.

BRASIL. Lei nº 13.146, de 6 de julho de 2015. Institui a Lei Brasileira de Inclusão da Pessoa com Deficiência. Brasília, DF: Presidência da República, 2015.

BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais (LGPD). Brasília, DF: Presidência da República, 2018.

BNEWS SÃO PAULO. Mesmo após recapeamento, SP registra quase 52 mil pedidos de tapa-buraco. 2025. Disponível em: https://www.bnewssaopaulo.com.br/noticias/politica/mesmo-apos-recapeamento-sp-registra-quase-52-mil-pedidos-de-tapa-buraco.html.

FARHI, E.; GOLDSTONE, J.; GUTMANN, S. A Quantum Approximate Optimization Algorithm. arXiv:1411.4028, 2014.

NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY. FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard. Gaithersburg: NIST, 2024.

SÃO PAULO (Município). Lei nº 15.442, de 9 de setembro de 2011. Dispõe sobre a limpeza de imóveis, o fechamento de terrenos não edificados e a construção e manutenção de passeios. São Paulo, 2011.

SÃO PAULO (Município). Secretaria Municipal da Pessoa com Deficiência. Calçadas e vias exclusivas de pedestres. São Paulo: SMPED/CPA, 2024.

ULTRALYTICS. YOLO11. Documentação. Disponível em: https://docs.ultralytics.com.
