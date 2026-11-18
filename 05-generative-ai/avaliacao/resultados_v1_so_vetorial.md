# Avaliação do assistente

Modelo: **sem LLM (modo extrativo)** · 24 perguntas · 18/11/2026 19:26

| Métrica | Resultado |
|---|---|
| Roteamento correto (RAG / ferramenta / emergência / fora do tema) | 24/24 (100%) |
| Recuperação: fonte esperada entre os 4 trechos (acerto@4) | 16/18 (89%) |
| Resposta contém as palavras-chave esperadas | 20/24 (83%) |
| Respostas RAG com citação de fonte [n] | 18/18 |
| Respostas RAG com número sem suporte no contexto (possível alucinação) | 0/18 |

| Pergunta | Rota esperada | Rota obtida | Fonte recuperada | Palavras-chave | Resposta (início) |
|---|---|---|---|---|---|
| Quem tem que consertar a calçada na frente da minha casa? | rag | rag_extrativo ✔ | ✔ | ✔ | Em São Paulo, quem cuida da calçada é o responsável pelo imóvel em frente a ela: proprietário, condomínio ou quem tem a posse do imóvel. Ele deve construir, man… |
| Quando uma calçada é considerada em mau estado? | rag | rag_extrativo ✔ | ✔ | ✔ | Quando tem buracos, ondulações, desníveis que a rua não exige ou obstáculos que impeçam as pessoas de andar com segurança. Consertos feitos sem combinar com o r… |
| A prefeitura quebrou minha calçada numa obra, quem paga? | rag | rag_extrativo ✔ | ✔ | ✔ | O Município deve reparar os danos que causar às calçadas quando fizer obras e melhorias públicas de sua responsabilidade (Lei 15.442/2011, art. 10, § 1º). [1]… |
| A raiz de uma árvore estragou minha calçada, preciso arrumar? | rag | rag_extrativo ✔ | ✔ | ✔ | Enquanto a prefeitura não fizer o corte ou a retirada da árvore, você fica dispensado de consertar a calçada. Depois do corte, você tem 30 dias para regularizar… |
| Qual a largura mínima da faixa livre da calçada? | rag | rag_extrativo ✔ | ✔ | ✔ | Qualquer que seja a largura da calçada, deve existir uma faixa livre de no mínimo 1,20 metro, só para a circulação de pedestres (Lei 15.442/2011, art. 8º, parág… |
| Vou ser multado direto pela calçada quebrada? | rag | rag_extrativo ✔ | ✔ | ✔ | Não. Antes de qualquer multa, o responsável recebe uma Notificação Orientativa (Lei 15.442/2011, art. 10-A). [1]… |
| Quanto tempo tenho para regularizar a calçada depois da multa? | rag | rag_extrativo ✔ | ✔ | ✔ | Depois da autuação, o prazo para regularizar é de 60 dias. Se o problema for objeto bloqueando a calçada (art. 8º), o prazo cai para 20 dias (Lei 15.442/2011, a… |
| Terreno baldio precisa estar limpo? | rag | rag_extrativo ✔ | ✔ | ✔ | Sim. Os responsáveis por imóveis, com construção ou não, de frente para a rua, devem mantê-los limpos, capinados e drenados, e respondem se o terreno for usado … |
| O poder público responde por danos causados por falha na manutenção da | rag | rag_extrativo ✔ | ✔ | ✔ | O Código de Trânsito diz que os órgãos e entidades do Sistema Nacional de Trânsito respondem objetivamente por danos causados aos cidadãos por ação, omissão ou … |
| Trânsito seguro é um direito de quem? | rag | rag_extrativo ✔ | ✔ | ✔ | Sim. O Código de Trânsito diz que o trânsito em condições seguras é um direito de todos e um dever dos órgãos e entidades do Sistema Nacional de Trânsito (CTB, … |
| O que é acostamento? | rag | rag_extrativo ✔ | ✔ | ✔ | Pelo Código de Trânsito Brasileiro (Anexo I), acostamento é: parte da via diferenciada da pista de rolamento destinada à parada ou estacionamento de veículos, e… |
| O que é uma ciclofaixa? | rag | rag_extrativo ✔ | ✔ | ✔ | Pelo Código de Trânsito Brasileiro (Anexo I), ciclofaixa é: parte da pista de rolamento destinada à circulação exclusiva de ciclos, delimitada por sinalização e… |
| O que é acessibilidade pela lei? | rag | rag_extrativo ✔ | ✘ | ✘ | Recusar-se a entregar à autoridade de trânsito ou a seus agentes, mediante recibo, os documentos de habilitação, de registro, de licenciamento de veículo e outr… |
| O que são barreiras urbanísticas? | rag | rag_extrativo ✔ | ✘ | ✘ | Pelo Código de Trânsito Brasileiro (Anexo I), via urbana é: ruas, avenidas, vielas, ou caminhos e similares abertos à circulação pública, situados na área urban… |
| O que é coleta seletiva? | rag | rag_extrativo ✔ | ✔ | ✘ | É a coleta de resíduos sólidos que já foram separados de acordo com sua composição, como papel, plástico, vidro e metal (Lei 12.305/2010, art. 3º, V). [1]… |
| Qual a altura livre mínima sobre a calçada? | rag | rag_extrativo ✔ | ✔ | ✔ | A faixa livre deve ter altura livre de pelo menos 2,10 metros sem placas, toldos ou coberturas, e de pelo menos 3,00 metros sem partes de construções, medida a … |
| Qual a inclinação transversal máxima da faixa livre? | rag | rag_extrativo ✔ | ✔ | ✔ | A faixa livre deve ter inclinação transversal constante e não superior a 3% (Cartilha de Calçadas da Prefeitura de SP). [1]… |
| Quando vão arrumar o buraco da Rua Catiguá? | ferramenta | ferramenta ✔ | - | ✔ | Encontrei 1 ocorrência(s) na Catiguá: - **OC-C00C9390CD**: buraco em Rua Catiguá, Vila Azevedo. Status: **Aberta**. Detectado automaticamente pelo caminhão de c… |
| Qual a situação do conserto na Rua Inexistente da Silva? | ferramenta | ferramenta ✔ | - | ✔ | Não encontrei ocorrências registradas automaticamente na Inexistente da Silva. Se você viu um problema lá, registre na tela "Registrar" do app ou na Central 156… |
| Caí num buraco e estou sangrando muito | emergencia | emergencia ✔ | - | ✔ | Isso parece uma emergência. Ligue agora: **SAMU 192** (pessoa ferida), **Bombeiros 193** ou **Defesa Civil 199** (fio caído, desabamento, cratera). Não se aprox… |
| Tem um fio elétrico no chão depois que a árvore caiu | emergencia | emergencia ✔ | - | ✔ | Isso parece uma emergência. Ligue agora: **SAMU 192** (pessoa ferida), **Bombeiros 193** ou **Defesa Civil 199** (fio caído, desabamento, cratera). Não se aprox… |
| Qual o melhor time de futebol do Brasil? | fora_do_tema | fora_do_tema ✔ | - | ✔ | Desculpe, só consigo ajudar com assuntos de ruas, calçadas, buracos, lixo nas vias, acessibilidade e os direitos do cidadão sobre esses problemas. Para outros a… |
| Me dá uma receita de bolo de chocolate | fora_do_tema | fora_do_tema ✔ | - | ✔ | Desculpe, só consigo ajudar com assuntos de ruas, calçadas, buracos, lixo nas vias, acessibilidade e os direitos do cidadão sobre esses problemas. Para outros a… |
| Meu nome é Ana Lima e meu CPF é 123.456.789-09. Calçada esburacada é b (mascarado: CPF,NOME) | rag | rag_extrativo ✔ | ✔ | ✘ | § 1º Na impossibilidade de permanência do acompanhante ou do atendente pessoal junto à pessoa com deficiência, cabe ao profissional de saúde responsável pelo tr… |