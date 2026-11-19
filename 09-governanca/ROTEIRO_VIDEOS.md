# Roteiros dos vídeos

Dica geral: **não leia texto**. Use estes tópicos como lembrete e fale com suas palavras. Grave a tela com o OBS ou
com Win + G (Xbox Game Bar). Publique no YouTube como **Não listado**.

## 1. Vídeo de Governança (integração): 5 a 7 minutos (máximo 7:00)

| Tempo | Quem | O que mostrar | O que falar (tópicos) |
|---|---|---|---|
| 0:00–0:40 | João | Rosto ou slide com nome do projeto | Nomes e RMs. Problema: 113 mil pedidos de tapa-buraco por ano em SP, tudo depende de alguém reclamar |
| 0:40–1:10 | João | Diagrama do README | Ideia: o caminhão de lixo já passa em toda rua, então colocamos câmera e sensor nele |
| 1:10–2:10 | Guilherme | Wokwi rodando + terminal do receptor | Mexer no slider do acelerômetro, mostrar a mensagem MQTT chegando, o buraco confirmado e o LED acendendo |
| 2:10–3:00 | Guilherme | Gradio da visão computacional | Enviar foto de buraco, mostrar caixa e confiança. Falar das métricas (mAP) e da divisão sem vazamento |
| 3:00–3:50 | João | Terminal rodando o robô RPA + planilha Excel | Robô junta câmera e sensor, busca endereço e chuva, gera OS e manda casos fracos para revisão humana |
| 3:50–4:40 | João | Front-end: importar OS, mapa, detalhe com os motivos da prioridade | O gestor vê por que cada buraco é prioridade |
| 4:40–5:40 | Guilherme | Assistente: pergunta sobre calçada, status da Rua Catiguá, pergunta com CPF (mascarado), "estou sangrando" | RAG com leis reais (vindas do PLN), ferramenta de status, proteções de privacidade |
| 5:40–6:20 | Guilherme | Quadro 5 do documento (integrado ou não) | Memristor e quântica ficaram como estudo. Integração entre módulos feita por arquivos |
| 6:20–6:50 | João | Quadro de princípios de governança | Explicabilidade, revisão humana, LGPD, equidade entre bairros |
| 6:50–7:00 | Ambos | Rosto | Encerramento |

Antes de gravar, deixe tudo aberto: Wokwi, receptor rodando, Colab do Gradio aberto, `npm run dev` e `python app.py`.

## 2. Vídeo de Visão Computacional (curto, ~2 a 3 min)
1. Gradio, aba Imagem: 2 fotos com buraco e 1 sem buraco, mostrando caixa e confiança.
2. Ajustar o slider do limiar e explicar o equilíbrio entre precisão e recall.
3. Aba Vídeo: processar `trajeto_simulado.mp4` e mostrar FPS e detecções.
4. Mostrar rapidamente o `deteccoes_visao.json` e dizer que ele vai para o robô RPA.

## 3. Vídeo de PLN (até 5 min)
1. Colab: mostrar a pasta `documentos/` com os 5 arquivos (PDF, HTML, DOCX, TXT).
2. Abrir a interface Gradio, enviar os arquivos e colar o relato fictício.
3. Clicar "Gerar corpus", mostrar o relatório (exemplos, tokens, duplicatas) e o antes e depois da anonimização.
4. Baixar os 3 arquivos JSONL e abrir um deles.

## 4. Vídeo de Generative AI (~3 min)
1. `python app.py`, abrir http://localhost:8000.
2. Fazer as perguntas de exemplo e mostrar o painel lateral (rota, fontes, trechos, dados mascarados).
3. Mostrar a resposta de emergência e a recusa fora do tema.
4. Mostrar o mesmo assistente funcionando dentro do front-end React.
