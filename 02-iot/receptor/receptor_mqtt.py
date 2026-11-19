"""Receptor MQTT: recebe os dados do ESP32, grava no SQLite e confirma os buracos.

Uso: python receptor_mqtt.py
"""

import json
import logging
import math
import os
import sqlite3
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import paho.mqtt.client as mqtt

BASE = Path(__file__).resolve().parent
RAIZ = BASE.parent.parent
DB_PATH = BASE / "dados" / "iot.db"
EXPORT_PATH = RAIZ / "06-rpa" / "entrada" / "deteccoes_iot.json"

BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
PORTA = int(os.getenv("MQTT_PORT", "1883"))
TOPICO_BASE = "cidadeemordem/+/"
RAIO_MESMO_BURACO_M = 25

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(BASE / "receptor.log", encoding="utf-8")],
)
log = logging.getLogger("receptor")


def carregar_env():
    env = BASE / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if "=" in linha and not linha.strip().startswith("#"):
                k, v = linha.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def conectar_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recebido_em TEXT, veiculo TEXT, seq INTEGER, tipo TEXT,
            lat REAL, lon REAL, impacto_g REAL, distancia_cm REAL, profundidade_cm REAL,
            severidade TEXT, payload TEXT
        );
        CREATE TABLE IF NOT EXISTS buracos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL, lon REAL, primeira_deteccao TEXT, ultima_deteccao TEXT,
            passagens INTEGER, maior_impacto_g REAL, maior_profundidade_cm REAL,
            status TEXT
        );
        CREATE TABLE IF NOT EXISTS status_veiculo (
            veiculo TEXT PRIMARY KEY, status TEXT, atualizado_em TEXT
        );
        """
    )
    return con


def distancia_m(lat1, lon1, lat2, lon2):
    # haversine, em metros
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def validar(msg):
    obrigatorios = ["veiculo", "tipo", "lat", "lon", "impacto_g", "profundidade_cm"]
    faltando = [c for c in obrigatorios if c not in msg]
    if faltando:
        raise ValueError(f"campos ausentes: {faltando}")
    if not (-90 <= float(msg["lat"]) <= 90 and -180 <= float(msg["lon"]) <= 180):
        raise ValueError("coordenadas fora do intervalo")
    if float(msg["impacto_g"]) < 0 or float(msg["impacto_g"]) > 16:
        raise ValueError("impacto fora da faixa do sensor")


def enviar_telegram(texto):
    token, chat = os.getenv("TELEGRAM_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        log.info("Telegram não configurado - alerta apenas no log: %s", texto)
        return
    try:
        dados = urllib.parse.urlencode({"chat_id": chat, "text": texto}).encode()
        urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", dados, timeout=10)
        log.info("Alerta enviado ao Telegram")
    except Exception as e:
        log.warning("Falha ao enviar Telegram (%s) - alerta mantido no log", e)


def exportar_para_rpa(con):
    linhas = con.execute(
        "SELECT id, lat, lon, primeira_deteccao, ultima_deteccao, passagens, maior_impacto_g, maior_profundidade_cm, status "
        "FROM buracos ORDER BY id"
    ).fetchall()
    itens = [
        {
            "id_origem": f"iot-{r[0]}",
            "fonte": "sensor",
            "tipo": "buraco",
            "lat": r[1],
            "lon": r[2],
            "detectado_em": r[4],
            "passagens": r[5],
            "impacto_g": r[6],
            "profundidade_cm": r[7],
            "status_iot": r[8],
        }
        for r in linhas
    ]
    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXPORT_PATH.write_text(json.dumps(itens, ensure_ascii=False, indent=2), encoding="utf-8")


def tratar_evento(cliente, con, msg, veiculo):
    lat, lon = float(msg["lat"]), float(msg["lon"])
    g, prof = float(msg["impacto_g"]), float(msg["profundidade_cm"])
    agora = datetime.now().isoformat(timespec="seconds")

    existente = None
    for b in con.execute("SELECT id, lat, lon, passagens, maior_impacto_g, maior_profundidade_cm, status FROM buracos"):
        if distancia_m(lat, lon, b[1], b[2]) <= RAIO_MESMO_BURACO_M:
            existente = b
            break

    if existente:
        bid, passagens = existente[0], existente[3] + 1
        con.execute(
            "UPDATE buracos SET ultima_deteccao=?, passagens=?, maior_impacto_g=MAX(maior_impacto_g, ?), "
            "maior_profundidade_cm=MAX(maior_profundidade_cm, ?) WHERE id=?",
            (agora, passagens, g, prof, bid),
        )
        status_anterior = existente[6]
    else:
        cur = con.execute(
            "INSERT INTO buracos (lat, lon, primeira_deteccao, ultima_deteccao, passagens, maior_impacto_g, maior_profundidade_cm, status) "
            "VALUES (?, ?, ?, ?, 1, ?, ?, 'suspeito')",
            (lat, lon, agora, agora, g, prof),
        )
        bid, passagens, status_anterior = cur.lastrowid, 1, "suspeito"

    confirmado = msg.get("severidade") == "alta" or passagens >= 2
    if confirmado and status_anterior != "confirmado":
        con.execute("UPDATE buracos SET status='confirmado' WHERE id=?", (bid,))
        log.warning("BURACO #%s CONFIRMADO em (%.5f, %.5f) - %.2f g, %.1f cm, %d passagem(ns)", bid, lat, lon, g, prof, passagens)
        cliente.publish(f"cidadeemordem/{veiculo}/comando", json.dumps({"acao": "alerta_critico", "buraco_id": bid}), qos=1)
        enviar_telegram(
            f"Cidade em Ordem: buraco confirmado #{bid}\n"
            f"Local: https://maps.google.com/?q={lat},{lon}\n"
            f"Impacto {g:.1f} g | profundidade {prof:.0f} cm | {passagens} passagem(ns).\n"
            f"Ordem de serviço será aberta pelo robô."
        )
    elif confirmado:
        # ja confirmado: so avisa o motorista de novo
        log.warning("Buraco #%s ja confirmado - nova passagem (%d), alerta reenviado ao veiculo", bid, passagens)
        cliente.publish(f"cidadeemordem/{veiculo}/comando", json.dumps({"acao": "alerta_critico", "buraco_id": bid}), qos=1)
    else:
        log.info("Buraco #%s %s (passagens=%d)", bid, "registrado como suspeito" if passagens == 1 else "atualizado", passagens)

    con.commit()
    exportar_para_rpa(con)


def main():
    carregar_env()
    con = conectar_db()

    def on_connect(cliente, userdata, flags, reason_code, properties=None):
        log.info("Conectado ao broker %s (código %s)", BROKER, reason_code)
        for sufixo in ("telemetria", "evento", "status"):
            cliente.subscribe(TOPICO_BASE + sufixo, qos=1)
        log.info("Assinando %s{telemetria,evento,status}", TOPICO_BASE)

    def on_message(cliente, userdata, m):
        veiculo = m.topic.split("/")[1]
        try:
            msg = json.loads(m.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            log.error("Mensagem inválida descartada em %s: %r", m.topic, m.payload[:80])
            return

        if m.topic.endswith("/status"):
            con.execute(
                "INSERT OR REPLACE INTO status_veiculo VALUES (?, ?, ?)",
                (veiculo, msg.get("status"), datetime.now().isoformat(timespec="seconds")),
            )
            con.commit()
            log.info("Veículo %s está %s", veiculo, msg.get("status"))
            return

        try:
            validar(msg)
        except (ValueError, TypeError) as e:
            log.error("Leitura rejeitada (%s): %s", e, msg)
            return

        con.execute(
            "INSERT INTO leituras (recebido_em, veiculo, seq, tipo, lat, lon, impacto_g, distancia_cm, profundidade_cm, severidade, payload) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                datetime.now().isoformat(timespec="seconds"), veiculo, msg.get("seq"), msg["tipo"],
                msg["lat"], msg["lon"], msg["impacto_g"], msg.get("distancia_cm"), msg["profundidade_cm"],
                msg.get("severidade"), json.dumps(msg),
            ),
        )
        con.commit()
        log.info("[%s] %s | %.2f g | prof %.1f cm", m.topic.split("/")[-1], veiculo, msg["impacto_g"], msg["profundidade_cm"])

        if msg["tipo"] == "possivel_buraco":
            tratar_evento(cliente, con, msg, veiculo)

    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"cidadeemordem-central-{os.getpid()}")
    cliente.on_connect = on_connect
    cliente.on_message = on_message
    cliente.reconnect_delay_set(min_delay=1, max_delay=30)
    log.info("Conectando a %s:%s ...", BROKER, PORTA)
    cliente.connect(BROKER, PORTA, keepalive=60)
    try:
        cliente.loop_forever()
    except KeyboardInterrupt:
        log.info("Receptor encerrado.")


if __name__ == "__main__":
    main()
