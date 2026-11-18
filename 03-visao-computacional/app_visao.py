"""
Demonstração local do detector de buracos (para o vídeo), usando o modelo já treinado em resultados/best.pt.

    pip install -r requirements.txt
    python app_visao.py          -> abre http://127.0.0.1:7860
"""

import json
import time
from pathlib import Path

import cv2
import gradio as gr
import numpy as np
from ultralytics import YOLO

BASE = Path(__file__).resolve().parent
MODELO = YOLO(str(BASE / "resultados" / "best.pt"))
METRICAS = json.loads((BASE / "resultados" / "metricas_visao.json").read_text(encoding="utf-8"))
LIMIAR = float(METRICAS["limiar"])


def analisar(img_bgr, limiar):
    r = MODELO.predict(img_bgr, conf=limiar, imgsz=640, verbose=False)[0]
    h, w = img_bgr.shape[:2]
    ocs = []
    for b in r.boxes:
        x1, y1, x2, y2 = map(float, b.xyxy[0]); c = float(b.conf[0])
        ocs.append({"confianca": c, "area": (x2 - x1) * (y2 - y1) / (w * h),
                    "recomendacao": "abrir ordem de serviço" if c >= 0.5 else "enviar para vistoria"})
    return ocs, r.plot(), sum(r.speed.values())


def tela_imagem(img_rgb, limiar):
    if img_rgb is None:
        return None, "Envie uma imagem."
    ocs, anotada, ms = analisar(cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR), limiar)
    if not ocs:
        texto = f"Nenhum buraco detectado acima de {limiar:.2f} de confiança ({ms:.0f} ms)."
    else:
        texto = f"**{len(ocs)} buraco(s) detectado(s)** em {ms:.0f} ms\n\n" + "\n".join(
            f"- Buraco {i + 1}: confiança **{o['confianca']:.0%}**, {o['area']:.1%} da imagem → {o['recomendacao']}"
            for i, o in enumerate(ocs))
    texto += "\n\n*A detecção apoia a triagem e não substitui a vistoria técnica presencial.*"
    return cv2.cvtColor(anotada, cv2.COLOR_BGR2RGB), texto


def tela_video(caminho, limiar):
    if not caminho:
        return None, "Envie um vídeo."
    cap = cv2.VideoCapture(str(caminho))
    fps = cap.get(cv2.CAP_PROP_FPS) or 2
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    saida = BASE / "resultados" / "gradio_saida.mp4"
    out = cv2.VideoWriter(str(saida), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    tempos, total, quadros = [], 0, 0
    t0 = time.perf_counter()
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        ocs, anotada, ms = analisar(frame, limiar)
        tempos.append(ms); total += len(ocs); quadros += 1
        cv2.putText(anotada, f"quadro {quadros}  {len(ocs)} buraco(s)  {1000 / ms:.0f} FPS", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        out.write(anotada)
    cap.release(); out.release()
    return str(saida), (f"{quadros} quadros · {total} detecções · latência média {np.mean(tempos):.1f} ms/quadro · "
                        f"{1000 / np.mean(tempos):.1f} FPS do modelo · {quadros / (time.perf_counter() - t0):.1f} FPS ponta a ponta")


m = METRICAS["teste"]
with gr.Blocks(title="Cidade em Ordem - Detecção de buracos") as demo:
    gr.Markdown(f"# Cidade em Ordem: detecção de buracos (YOLO11n)\nCâmera do caminhão de coleta → buraco com confiança. "
                f"Teste: precisão {m['precisao']:.2f} · recall {m['recall']:.2f} · mAP@0,5 {m['mAP50']:.2f}")
    lim = gr.Slider(0.05, 0.9, value=LIMIAR, step=0.05, label="Limiar de confiança")
    with gr.Tab("Imagem"):
        with gr.Row():
            ei, si = gr.Image(label="Foto da via"), gr.Image(label="Resultado")
        ti = gr.Markdown()
        gr.Button("Analisar", variant="primary").click(tela_imagem, [ei, lim], [si, ti])
        exemplos = sorted((BASE / "exemplos").glob("*.jpg"))
        if exemplos:
            gr.Examples([str(p) for p in exemplos], inputs=ei)
    with gr.Tab("Vídeo (monitoramento contínuo)"):
        with gr.Row():
            ev, sv = gr.Video(label="Vídeo do trajeto"), gr.Video(label="Vídeo anotado")
        tv = gr.Markdown()
        gr.Button("Processar vídeo", variant="primary").click(tela_video, [ev, lim], [sv, tv])
        gr.Examples([str(BASE / "resultados" / "trajeto_simulado.mp4")], inputs=ev)

if __name__ == "__main__":
    demo.launch()
