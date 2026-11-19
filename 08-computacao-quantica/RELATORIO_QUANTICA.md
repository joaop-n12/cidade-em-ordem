# Computação quântica no Cidade em Ordem: quando ela faz sentido

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
- São Paulo recebeu **113,1 mil pedidos de tapa-buraco em 2025** (cerca de 310 por dia) e 177,3 mil em 2023 [1].
- Com detecção automática, o volume tende a **aumentar** no início, porque problemas que ninguém reclamava passam a
  aparecer.
- A cidade tem 32 subprefeituras [2], cada uma com várias equipes, cada equipe com capacidade diária, horário, tipo de
  material (tapa-buraco a frio ou a quente) e base de saída.

### Por que é difícil
Distribuir as OS entre equipes e definir a rota de cada uma é um **problema de roteamento de veículos com janelas de
tempo e capacidade (VRPTW)**, que é **NP-difícil**: o número de soluções cresce de forma fatorial.
- Uma equipe com 15 paradas já tem 15! ≈ **1,3 trilhão** de ordens de visita possíveis.
- Num cenário hipotético com 30 equipes e 300 OS por dia (números usados apenas para dimensionar o problema), prazos diferentes (24 h para críticas, 72 h para altas) e a restrição de
  equidade entre bairros, o espaço de busca é astronômico.
