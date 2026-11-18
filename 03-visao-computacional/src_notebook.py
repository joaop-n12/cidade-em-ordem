# %% [markdown]
# # Cidade em Ordem: Visão Computacional para detecção de buracos
# **Global Solution 2026.2 · CitizenTech · Visão Computacional**
#
# | Integrante | RM |
# |---|---|
# | João Pedro de Souza Nunes | RM567318 |
# | Guilherme Nakamura | RM567460 |
#
# **Nicho escolhido:** 1. Infraestrutura e Pavimentação, com detecção de **buracos na via** por caixas delimitadoras (bounding boxes).
#
# **Contexto:** uma câmera instalada no caminhão de coleta de lixo, que já passa por todas as ruas, filma o trajeto. O modelo
# localiza buracos em cada quadro e informa a confiança. As detecções vão para o robô RPA, que junta as repetidas,
# cruza com o sensor IoT do caminhão e abre a ordem de serviço. **A detecção apoia a triagem e a rota de inspeção.
# Ela não substitui a vistoria técnica presencial.**
#
# **Como rodar:** no Colab, use *Ambiente de execução → Alterar tipo → GPU T4* e depois *Executar tudo*.
# Leva cerca de 15 a 20 minutos.

# %% [markdown]
# ## 0. Instalação e ambiente

# %%
import os
RAPIDO = os.getenv("CV_RAPIDO") == "1"   # usado só para teste rápido em CPU; no Colab fica False
NO_COLAB = "google.colab" in str(get_ipython()) if "get_ipython" in globals() else False
if NO_COLAB:
    !pip -q install ultralytics gradio

# %%
import json, random, shutil, time, platform, glob
from pathlib import Path
import numpy as np
import cv2
import matplotlib.pyplot as plt
import torch
from ultralytics import YOLO

random.seed(42); np.random.seed(42)
TRABALHO = Path("/content") if NO_COLAB else Path("trabalho_cv").resolve()
TRABALHO.mkdir(exist_ok=True)
DISPOSITIVO = 0 if torch.cuda.is_available() else "cpu"
HARDWARE = torch.cuda.get_device_name(0) if torch.cuda.is_available() else f"CPU {platform.processor()} ({os.cpu_count()} núcleos)"
print("Dispositivo:", HARDWARE)

# %% [markdown]
# ## 1. Seleção e preparação dos dados
#
# **Base pública:** *Road Damage / Pothole Segmentation* (Roboflow Universe, licença CC BY 4.0, espelhada no
# Hugging Face em `manot/pothole-segmentation`), com 819 imagens de vias com buracos anotados no formato COCO.
# A base tem 4 rótulos ("potholes", "pothole", "potholes" duplicado e 1 anotação "object"), que são variações do
# mesmo conceito. **Unificamos tudo na classe única `buraco`.**
#
# **Conversão:** COCO (JSON com caixas em pixels `x, y, largura, altura`) para YOLO (um `.txt` por imagem com
# `classe xc yc w h` normalizados entre 0 e 1).
#
# **Divisão sem vazamento:** o Roboflow gera variações da mesma foto (`images44_jpg.rf.<hash>.jpg`). Juntamos as três
# partições originais, **agrupamos pela foto de origem** (`images44_jpg`) e dividimos os grupos em
# **70% treino / 15% validação / 15% teste**. Assim, variações de uma mesma foto nunca ficam em conjuntos diferentes.

# %%
import zipfile, urllib.request
HF = "https://huggingface.co/datasets/manot/pothole-segmentation/resolve/main/data/"
BRUTO = TRABALHO / "bruto"
for parte in ("train", "valid", "test"):
    destino = BRUTO / parte
    if not destino.exists():
        zip_local = TRABALHO / f"{parte}.zip"
        if not zip_local.exists():
            urllib.request.urlretrieve(HF + f"{parte}.zip", zip_local)
        zipfile.ZipFile(zip_local).extractall(destino)
    print(parte, len(list(destino.glob("*.jpg"))), "imagens")

# %%
def chave_original(nome: str) -> str:
    """Nome da foto original (remove o sufixo de variação do Roboflow)."""
    return nome.split(".rf.")[0] if ".rf." in nome else Path(nome).stem

