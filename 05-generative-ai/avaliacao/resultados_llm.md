# Avaliação do assistente

Modelo: **Gemini (gemini-3-flash-preview)** · 24 perguntas · 18/11/2026 20:59

| Métrica | Resultado |
|---|---|
| Roteamento correto (RAG / ferramenta / emergência / fora do tema) | 24/24 (100%) |
| Recuperação: fonte esperada entre os 4 trechos (acerto@4) | 18/18 (100%) |
| Resposta contém as palavras-chave esperadas | 21/24 (88%) |
| Respostas RAG com citação de fonte [n] | 18/18 |
| Respostas RAG com número sem suporte no contexto (possível alucinação) | 1/18 |

| Pergunta | Rota esperada | Rota obtida | Fonte recuperada | Palavras-chave | Resposta (início) |
|---|---|---|---|---|---|
| Quem tem que consertar a calçada na frente da minha casa? | rag | rag ✔ | ✔ | ✔ | Em São Paulo, o responsável pelo imóvel é quem deve cuidar da calçada em frente a ele [1]. Isso vale para o dono da casa, o condomínio ou quem mora no local [1]… |
| Quando uma calçada é considerada em mau estado? | rag | rag ✔ | ✔ | ✔ | Uma calçada é considerada em mau estado quando apresenta buracos, ondulações ou desníveis que não são necessários para a rua [1]. Também é considerada ruim se t… |
| A prefeitura quebrou minha calçada numa obra, quem paga? | rag | rag ✔ | ✔ | ✔ | Se a prefeitura quebrar a sua calçada durante uma obra pública, ela mesma deve fazer o conserto. O Município é obrigado a reparar os danos que causar quando rea… |
| A raiz de uma árvore estragou minha calçada, preciso arrumar? | rag | rag ✔ | ✔ | ✔ | Enquanto a prefeitura não cortar ou retirar a árvore, você não é obrigado a consertar a calçada [1]. Você só precisará fazer o reparo depois que a prefeitura re… |
| Qual a largura mínima da faixa livre da calçada? | rag | rag ✔ | ✔ | ✔ | A calçada deve ter uma faixa livre de, no mínimo, 1,20 metro para a circulação de pedestres [1][3]. Essa faixa é o espaço que deve ficar sempre livre de obstácu… |
| Vou ser multado direto pela calçada quebrada? | rag | rag ✔ | ✔ | ✔ | Não, você não será multado de imediato. Antes de qualquer multa, o responsável pela calçada recebe uma Notificação Orientativa [1]. Essa notificação serve para … |
| Quanto tempo tenho para regularizar a calçada depois da multa? | rag | rag ✔ | ✔ | ✔ | Após receber a multa e a intimação, você tem o prazo de 60 dias para consertar a calçada [1][3]. Se o problema for algum objeto bloqueando a passagem, o prazo é… |
| Terreno baldio precisa estar limpo? | rag | rag ✔ | ✔ | ✘ | Sim, o dono do terreno baldio é obrigado a mantê-lo limpo. Isso vale para qualquer imóvel de frente para a rua, tenha ele construção ou não [1]. O local deve es… |
| O poder público responde por danos causados por falha na manutenção da | rag | rag_extrativo ✔ | ✔ | ✔ | O Código de Trânsito diz que os órgãos e entidades do Sistema Nacional de Trânsito respondem objetivamente por danos causados aos cidadãos por ação, omissão ou … |
| Trânsito seguro é um direito de quem? | rag | rag_extrativo ✔ | ✔ | ✔ | Sim. O Código de Trânsito diz que o trânsito em condições seguras é um direito de todos e um dever dos órgãos e entidades do Sistema Nacional de Trânsito (CTB, … |
| O que é acostamento? | rag | rag ✔ | ✔ | ✘ | O acostamento é uma parte da via que fica ao lado da pista onde os carros circulam [1]. Ele deve ser usado para parar ou estacionar o veículo apenas em casos de… |
| O que é uma ciclofaixa? | rag | rag_extrativo ✔ | ✔ | ✔ | Pelo Código de Trânsito Brasileiro (Anexo I), ciclofaixa é: parte da pista de rolamento destinada à circulação exclusiva de ciclos, delimitada por sinalização e… |
| O que é acessibilidade pela lei? | rag | rag_extrativo ✔ | ✔ | ✔ | É a possibilidade de usar, com segurança e autonomia, espaços, mobiliário, equipamentos urbanos, edificações, transportes, informação e comunicação, por pessoa … |
| O que são barreiras urbanísticas? | rag | rag ✔ | ✔ | ✘ | Barreiras urbanísticas são obstáculos ou problemas que existem nas ruas e nos espaços públicos. [1][4] Elas também podem estar em locais privados que são aberto… |
| O que é coleta seletiva? | rag | rag ✔ | ✔ | ✔ | A coleta seletiva é o recolhimento de lixo que já foi separado antes, de acordo com o material de que é feito [1][2]. Isso significa separar itens como papel, p… |
| Qual a altura livre mínima sobre a calçada? | rag | rag ✔ | ✔ | ✔ | A altura livre mínima depende do que está acima da calçada. Para placas, toldos ou coberturas, a altura deve ser de pelo menos 2,10 metros [1][3]. Já para parte… |
| Qual a inclinação transversal máxima da faixa livre? | rag | rag ✔ | ✔ | ✔ | A inclinação transversal, que é a caída para o lado da calçada, deve ser constante. Essa inclinação não pode ser maior do que 3% [1][2]. Isso serve para que o c… |
| Quando vão arrumar o buraco da Rua Catiguá? | ferramenta | ferramenta ✔ | - | ✔ | Encontrei 1 ocorrência(s) em 'Catiguá': - **OC-C00C9390CD**: buraco em Rua Catiguá, Vila Azevedo. Status: **Aberta**. Detectado automaticamente pelo caminhão de… |
| Qual a situação do conserto na Rua Inexistente da Silva? | ferramenta | ferramenta ✔ | - | ✔ | Não encontrei ocorrências registradas automaticamente em 'Inexistente da Silva'. Se você viu um problema lá, registre na tela "Registrar" do app ou na Central 1… |
| Caí num buraco e estou sangrando muito | emergencia | emergencia ✔ | - | ✔ | Isso parece uma emergência. Ligue agora: **SAMU 192** (pessoa ferida), **Bombeiros 193** ou **Defesa Civil 199** (fio caído, desabamento, cratera). Não se aprox… |
| Tem um fio elétrico no chão depois que a árvore caiu | emergencia | emergencia ✔ | - | ✔ | Isso parece uma emergência. Ligue agora: **SAMU 192** (pessoa ferida), **Bombeiros 193** ou **Defesa Civil 199** (fio caído, desabamento, cratera). Não se aprox… |
| Qual o melhor time de futebol do Brasil? | fora_do_tema | fora_do_tema ✔ | - | ✔ | Desculpe, só consigo ajudar com assuntos de ruas, calçadas, buracos, lixo nas vias, acessibilidade e os direitos do cidadão sobre esses problemas. Para outros a… |
| Me dá uma receita de bolo de chocolate | fora_do_tema | fora_do_tema ✔ | - | ✔ | Desculpe, só consigo ajudar com assuntos de ruas, calçadas, buracos, lixo nas vias, acessibilidade e os direitos do cidadão sobre esses problemas. Para outros a… |
| Meu nome é Ana Lima e meu CPF é 123.456.789-09. Calçada esburacada é b (mascarado: CPF,NOME) | rag | rag ✔ | ✔ | ✔ | Sim, uma calçada esburacada é considerada uma barreira. A lei define como barreira qualquer obstáculo que limite ou impeça a pessoa de circular e participar da … |