# Cidade em Ordem: Robô RPA + IA

**AI for Robotic Process Automation** · Global Solution 2026.2 · CitizenTech

| Integrante | RM |
|---|---|
| João Pedro de Souza Nunes | RM567318 |
| Guilherme Nakamura | RM567460 |

## Problema
Em 2025 a Prefeitura de São Paulo recebeu **113,1 mil pedidos de tapa-buraco**, quase 300 por dia, e reconhece
que um mesmo buraco gera vários chamados (Secretaria das Subprefeituras, via BNews SP). O fluxo atual
depende de o cidadão reclamar, e alguém precisa ler, juntar repetições, localizar e priorizar cada pedido
manualmente.

**Público:** cidadãos que circulam pelas ruas (motoristas, motociclistas, ciclistas, pedestres) e a equipe da
subprefeitura que programa os reparos.

## O que o robô faz (de ponta a ponta, sem intervenção)
```
deteccoes_visao.json (câmera do caminhão) ─┐
                                           ├─> validação ─> agrupamento DBSCAN ─> APIs (endereço + chuva)
deteccoes_iot.json (sensor do caminhão) ───┘        │                                     │
                                              rejeitados (log)          escore de prioridade + regra de confirmação
                                                                                          │
                     ┌────────────────────────────────────────────┬───────────────────────┴──────────────┐
             ordens_servico.xlsx                         fila_revisao_humana.csv            ordens_servico.json
             (OS + aba de revisão)                       (evidência fraca)                  (importado no front-end)
                                     relatorio_execucao.html + execucao.log
```

## Quadro de temas da disciplina (4 temas com função real)

| Tema | Onde é usado no fluxo | O que resolve |
|---|---|---|
| **1. Automação de leitura e integração de arquivos** | `coletar()` lê os JSON gerados pela visão computacional e pelo IoT e padroniza num único modelo (`Deteccao`) | Junta duas fontes diferentes sem digitação manual. Cada arquivo ausente ou corrompido é tratado separadamente |
| **2. Integração com APIs web (com timeout, retry e cache)** | `Enriquecedor`: **Nominatim/OpenStreetMap** (endereço e tipo de via a partir da coordenada) e **Open-Meteo** (chuva prevista para 24 h) | Transforma coordenada em endereço que a equipe entende. O tipo de via (avenida ou rua local) e a chuva entram na prioridade. Timeout de 10 s, 3 tentativas com espera exponencial, cache local e respeito ao limite de 1 req/s do Nominatim |
| **3. IA aplicada ao processo** | `agrupar()`: **DBSCAN** com distância haversine (raio de 25 m) junta detecções do mesmo buraco. `priorizar()`: escore explicável que combina confiança da câmera (modelo YOLO da disciplina de Visão Computacional), impacto e profundidade do sensor, tipo de via, chuva e reincidência | Elimina chamados duplicados (o problema citado pela própria prefeitura) e decide a ordem de atendimento com justificativa por fator |
| **4. Geração automática de documentos e relatórios** | `salvar_excel()` (planilha com abas "Ordens de serviço" e "Revisão humana"), `salvar_relatorio()` (HTML da execução), CSV da fila de revisão e JSON para o front-end | Entrega o resultado no formato que a equipe usa (Excel) e um relatório de auditoria de cada execução |

**Por que esses temas:** o gargalo real é o trabalho manual de *juntar, localizar e priorizar* pedidos. Os
temas 1 e 3 juntam e deduplicam, o tema 2 localiza e contextualiza e o tema 4 entrega. O LLM não é usado
porque a decisão precisa ser **explicável e reprodutível**: um escore por fatores mostra exatamente por que
um buraco ficou na frente de outro.

## Resiliência e segurança