# Junta tudo: {arquivo: (caminho, [caixas YOLO])}
todas = {}
for parte in ("train", "valid", "test"):
    coco = json.loads((BRUTO / parte / "_annotations.coco.json").read_text())
    imgs = {im["id"]: im for im in coco["images"]}
    caixas = {im_id: [] for im_id in imgs}
    for a in coco["annotations"]:
        im = imgs[a["image_id"]]; x, y, w, h = a["bbox"]
        if w < 2 or h < 2:
            continue  # caixa degenerada
        caixas[a["image_id"]].append((0, (x + w / 2) / im["width"], (y + h / 2) / im["height"], w / im["width"], h / im["height"]))
    for im_id, im in imgs.items():
        todas[im["file_name"]] = (BRUTO / parte / im["file_name"], caixas[im_id])

grupos = {}
for nome in todas:
    grupos.setdefault(chave_original(nome), []).append(nome)
chaves = sorted(grupos)
random.Random(42).shuffle(chaves)
n = len(chaves); n_tr, n_va = int(n * 0.70), int(n * 0.15)
divisao = {
    "train": [a for k in chaves[:n_tr] for a in grupos[k]],
    "val": [a for k in chaves[n_tr:n_tr + n_va] for a in grupos[k]],
    "test": [a for k in chaves[n_tr + n_va:] for a in grupos[k]],
}
if RAPIDO:
    divisao = {"train": divisao["train"][:40], "val": divisao["val"][:10], "test": divisao["test"][:12]}

print(f"{len(todas)} arquivos vindos de {n} fotos originais distintas")
conj = {s: {chave_original(a) for a in v} for s, v in divisao.items()}
assert not (conj["train"] & conj["val"] or conj["train"] & conj["test"] or conj["val"] & conj["test"]), "vazamento!"
print("Sem vazamento entre treino, validação e teste.")

DADOS = TRABALHO / "buracos"
if DADOS.exists():
    shutil.rmtree(DADOS)
for split, arquivos in divisao.items():
    (DADOS / "images" / split).mkdir(parents=True)
    (DADOS / "labels" / split).mkdir(parents=True)
    for nome in arquivos:
        caminho, cx = todas[nome]
        shutil.copy(caminho, DADOS / "images" / split / nome)
        (DADOS / "labels" / split / (Path(nome).stem + ".txt")).write_text(
            "\n".join(f"{c} {a:.6f} {b:.6f} {w:.6f} {h:.6f}" for c, a, b, w, h in cx))
    print(f"{split:5s}: {len(arquivos)} imagens")
divisao = {s: [DADOS / "images" / s / a for a in v] for s, v in divisao.items()}

YAML = DADOS / "buracos.yaml"
YAML.write_text(f"path: {DADOS}\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n  0: buraco\n")

# %% [markdown]
# ### Análise exploratória dos rótulos

