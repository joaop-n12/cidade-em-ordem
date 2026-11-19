"""Publica as mesmas mensagens do ESP32 para testar o receptor sem o Wokwi."""

import json
import os
import time

import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
VEICULO = "caminhao-01"
T = f"cidadeemordem/{VEICULO}/"

seq = 0


def msg(tipo, lat, lon, g, dist, prof, severidade=None):
    global seq
    seq += 1
    m = {
        "veiculo": VEICULO, "seq": seq, "tipo": tipo, "lat": lat, "lon": lon,
        "impacto_g": g, "distancia_cm": dist, "profundidade_cm": prof, "uptime_ms": seq * 3000,
    }
    if severidade:
        m["severidade"] = severidade
    return json.dumps(m)


def main():
    comandos = []
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"cidadeemordem-sim-{os.getpid()}")
    c.on_message = lambda cl, u, m: comandos.append(m.payload.decode())
    c.connect(BROKER, 1883, 60)
    c.subscribe(T + "comando", qos=1)
    c.loop_start()
    c.publish(T + "status", json.dumps({"status": "online"}), qos=1, retain=True)
    time.sleep(1)

    cenarios = [
        ("1. Rua em bom estado", T + "telemetria", msg("telemetria", -23.53980, -46.57710, 1.01, 40.1, 0.1)),
        ("2. Buraco moderado (R. Tuiuti)", T + "evento", msg("possivel_buraco", -23.54020, -46.57630, 2.2, 46.0, 6.0, "moderada")),
        ("3. Mesmo buraco, 2a passagem", T + "evento", msg("possivel_buraco", -23.54021, -46.57632, 2.4, 46.5, 6.5, "moderada")),
        ("4. Buraco severo (Av. Celso Garcia)", T + "evento", msg("possivel_buraco", -23.54310, -46.57120, 3.4, 53.0, 13.0, "alta")),
        ("5. Mensagem corrompida", T + "telemetria", "{leitura quebrada"),
        ("6. Leitura fora da faixa", T + "telemetria", msg("telemetria", -23.54, -46.57, 99.0, 40.0, 0.0)),
    ]
    for nome, topico, payload in cenarios:
        print(f"\n>>> {nome}\n    {topico}\n    {payload}")
        c.publish(topico, payload, qos=1)
        time.sleep(2.5)

    time.sleep(2)
    print("\nComandos recebidos de volta da central (o LED do ESP32 acenderia):")
    for cmd in comandos:
        print("   ", cmd)
    c.loop_stop()
    c.disconnect()


if __name__ == "__main__":
    main()
