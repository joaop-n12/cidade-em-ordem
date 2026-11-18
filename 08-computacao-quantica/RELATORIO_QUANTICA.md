# Computação quântica no Cidade em Ordem: quando (e se) ela faz sentido

**Computação Quântica & IA** · Global Solution 2026.2 · CitizenTech

| Integrante | RM |
|---|---|
| João Pedro de Souza Nunes | RM567318 |
| Guilherme Nakamura | RM567460 |

## 1. A solução hoje (IA clássica)
O Cidade em Ordem detecta buracos sem depender de reclamação: a câmera do caminhão de coleta (YOLO11n) e o
sensor de impacto (ESP32 com MQTT) geram detecções. Um robô RPA junta as repetidas (DBSCAN), calcula a
prioridade e abre ordens de serviço (OS). O cidadão acompanha pelo app e tira dúvidas com um assistente RAG.

Para um bairro, tudo funciona bem em computadores comuns. A pergunta desta disciplina é: **o que acontece quando
a solução atende a cidade inteira?**

## 2. O gargalo real: decidir *quem conserta o quê, em que ordem*

### Escala
- São Paulo recebeu **113,1 mil pedidos de tapa-buraco em 2025** (cerca de 310 por dia) e 177,3 mil em 2023.
- Com detecção automática, o volume tende a **aumentar** no início, porque problemas que ninguém reclamava passam a
  aparecer.
- A cidade tem 32 subprefeituras, cada uma com várias equipes, cada equipe com capacidade diária, horário, tipo de
  material (tapa-buraco a frio ou a quente) e base de saída.

### Por que é difícil
Distribuir as OS entre equipes e definir a rota de cada uma é um **problema de roteamento de veículos com janelas de
tempo e capacidade (VRPTW)**, que é **NP-difícil**: o número de soluções cresce de forma fatorial.
- Uma equipe com 15 paradas já tem 15! ≈ **1,3 trilhão** de ordens de visita possíveis.
- Com 30 equipes, 300 OS por dia, prazos diferentes (24 h para críticas, 72 h para altas) e a restrição de
  equidade entre bairros, o espaço de busca é astronômico.