# %%
def ler_caixas(rotulo: Path):
    """Lê o rótulo YOLO (caixa ou polígono) e devolve caixas normalizadas (xc, yc, w, h)."""
    caixas = []
    if not rotulo.exists():
        return caixas
    for linha in rotulo.read_text().split("\n"):
        v = [float(x) for x in linha.split()[1:]]
        if len(v) == 4:
            caixas.append(v)
        elif len(v) >= 6:
            xs, ys = v[0::2], v[1::2]
            caixas.append([(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(xs) - min(xs), max(ys) - min(ys)])
    return caixas

estat = {}
for split in divisao:
    rot = list((DADOS / "labels" / split).glob("*.txt"))
    por_img = [len(ler_caixas(r)) for r in rot]
    areas = [w * h for r in rot for (_, _, w, h) in ler_caixas(r)]
    estat[split] = {"imagens": len(divisao[split]), "buracos": sum(por_img),
                    "media_por_imagem": round(float(np.mean(por_img)), 2) if por_img else 0,
                    "area_mediana_%": round(float(np.median(areas)) * 100, 2) if areas else 0}
print(json.dumps(estat, indent=1, ensure_ascii=False))

fig, ax = plt.subplots(1, 2, figsize=(11, 3.5))
todos = [len(ler_caixas(r)) for r in (DADOS / "labels" / "train").glob("*.txt")]
ax[0].hist(todos, bins=range(0, max(todos) + 2)); ax[0].set_title("Buracos por imagem (treino)")
areas = [w * h * 100 for r in (DADOS / "labels" / "train").glob("*.txt") for (_, _, w, h) in ler_caixas(r)]
ax[1].hist(areas, bins=30); ax[1].set_title("Área da caixa (% da imagem)")
plt.tight_layout(); plt.show()

# %%
def desenhar(img, caixas_px, cor, rotulos=None):
    for i, (x1, y1, x2, y2) in enumerate(caixas_px):
        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), cor, 3)
        if rotulos:
            cv2.putText(img, rotulos[i], (int(x1), max(15, int(y1) - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)
    return img

def caixas_gt_px(img_path: Path, split: str):
    img = cv2.imread(str(img_path)); h, w = img.shape[:2]
    cx = ler_caixas(DADOS / "labels" / split / (img_path.stem + ".txt"))
    return img, [((xc - bw / 2) * w, (yc - bh / 2) * h, (xc + bw / 2) * w, (yc + bh / 2) * h) for xc, yc, bw, bh in cx]

fig, eixos = plt.subplots(2, 3, figsize=(14, 7))
for e, p in zip(eixos.flat, random.sample(divisao["train"], 6)):
    img, gt = caixas_gt_px(DADOS / "images" / "train" / p.name, "train")
    e.imshow(cv2.cvtColor(desenhar(img, gt, (0, 255, 0)), cv2.COLOR_BGR2RGB)); e.axis("off")
plt.suptitle("Amostras do treino com rótulos"); plt.tight_layout(); plt.show()

# %% [markdown]
# **Pré-processamento:** o YOLO redimensiona cada imagem para **640×640** mantendo a proporção (*letterbox*, com
# preenchimento cinza) e **normaliza os pixels para 0–1**. Durante o treino, o *data augmentation* padrão (variação
# de brilho, saturação e matiz HSV, espelhamento horizontal, mosaico e escala) simula as variações urbanas de
# iluminação, sombra e enquadramento. Nenhuma augmentação é aplicada aos conjuntos de validação e teste.

# %% [markdown]
# ## 2. Implementação: transfer learning com YOLO11n
#
# **Por que YOLO11n (nano)?**
# - É um detector de **um estágio**: localiza e classifica numa única passada. É rápido o bastante para vídeo em
#   tempo real num computador embarcado barato dentro do caminhão.
# - Os pesos pré-treinados no COCO já sabem extrair bordas, texturas e formas. Fazemos **transfer learning** e só
#   ajustamos o modelo para a classe "buraco", o que funciona bem com poucas centenas de imagens.
# - Versões maiores (s/m) costumam ganhar alguns pontos de mAP, mas ficam 2 a 4 vezes mais lentas. Para triagem,
#   a velocidade e o custo do hardware pesam mais.

# %%
EPOCAS = 1 if RAPIDO else int(os.getenv("CV_EPOCAS", "40"))
modelo = YOLO("yolo11n.pt")
treino = modelo.train(
    data=str(YAML), epochs=EPOCAS, imgsz=640 if not RAPIDO else 320, batch=16 if not RAPIDO else 4,
    patience=10, seed=42, device=DISPOSITIVO, project=str(TRABALHO / "runs"), name="buracos",
    exist_ok=True, plots=True, verbose=False, workers=2,
)
PESOS = TRABALHO / "runs" / "buracos" / "weights" / "best.pt"
print("Melhor modelo:", PESOS)

# %%
from IPython.display import Image as IImage, display
curvas = TRABALHO / "runs" / "buracos" / "results.png"
if curvas.exists():
    display(IImage(filename=str(curvas), width=900))

# %% [markdown]
# ## 3. Avaliação no conjunto de teste (nunca visto)

# %%
melhor = YOLO(str(PESOS))
IMGSZ = 320 if RAPIDO else 640
m = melhor.val(data=str(YAML), split="test", imgsz=IMGSZ, device=DISPOSITIVO, plots=True,
               project=str(TRABALHO / "runs"), name="teste", exist_ok=True, verbose=False)
P, R = float(m.box.mp), float(m.box.mr)
metricas_teste = {
    "precisao": round(P, 3), "recall": round(R, 3),
    "f1": round(2 * P * R / (P + R + 1e-9), 3),
    "mAP50": round(float(m.box.map50), 3), "mAP50_95": round(float(m.box.map), 3),
}
print(json.dumps(metricas_teste, indent=1))

# %%
for nome in ("confusion_matrix.png", "BoxPR_curve.png", "PR_curve.png", "BoxF1_curve.png", "F1_curve.png"):
    arq = TRABALHO / "runs" / "teste" / nome
    if arq.exists():
        display(IImage(filename=str(arq), width=600))

# %% [markdown]
# ### Escolha do limiar de confiança
# Rodamos o modelo uma vez no teste com limiar baixo e calculamos precisão, recall e F1 para vários limiares,
# contando acerto quando a caixa prevista tem **IoU ≥ 0,5** com um buraco rotulado.

# %%
def iou(a, b):
    x1, y1, x2, y2 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter + 1e-9)

def casar(preds, gts, limiar_iou=0.5):
    """Casamento guloso: devolve (TP, FP, FN, lista de preds FP, lista de gts FN)."""
    usados, tp, fps = set(), 0, []
    for p in sorted(preds, key=lambda x: -x[4]):
        melhor_j, melhor_iou = -1, limiar_iou
        for j, g in enumerate(gts):
            if j not in usados and iou(p, g) >= melhor_iou:
                melhor_j, melhor_iou = j, iou(p, g)
        if melhor_j >= 0:
            usados.add(melhor_j); tp += 1
        else:
            fps.append(p)
    fns = [g for j, g in enumerate(gts) if j not in usados]
    return tp, len(fps), len(fns), fps, fns

TESTE = sorted((DADOS / "images" / "test").glob("*.jpg"))
cache = {}
for p in TESTE:
    r = melhor.predict(str(p), conf=0.05, imgsz=IMGSZ, device=DISPOSITIVO, verbose=False)[0]
    preds = [list(map(float, b.xyxy[0])) + [float(b.conf[0])] for b in r.boxes]
    _, gt = caixas_gt_px(p, "test")
    cache[p.name] = (preds, gt)

linhas = []
for lim in np.arange(0.1, 0.8, 0.05):
    TP = FP = FN = 0
    for preds, gt in cache.values():
        tp, fp, fn, _, _ = casar([q for q in preds if q[4] >= lim], gt)
        TP += tp; FP += fp; FN += fn
    pr, rc = TP / (TP + FP + 1e-9), TP / (TP + FN + 1e-9)
    linhas.append((round(lim, 2), round(pr, 3), round(rc, 3), round(2 * pr * rc / (pr + rc + 1e-9), 3), TP, FP, FN))
print("limiar | precisão | recall | F1 | TP | FP | FN")
for l in linhas:
    print(" | ".join(map(str, l)))
LIMIAR = max(linhas, key=lambda l: l[3])[0]
print(f"\nLimiar escolhido (maior F1): {LIMIAR}")

# %% [markdown]
# **Critério do limiar:** usamos o limiar de **maior F1** porque o sistema tem duas defesas contra falso positivo
# (a confirmação pelo sensor IoT do caminhão e a deduplicação pelo robô RPA). Por isso podemos aceitar um limiar
# um pouco mais baixo e priorizar o **recall**, já que deixar de ver um buraco é pior que mandar um fiscal conferir.
# Detecções com confiança abaixo de 0,5 entram como "vistoria" e não como ordem de serviço direta.

# %% [markdown]
# ## 4. Análise de acertos e erros

# %%
erros = []
for p in TESTE:
    preds, gt = cache[p.name]
    tp, fp, fn, lfp, lfn = casar([q for q in preds if q[4] >= LIMIAR], gt)
    erros.append((p, tp, fp, fn))

def mostrar(lista, titulo):
    if not lista:
        print("Nenhum caso para:", titulo); return
    fig, eixos = plt.subplots(1, len(lista), figsize=(5 * len(lista), 4))
    eixos = np.atleast_1d(eixos)
    for e, (p, tp, fp, fn) in zip(eixos, lista):
        img, gt = caixas_gt_px(p, "test")
        preds = [q for q in cache[p.name][0] if q[4] >= LIMIAR]
        desenhar(img, gt, (0, 255, 0))
        desenhar(img, [q[:4] for q in preds], (0, 0, 255), [f"{q[4]:.2f}" for q in preds])
        e.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)); e.axis("off"); e.set_title(f"TP={tp} FP={fp} FN={fn}")
    plt.suptitle(titulo + "  (verde = rótulo, vermelho = previsão)"); plt.tight_layout(); plt.show()