| Falha previsível | Caminho seguro |
|---|---|
| Arquivo de entrada ausente | Log de erro e segue com a outra fonte |
| JSON corrompido | Log de erro e a fonte é ignorada no lote |
| Registro inválido (coordenada fora do município, confiança > 1, campo faltando) | Rejeitado com o motivo no log e no relatório |
| API fora do ar ou lenta | Timeout de 10 s, 3 tentativas (1 s, 2 s, 4 s). Depois usa as coordenadas como endereço e calcula a prioridade sem o fator chuva |
| Erro inesperado numa ocorrência | Só essa ocorrência vai para revisão humana, o lote continua |
| Planilha aberta no Excel | Salva com outro nome |
| Execução repetida | **Idempotência:** o ID da ocorrência é estável (grade de cerca de 20 m), então OS já emitida não é duplicada |
| Evidência fraca (uma só detecção, confiança baixa) | **Revisão humana**, sem mobilizar equipe à toa |

Não há chaves de API: as duas APIs usadas são públicas e gratuitas. Configurações opcionais ficam no arquivo
`.env` (fora do repositório, ver `.env.example`). Nenhum dado pessoal é processado: as entradas são
coordenadas e leituras de sensor.

## Evidências de validação
`python validacao/validar.py` gera um **lote rotulado** com 14 pontos (10 buracos reais e 4 falsos alarmes:
sombra, tampa de bueiro, mancha, lombada), 37 detecções com ruído de GPS e 3 registros inválidos.
Saída completa em `evidencias/validacao_saida.txt`.

| Métrica | Resultado |
|---|---|
| Registros inválidos rejeitados | 3 de 3 |
| Pontos encontrados após agrupamento | 14 de 14, com 14 grupos puros (nenhum grupo misturou dois pontos) |
| Decisão OS vs. revisão | VP = 10, FP = 0, FN = 0, VN = 4 (precisão 1,00, recall 1,00) |
| Idempotência (2ª execução) | 0 OS novas, 10 reconhecidas como já emitidas |
| Arquivo ausente e JSON corrompido | Execução concluída sem exceção |
| API de clima fora do ar | 1 falha tratada, 10 OS geradas mesmo assim |

**Limites honestos:** o lote é sintético e foi montado com cenários típicos. Ele prova que a lógica faz o
que foi projetada para fazer, não a precisão em campo. Os erros reais devem aparecer em casos de fronteira:
dois buracos a menos de 25 m (seriam agrupados num só) ou um buraco visto em só um quadro com confiança
média (iria para revisão humana). O desempenho da câmera em si é medido na pasta `03-visao-computacional`.

**Execução real (online):** com as detecções do IoT, o robô consultou o Nominatim (endereços reais na Vila
Azevedo/Tatuapé) e o Open-Meteo (16,3 mm de chuva previstos), que elevou a prioridade. Ver `saida/execucao.log`.

## Proteção de dados, ética e ODS
O robô não processa dados pessoais: recebe só coordenadas, confiança da câmera e leituras do sensor. As
imagens ficam no módulo de visão, e o que chega aqui é apenas o resultado. A decisão é explicável (cada
ponto do escore tem um motivo) e casos duvidosos vão para revisão humana, para que a automação não mande
equipes à toa nem ignore um problema real. Como o caminhão passa em todas as ruas, bairros que reclamam
menos deixam de ser esquecidos (**ODS 10**). Vias mais seguras e mantidas apoiam o **ODS 11** (meta 11.2) e
o **ODS 9** (meta 9.1).

## Como executar
```bash
cd 06-rpa
pip install -r requirements.txt
python robo_cidade_em_ordem.py              # execução real (usa as APIs públicas)
python robo_cidade_em_ordem.py --offline    # sem internet
python validacao/validar.py                 # testes com lote rotulado e casos de falha
```
Entradas: `entrada/deteccoes_visao.json` (gerado pelo notebook de visão) e `entrada/deteccoes_iot.json`
(gerado pelo receptor MQTT). Saídas em `saida/`. Para ver no front-end, entre como gestor, abra **Importar
detecções** e envie `saida/ordens_servico.json`.