- E ele **muda durante o dia**: começa a chover (buraco cheio d'água vira prioridade), uma via é interditada, uma
  equipe termina antes. O ideal seria **reotimizar a cada hora**.

### Onde a IA clássica sofre
| Situação | Comportamento clássico |
|---|---|
| 1 subprefeitura, ~20 OS | Solvers clássicos (OR-Tools, busca local) encontram solução ótima ou quase ótima em segundos. **Não há gargalo.** |
| Cidade inteira, reotimização a cada hora com várias restrições | Heurísticas ainda funcionam, mas sem garantia de qualidade. O tempo de cálculo cresce e na prática se aceita a "primeira solução razoável" |
| Restrição de equidade (nenhum bairro esperar muito mais que outro) | Ela aumenta muito o espaço de busca. A heurística tende a favorecer áreas centrais e densas, onde as rotas são mais curtas |

**Exemplo de equidade:** imagine duas ocorrências de mesma gravidade, uma no centro e outra num bairro periférico a
40 minutos da base da equipe. Um otimizador que só minimiza o deslocamento vai sempre deixar a da periferia para
depois. Um bairro periférico não deve esperar mais por reparos só porque fica longe das equipes. Por isso, a
otimização precisa considerar **a gravidade do problema e o tempo de espera acumulado por região**, evitando que os
recursos se concentrem nas áreas centrais.

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

**Escopo da formulação:** esse QUBO representa principalmente a **atribuição das OS às equipes**. O problema
completo de roteamento (ordem das visitas, janelas de tempo e deslocamento entre pontos) exige variáveis e
restrições adicionais, por exemplo x(o,e,k) = 1 se a OS *o* é a *k*-ésima parada da equipe *e*. Isso aumenta muito o
número de qubits necessários [6][7]. Por isso, a proposta realista é **híbrida**: o quântico resolve a atribuição, e
um algoritmo clássico define a sequência de visitas de cada equipe.

A computação quântica usa fenômenos como **superposição** e **interferência** para manipular as amplitudes dos
estados quânticos. Em algoritmos como o QAOA [4], essas propriedades são exploradas para buscar **soluções
aproximadas** de problemas combinatórios. Isso **não** significa testar todas as soluções ao mesmo tempo e encontrar
automaticamente a melhor: a qualidade do resultado depende da formulação do problema, da configuração do algoritmo
(número de camadas e parâmetros) e das limitações do hardware, como o ruído e a quantidade de qubits.

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
| **3. Uso seletivo** | 2030–2033 (se a fase 2 mostrar vantagem) | Planeja o dia e trata os casos simples | Quântico usado **só** na reotimização da cidade inteira em dias críticos (chuvas fortes, quando centenas de buracos aparecem de uma vez), se e quando houver hardware com **correção de erros** (a IBM anunciou em 2025 o sistema Starling, previsto para 2029, com 200 qubits lógicos [5]. É uma meta do fabricante, não uma garantia) | Em dias de chuva forte, as equipes chegam antes aos buracos mais perigosos, e a equidade entre bairros é garantida pela otimização |
| **Critério de parada** | contínuo | — | Se o quântico **não** superar o clássico em qualidade ou custo, o projeto continua 100% clássico | Dinheiro público não é gasto em tecnologia sem retorno |

**Por que esse cronograma:** os computadores quânticos atuais (era NISQ) têm poucos qubits e muito ruído. Para
problemas de roteamento reais, ainda **não há evidência de vantagem prática** sobre bons algoritmos clássicos.
Prometer ganho em 2026 seria desonesto. O valor imediato é **preparar o problema** (formulação QUBO, dados,
benchmark) para quando o hardware amadurecer.

## 5. Ética, LGPD e ODS ao longo do roadmap

| Fase | Ética | LGPD | ODS |
|---|---|---|---|
| **Hoje** | Prioridade explicável (cada ponto do escore tem motivo). Casos duvidosos vão para revisão humana. A câmera não guarda rostos nem placas | Coordenadas podem ser **dados pessoais** quando permitem localizar ou identificar uma pessoa (por exemplo, a OS aberta por um morador na frente de casa). Por isso, o sistema prioriza dados **operacionais e geográficos agregados** e não associa coordenadas a cidadãos identificáveis. Se houver tratamento de dados pessoais, valem os princípios de **finalidade, necessidade, segurança e transparência** (art. 6º). O cidadão tem login local e direito de exclusão (art. 18) | **11** (vias seguras, meta 11.2), **9** (infraestrutura, meta 9.1) |
| **Experimentação** | Risco de **viés de eficiência**: um otimizador que só minimiza distância favorece bairros centrais. Por isso a **restrição de equidade** entra na formulação desde o início | Nuvens quânticas ficam em geral no exterior, o que configura **transferência internacional** (LGPD, art. 33 [8]). Solução: enviar **somente** o problema matemático (matriz QUBO com IDs e distâncias), nunca endereços ou dados de cidadãos | **10** (redução das desigualdades): todos os bairros com tempo de espera parecido |
| **Uso seletivo** | Decisão final continua humana (gestor aprova o plano). Transparência: publicar os critérios de prioridade | **Criptografia pós-quântica:** dados guardados hoje podem ser decifrados no futuro por computadores quânticos ("colete agora, decifre depois"). Migrar as comunicações (MQTT com TLS, API) para algoritmos padronizados pelo NIST em 2024 (**ML-KEM** para troca de chaves e **ML-DSA** para assinatura) [3] | **13** (ação climática): resposta rápida em eventos de chuva extrema, mais frequentes com a mudança do clima |

## 6. Conclusão
O gargalo do Cidade em Ordem em escala municipal é **otimizar a distribuição e a rota das equipes de reparo** com
prazos, chuva e equidade entre bairros: um problema combinatório NP-difícil. A **otimização quântica** (QUBO,
QAOA, annealing) é a capacidade adequada a ele. Mas o raciocínio honesto é que **hoje** a IA clássica resolve
bem o problema na escala de subprefeitura, e o quântico só fará sentido **depois** de demonstrar vantagem em testes
comparativos, provavelmente no início da próxima década. Até lá, a contribuição concreta da área é a
**criptografia pós-quântica** para proteger os dados da cidade e a **formulação do problema com a equidade como
restrição**. O cidadão ganha com isso independentemente do hardware.

## Dados reais e hipóteses
| Informação | Tipo |
|---|---|
| 113,1 mil pedidos de tapa-buraco em 2025 e 177,3 mil em 2023 | **Dado real** [1] |
| 32 subprefeituras em São Paulo | **Dado real** [2] |
| Padrões ML-KEM e ML-DSA publicados pelo NIST em agosto de 2024 | **Dado real** [3] |
| Meta da IBM de um computador tolerante a falhas em 2029 | **Previsão do fabricante** [5] |
| 30 equipes, 300 OS por dia, 15 paradas por equipe | **Hipótese** para dimensionar o problema |
| Prazos de 24 h (crítica) e 72 h (alta) | **Regra do protótipo** Cidade em Ordem |
| Períodos do roadmap (2027–2029 e 2030–2033) | **Estimativa do grupo**, condicionada aos testes da fase 2 |

## Referências
[1] BNEWS SÃO PAULO. *Mesmo após recapeamento, SP registra quase 52 mil pedidos de tapa-buraco*. 2025. Dados da
Secretaria Municipal das Subprefeituras. Disponível em:
https://www.bnewssaopaulo.com.br/noticias/politica/mesmo-apos-recapeamento-sp-registra-quase-52-mil-pedidos-de-tapa-buraco.html

[2] PREFEITURA DE SÃO PAULO. *Secretaria Municipal das Subprefeituras*. Disponível em:
https://prefeitura.sp.gov.br/web/subprefeituras

[3] NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY. *FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism
Standard* e *FIPS 204: Module-Lattice-Based Digital Signature Standard*. Gaithersburg: NIST, ago. 2024. Disponível em:
https://csrc.nist.gov/pubs/fips/203/final e https://csrc.nist.gov/pubs/fips/204/final

[4] FARHI, E.; GOLDSTONE, J.; GUTMANN, S. *A Quantum Approximate Optimization Algorithm*. arXiv:1411.4028, 2014.
Disponível em: https://arxiv.org/abs/1411.4028

[5] CONSTELLATION RESEARCH. *IBM outlines quantum computing roadmap through 2029, fault-tolerant systems*. Jun. 2025.
Cobertura do anúncio da IBM sobre o sistema Starling. Disponível em:
https://www.constellationr.com/blog-news/insights/ibm-outlines-quantum-computing-roadmap-through-2029-fault-tolerant-systems

[6] LUCAS, A. *Ising formulations of many NP problems*. Frontiers in Physics, v. 2, art. 5, 2014.
DOI: https://doi.org/10.3389/fphy.2014.00005

[7] FELD, S. et al. *A Hybrid Solution Method for the Capacitated Vehicle Routing Problem Using a Quantum Annealer*.
Frontiers in ICT, v. 6, art. 13, 2019. DOI: https://doi.org/10.3389/fict.2019.00013

[8] BRASIL. *Lei nº 13.709, de 14 de agosto de 2018*. Lei Geral de Proteção de Dados Pessoais (LGPD), arts. 6º, 18 e 33.
Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