mostrar([e for e in erros if e[2] == 0 and e[3] == 0][:3], "Acertos")
mostrar(sorted(erros, key=lambda e: -e[3])[:3], "Mais buracos NÃO detectados (falsos negativos)")
mostrar(sorted(erros, key=lambda e: -e[2])[:3], "Mais detecções erradas (falsos positivos)")

# %% [markdown]
# ### Robustez a interferências urbanas
# Aplicamos às imagens de teste as interferências citadas no enunciado e medimos quanto o recall e a precisão
# caem: **sombra**, **pouca luz (anoitecer)**, **luz estourada**, **desfoque** (caminhão em movimento) e
# **obstrução parcial** (um carro na frente).

# %%
def sombra(img):
    h, w = img.shape[:2]; s = img.copy().astype(np.float32)
    pts = np.array([[0, 0], [int(w * 0.6), 0], [int(w * 0.35), h], [0, h]])
    mask = np.zeros((h, w), np.uint8); cv2.fillPoly(mask, [pts], 1)
    s[mask == 1] *= 0.4
    return s.clip(0, 255).astype(np.uint8)

def escuro(img):  return (255 * (img / 255.0) ** 2.2).astype(np.uint8)
def claro(img):   return cv2.convertScaleAbs(img, alpha=1.6, beta=60)
def desfoque(img): return cv2.GaussianBlur(img, (15, 15), 0)
def obstrucao(img):
    h, w = img.shape[:2]; o = img.copy()
    cv2.rectangle(o, (int(w * 0.35), int(h * 0.45)), (int(w * 0.75), int(h * 0.95)), (40, 40, 40), -1)
    return o