- E ele **muda durante o dia**: começa a chover (buraco cheio d'água vira prioridade), uma via é interditada, uma
  equipe termina antes. O ideal seria **reotimizar a cada hora**.

### Onde a IA clássica sofre
| Situação | Comportamento clássico |
|---|---|
| 1 subprefeitura, ~20 OS | Solvers clássicos (OR-Tools, busca local) encontram solução ótima ou quase ótima em segundos. **Não há gargalo.** |
| Cidade inteira, reotimização a cada hora com várias restrições | Heurísticas ainda funcionam, mas sem garantia de qualidade. O tempo de cálculo cresce e na prática se aceita a "primeira solução razoável" |
| Restrição de equidade (nenhum bairro esperar muito mais que outro) | Ela aumenta muito o espaço de busca. A heurística tende a favorecer áreas centrais e densas, onde as rotas são mais curtas |

**Conclusão honesta:** o gargalo é de **qualidade da otimização em grande escala e em tempo quase real**, e não de
capacidade de processamento para um bairro. É exatamente o tipo de problema que a computação quântica *promete*
atacar, mas que ainda **não resolve melhor que o clássico** hoje.

## 3. Capacidade quântica escolhida: **otimização**

### Como o problema vira linguagem quântica
O subproblema "quais OS cada equipe atende hoje" pode ser escrito como um **QUBO** (otimização binária quadrática
sem restrições), que é o formato aceito por *quantum annealers* e pelo algoritmo **QAOA** (Quantum Approximate
Optimization Algorithm):

- variável binária x(o,e) = 1 se a OS *o* vai para a equipe *e*;
- **função objetivo:** maximizar Σ prioridade(o)·x(o,e) e minimizar a distância entre OS da mesma equipe;
- **penalidades** (termos quadráticos): cada OS em no máximo uma equipe; capacidade diária de cada equipe; OS
  críticas (24 h) obrigatoriamente atendidas; **diferença máxima de espera entre bairros** (equidade).

Um computador quântico explora muitas combinações em **superposição**, e a **interferência** reforça as boas
soluções. Em teoria, isso permite encontrar soluções melhores em problemas combinatórios grandes.

### Por que otimização, e não as outras capacidades
| Capacidade | Faz sentido aqui? |
|---|---|
| **Otimização (QAOA / annealing)** | **Sim.** O gargalo é combinatório e cresce com a cidade |
| Simulação quântica | Não. Não simulamos moléculas ou materiais (talvez no futuro, para novos asfaltos mais duráveis, fora do escopo) |
| Busca em grandes bases (Grover) | Não. A base de OS é pequena para um banco de dados comum. Ganho quadrático irrelevante |
| Criptografia pós-quântica (PQC) | **Complementar.** Não acelera nada, mas protege os dados da cidade de futuros computadores quânticos (ver seção 5) |

## 4. Roadmap realista

| Fase | Período | IA clássica entrega | Quântico agrega | Benefício para o cidadão |
|---|---|---|---|---|
| **1. Hoje** | 2026 | Detecção (YOLO + sensor), deduplicação (DBSCAN), prioridade explicável, OS automática. Roteirização por heurística clássica (OR-Tools) por subprefeitura | **Nada em produção.** Estudo e formulação do problema como QUBO. Dados de OS guardados de forma estruturada para comparações futuras | Buraco encontrado antes da reclamação, sem chamados duplicados |
| **2. Experimentação híbrida** | 2027–2029 | Continua sendo o motor oficial | Testes com **solvers híbridos clássico-quânticos** em nuvem e QAOA em simuladores e hardware atual (dezenas a centenas de qubits com ruído), em **subproblemas pequenos** (1 subprefeitura, 20–50 OS). **Comparação sempre contra o clássico**: qualidade da rota, tempo de cálculo e custo | Nenhum benefício direto ainda. É uma fase de aprendizado, sem risco para o serviço |
| **3. Uso seletivo** | 2030–2033 (se a fase 2 mostrar vantagem) | Planeja o dia e trata os casos simples | Quântico usado **só** na reotimização da cidade inteira em dias críticos (chuvas fortes, quando centenas de buracos aparecem de uma vez), se e quando houver hardware com **correção de erros** (fabricantes como a IBM anunciam sistemas tolerantes a falhas para o fim desta década) | Em dias de chuva forte, as equipes chegam antes aos buracos mais perigosos, e a equidade entre bairros é garantida pela otimização |
| **Critério de parada** | contínuo | — | Se o quântico **não** superar o clássico em qualidade ou custo, o projeto continua 100% clássico | Dinheiro público não é gasto em tecnologia sem retorno |

**Por que esse cronograma:** os computadores quânticos atuais (era NISQ) têm poucos qubits e muito ruído. Para
problemas de roteamento reais, ainda **não há evidência de vantagem prática** sobre bons algoritmos clássicos.
Prometer ganho em 2026 seria desonesto. O valor imediato é **preparar o problema** (formulação QUBO, dados,
benchmark) para quando o hardware amadurecer.

## 5. Ética, LGPD e ODS ao longo do roadmap

| Fase | Ética | LGPD | ODS |
|---|---|---|---|
| **Hoje** | Prioridade explicável (cada ponto do escore tem motivo). Casos duvidosos vão para revisão humana. A câmera não guarda rostos nem placas | O sistema processa coordenadas e leituras de sensor, não dados pessoais. Cidadão com login local e direito de exclusão (art. 18). Minimização (art. 6º, III) | **11** (vias seguras, meta 11.2), **9** (infraestrutura, meta 9.1) |
| **Experimentação** | Risco de **viés de eficiência**: um otimizador que só minimiza distância favorece bairros centrais. Por isso a **restrição de equidade** entra na formulação desde o início | Nuvens quânticas ficam em geral no exterior, o que configura **transferência internacional** (LGPD art. 33). Solução: enviar **somente** o problema matemático (matriz QUBO com IDs e distâncias), nunca endereços ou dados de cidadãos | **10** (redução das desigualdades): todos os bairros com tempo de espera parecido |
| **Uso seletivo** | Decisão final continua humana (gestor aprova o plano). Transparência: publicar os critérios de prioridade | **Criptografia pós-quântica:** dados guardados hoje podem ser decifrados no futuro por computadores quânticos ("colete agora, decifre depois"). Migrar as comunicações (MQTT com TLS, API) para algoritmos padronizados pelo NIST em 2024 (**ML-KEM** para troca de chaves e **ML-DSA** para assinatura) | **13** (ação climática): resposta rápida em eventos de chuva extrema, mais frequentes com a mudança do clima |

## 6. Conclusão
O gargalo do Cidade em Ordem em escala municipal é **otimizar a distribuição e a rota das equipes de reparo** com
prazos, chuva e equidade entre bairros: um problema combinatório NP-difícil. A **otimização quântica** (QUBO,
QAOA, annealing) é a capacidade adequada a ele. Mas o raciocínio honesto é que **hoje** a IA clássica resolve
bem o problema na escala de subprefeitura, e o quântico só fará sentido **depois** de demonstrar vantagem em testes
comparativos, provavelmente no início da próxima década. Até lá, a contribuição concreta da área é a
**criptografia pós-quântica** para proteger os dados da cidade e a **formulação do problema com a equidade como
restrição**. O cidadão ganha com isso independentemente do hardware.

## Fontes
- Pedidos de tapa-buraco em SP: Secretaria Municipal das Subprefeituras, via BNews SP (2025).
- NIST, FIPS 203 (ML-KEM) e FIPS 204 (ML-DSA), padrões de criptografia pós-quântica publicados em agosto de 2024.
- Farhi, Goldstone e Gutmann, *A Quantum Approximate Optimization Algorithm*, arXiv:1411.4028 (2014).
- Lucas, *Ising formulations of many NP problems*, Frontiers in Physics (2014): formulações QUBO para problemas de roteamento.
- Lei 13.709/2018 (LGPD), arts. 6º, 18 e 33.
