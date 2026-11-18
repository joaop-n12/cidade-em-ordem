# Cidade em Ordem: Visão Computacional (detecção de buracos)

**Integrantes:** João Pedro de Souza Nunes (RM567318) · Guilherme Nakamura (RM567460)

YOLO11n com transfer learning para detectar buracos nas imagens da câmera do caminhão de coleta.
Relatório técnico: [RELATORIO_VISAO.md](RELATORIO_VISAO.md).

**Resultado no teste:** precisão 0,611 · recall 0,456 · F1 0,523 · mAP@0,5 0,442 · 30 FPS em CPU (640×640).

## Como executar
**Demonstração local (modelo já treinado):**
```bash
pip install -r requirements.txt
python app_visao.py      # http://127.0.0.1:7860
```
**Treino completo:** abra `deteccao_buracos.ipynb` no Colab, escolha *GPU T4* e use *Executar tudo* (~20 min).

## Arquivos
- `deteccao_buracos.ipynb`: notebook completo (gerado a partir de `src_notebook.py`)
- `app_visao.py`: interface Gradio (imagem e vídeo)
- `resultados/`: modelo `best.pt`, métricas, gráficos, vídeos e `deteccoes_visao.json` (entrada do robô RPA)
- `exemplos/`: imagens do conjunto de teste para a demonstração