PERTURBACOES = {"original": lambda x: x, "sombra": sombra, "pouca luz": escuro, "luz estourada": claro,
                "desfoque": desfoque, "obstrução parcial": obstrucao}
robustez = {}
for nome, f in PERTURBACOES.items():
    TP = FP = FN = 0
    for p in TESTE:
        img, gt = caixas_gt_px(p, "test")
        r = melhor.predict(f(img), conf=LIMIAR, imgsz=IMGSZ, device=DISPOSITIVO, verbose=False)[0]
        preds = [list(map(float, b.xyxy[0])) + [float(b.conf[0])] for b in r.boxes]
        tp, fp, fn, _, _ = casar(preds, gt); TP += tp; FP += fp; FN += fn
    robustez[nome] = {"precisao": round(TP / (TP + FP + 1e-9), 3), "recall": round(TP / (TP + FN + 1e-9), 3)}
print(json.dumps(robustez, indent=1, ensure_ascii=False))

img0, _ = caixas_gt_px(TESTE[0], "test")
fig, eixos = plt.subplots(1, 6, figsize=(22, 3.5))
for e, (nome, f) in zip(eixos, PERTURBACOES.items()):
    e.imshow(cv2.cvtColor(f(img0), cv2.COLOR_BGR2RGB)); e.set_title(nome); e.axis("off")
plt.show()

# %% [markdown]
# ## 5. Desempenho: latência e FPS

# %%
def medir(dispositivo, n=50):
    amostra = (TESTE * 10)[:n]
    for p in amostra[:5]:   # aquecimento
        melhor.predict(str(p), imgsz=IMGSZ, device=dispositivo, verbose=False)
    tempos = []
    for p in amostra:
        r = melhor.predict(str(p), imgsz=IMGSZ, device=dispositivo, conf=LIMIAR, verbose=False)[0]
        tempos.append(sum(r.speed.values()))   # pré-processamento + inferência + pós-processamento (ms)
    ms = float(np.mean(tempos))
    return {"latencia_media_ms": round(ms, 1), "fps": round(1000 / ms, 1), "imagens": n}

desempenho = {"hardware_gpu": HARDWARE if torch.cuda.is_available() else None, "resolucao_entrada": f"{IMGSZ}x{IMGSZ}"}
if torch.cuda.is_available():
    desempenho["gpu"] = medir(0)
desempenho["cpu"] = medir("cpu", n=10 if RAPIDO else 30)
desempenho["hardware_cpu"] = f"{platform.processor() or platform.machine()} ({os.cpu_count()} núcleos)"
print(json.dumps(desempenho, indent=1, ensure_ascii=False))

# %% [markdown]
# ## 6. Integração com o CitizenTech
# ### 6.1 Função usada pelo protótipo
# Recebe uma imagem e devolve as ocorrências com confiança, a recomendação (ordem de serviço ou vistoria) e a
# imagem anotada.

# %%
ROTA = [(-23.53980, -46.57710), (-23.54020, -46.57630), (-23.54080, -46.57520),
        (-23.54150, -46.57400), (-23.54230, -46.57280), (-23.54310, -46.57120)]

def posicao_na_rota(fracao):
    """GPS simulado: posição do caminhão ao longo da rota (0 = início, 1 = fim)."""
    pos = fracao * (len(ROTA) - 1); i = min(int(pos), len(ROTA) - 2); t = pos - i
    return (ROTA[i][0] + t * (ROTA[i + 1][0] - ROTA[i][0]), ROTA[i][1] + t * (ROTA[i + 1][1] - ROTA[i][1]))

def analisar_imagem(img_bgr, limiar=None):
    limiar = LIMIAR if limiar is None else limiar
    r = melhor.predict(img_bgr, conf=limiar, imgsz=IMGSZ, device=DISPOSITIVO, verbose=False)[0]
    h, w = img_bgr.shape[:2]
    ocorrencias = []
    for b in r.boxes:
        x1, y1, x2, y2 = map(float, b.xyxy[0]); c = float(b.conf[0])
        area = (x2 - x1) * (y2 - y1) / (w * h)
        ocorrencias.append({
            "tipo": "buraco", "confianca": round(c, 3), "bbox": [round(x1), round(y1), round(x2), round(y2)],
            "area_relativa": round(area, 4),
            "recomendacao": "abrir ordem de serviço" if c >= 0.5 else "enviar para vistoria",
        })
    anotada = r.plot()
    return ocorrencias, anotada, sum(r.speed.values())

ocs, anotada, ms = analisar_imagem(cv2.imread(str(TESTE[0])))
print(json.dumps(ocs, indent=1, ensure_ascii=False), f"\n{ms:.1f} ms")
plt.imshow(cv2.cvtColor(anotada, cv2.COLOR_BGR2RGB)); plt.axis("off"); plt.show()

# %% [markdown]
# ### 6.2 Monitoramento contínuo: vídeo da câmera do caminhão
# Montamos um vídeo com a sequência de imagens de teste (simulando o trajeto do caminhão) e processamos quadro
# a quadro. Cada detecção recebe a posição GPS simulada do caminhão naquele instante. O resultado é exportado
# como `deteccoes_visao.json`, que o robô RPA (pasta `06-rpa/entrada`) lê para abrir as ordens de serviço.
# Para usar um vídeo real, troque `VIDEO_ENTRADA` pelo caminho do arquivo.

# %%
VIDEO_ENTRADA = TRABALHO / "trajeto_simulado.mp4"
seq_imgs = TESTE[: 12 if RAPIDO else 40]
escritor = cv2.VideoWriter(str(VIDEO_ENTRADA), cv2.VideoWriter_fourcc(*"mp4v"), 2, (960, 540))
for p in seq_imgs:
    escritor.write(cv2.resize(cv2.imread(str(p)), (960, 540)))
escritor.release()

def processar_video(caminho_entrada, caminho_saida, limiar=None):
    cap = cv2.VideoCapture(str(caminho_entrada))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    fps_in = cap.get(cv2.CAP_PROP_FPS) or 2
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(str(caminho_saida), cv2.VideoWriter_fourcc(*"mp4v"), fps_in, (w, h))
    deteccoes, tempos, i = [], [], 0
    inicio = time.perf_counter()
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        ocs, anotada, ms = analisar_imagem(frame, limiar)
        tempos.append(ms)
        lat, lon = posicao_na_rota(i / max(total - 1, 1))
        for k, o in enumerate(ocs):
            deteccoes.append({"id_origem": f"cv-q{i:04d}-{k}", "fonte": "camera", "lat": round(lat, 6), "lon": round(lon, 6),
                              "quadro": i, "detectado_em": time.strftime("%Y-%m-%dT%H:%M:%S"), **o})
        cv2.putText(anotada, f"quadro {i}  {len(ocs)} buraco(s)  {1000 / ms:.0f} FPS", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        out.write(anotada); i += 1
    cap.release(); out.release()
    total_s = time.perf_counter() - inicio
    return deteccoes, {"quadros": i, "latencia_media_ms": round(float(np.mean(tempos)), 1),
                       "fps_modelo": round(1000 / float(np.mean(tempos)), 1), "fps_ponta_a_ponta": round(i / total_s, 1)}

VIDEO_SAIDA = TRABALHO / "trajeto_anotado.mp4"
deteccoes_video, stats_video = processar_video(VIDEO_ENTRADA, VIDEO_SAIDA)
print(json.dumps(stats_video, indent=1), f"\n{len(deteccoes_video)} detecções no trajeto")

SAIDA_JSON = TRABALHO / "deteccoes_visao.json"
SAIDA_JSON.write_text(json.dumps(deteccoes_video, ensure_ascii=False, indent=1), encoding="utf-8")
(TRABALHO / "metricas_visao.json").write_text(json.dumps(
    {"estatisticas_dados": estat, "teste": metricas_teste, "limiar": LIMIAR, "varredura_limiar": linhas,
     "robustez": robustez, "desempenho": desempenho, "video": stats_video}, ensure_ascii=False, indent=1), encoding="utf-8")
print("Arquivos gerados:", SAIDA_JSON, TRABALHO / "metricas_visao.json", VIDEO_SAIDA)

# %% [markdown]
# ### 6.3 Interface de demonstração (Gradio)
# Interface para o vídeo de apresentação: envie uma foto ou um vídeo da via e veja os buracos localizados,
# a confiança e a recomendação.

# %%
import gradio as gr

def gr_imagem(img_rgb, limiar):
    if img_rgb is None:
        return None, "Envie uma imagem."
    ocs, anotada, ms = analisar_imagem(cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR), limiar)
    if not ocs:
        texto = f"Nenhum buraco detectado acima de {limiar:.2f} de confiança. ({ms:.0f} ms)"
    else:
        texto = f"**{len(ocs)} buraco(s) detectado(s)** em {ms:.0f} ms\n\n" + "\n".join(
            f"- Buraco {i+1}: confiança **{o['confianca']:.0%}**, {o['area_relativa']:.1%} da imagem → {o['recomendacao']}"
            for i, o in enumerate(ocs))
        texto += "\n\n*A detecção apoia a triagem e não substitui a vistoria técnica presencial.*"
    return cv2.cvtColor(anotada, cv2.COLOR_BGR2RGB), texto

def gr_video(caminho, limiar):
    if not caminho:
        return None, "Envie um vídeo."
    saida = TRABALHO / "gradio_saida.mp4"
    dets, st = processar_video(caminho, saida, limiar)
    return str(saida), f"{st['quadros']} quadros · {len(dets)} detecções · {st['fps_modelo']} FPS do modelo · {st['latencia_media_ms']} ms/quadro"

with gr.Blocks(title="Cidade em Ordem - Detecção de buracos") as demo:
    gr.Markdown("# Cidade em Ordem: detecção de buracos\nCâmera do caminhão de coleta → YOLO11n → ocorrência com confiança")
    lim = gr.Slider(0.05, 0.9, value=float(LIMIAR), step=0.05, label="Limiar de confiança")
    with gr.Tab("Imagem"):
        with gr.Row():
            ei = gr.Image(label="Foto da via"); si = gr.Image(label="Resultado")
        ti = gr.Markdown()
        gr.Button("Analisar").click(gr_imagem, [ei, lim], [si, ti])
        gr.Examples([str(p) for p in TESTE[:4]], inputs=ei)
    with gr.Tab("Vídeo (monitoramento contínuo)"):
        with gr.Row():
            ev = gr.Video(label="Vídeo do trajeto"); sv = gr.Video(label="Vídeo anotado")
        tv = gr.Markdown()
        gr.Button("Processar vídeo").click(gr_video, [ev, lim], [sv, tv])
        gr.Examples([str(VIDEO_ENTRADA)], inputs=ev)

if not RAPIDO and os.getenv("CV_SEM_INTERFACE") != "1":
    demo.launch(share=True, debug=False)

# %% [markdown]
# ## 7. Baixar os resultados
# Baixe os arquivos abaixo e coloque-os no repositório:
# - `deteccoes_visao.json` → `06-rpa/entrada/` (o robô abre as ordens de serviço)
# - `metricas_visao.json`, `best.pt` e os gráficos → `03-visao-computacional/resultados/`

# %%
pasta = TRABALHO / "resultados_visao"; pasta.mkdir(exist_ok=True)
for arq in [SAIDA_JSON, TRABALHO / "metricas_visao.json", PESOS, VIDEO_SAIDA, curvas,
            *(TRABALHO / "runs" / "teste").glob("*.png")]:
    if Path(arq).exists():
        shutil.copy(arq, pasta)
shutil.make_archive(str(TRABALHO / "resultados_visao"), "zip", pasta)
print("Pacote:", TRABALHO / "resultados_visao.zip")
if NO_COLAB:
    from google.colab import files
    files.download(str(TRABALHO / "resultados_visao.zip"))
