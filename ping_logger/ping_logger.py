import os
import json
import time
import csv
from datetime import datetime, timedelta
from pythonping import ping
import paho.mqtt.client as mqtt

CONFIG_PATH = "/data/options.json"
LOG_FILE = "/data/ping_logger.csv"

print("=== [PING LOGGER START] ===")
print("Wczytywanie configu z", CONFIG_PATH)
try:
    with open(CONFIG_PATH) as f:
        conf = json.load(f)
    print("Config wczytany:", conf)
except Exception as e:
    print("Błąd przy wczytywaniu configu:", e)
    raise SystemExit(1)

TARGETS = conf.get("targets", ["8.8.8.8"])
INTERVAL = int(conf.get("interval", 2))
KEEP_DAYS = int(conf.get("keep_days", 2))
MQTT_HOST = conf.get("mqtt_host", "localhost")
MQTT_PORT = int(conf.get("mqtt_port", 1883))
MQTT_USER = conf.get("mqtt_user", "")
MQTT_PASS = conf.get("mqtt_pass", "")

DISCOVERY_PREFIX = 'homeassistant'
DEVICE_NAME = 'ping_logger'

def log_ping(ip, rtt):
    try:
        with open(LOG_FILE, "a") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().isoformat(), ip, rtt if rtt is not None else "timeout"])
    except Exception as e:
        print(f"Błąd przy logowaniu pingu {ip}: {e}")

def cleanup_logs(days):
    try:
        if not os.path.exists(LOG_FILE):
            return
        cutoff = datetime.now() - timedelta(days=days)
        with open(LOG_FILE, "r") as f:
            rows = list(csv.reader(f))
        new_rows = [row for row in rows if row and datetime.fromisoformat(row[0]) > cutoff]
        with open(LOG_FILE, "w") as f:
            writer = csv.writer(f)
            writer.writerows(new_rows)
    except Exception as e:
        print(f"Błąd przy czyszczeniu logów: {e}")

def mqtt_publish_discovery(client, ip):
    sensor_id = f"ping_{ip.replace('.', '_')}"
    topic_cfg = f"{DISCOVERY_PREFIX}/sensor/{sensor_id}/config"
    topic_state = f"{DISCOVERY_PREFIX}/sensor/{sensor_id}/state"

    payload_cfg = {
        "name": f"Ping {ip}",
        "state_topic": topic_state,
        "unit_of_measurement": "ms",
        "unique_id": sensor_id,
        "device_class": "measurement",
        "device": {
            "identifiers": [DEVICE_NAME],
            "name": "PingLogger",
            "manufacturer": "Waldi"
        }
    }
    print(f"[DISCOVERY] Publikuję discovery na {topic_cfg}: {payload_cfg}")
    client.publish(topic_cfg, json.dumps(payload_cfg), retain=True)

def main():
    print("Próba połączenia z MQTT:", MQTT_HOST, MQTT_PORT)
    try:
        client = mqtt.Client(protocol=mqtt.MQTTv311)
        if MQTT_USER:
            client.username_pw_set(MQTT_USER, MQTT_PASS)
        client.connect(MQTT_HOST, MQTT_PORT)
        print("Połączono z MQTT")
        client.loop_start()
    except Exception as e:
        print("Błąd połączenia z MQTT:", e)
        raise SystemExit(2)

    # Publikuj discovery na start, tylko raz!
    for ip in TARGETS:
        mqtt_publish_discovery(client, ip)

    last_values = {}  # Zapamiętaj ostatni ping dla każdego IP

    print("Startuję pętlę pingowania...")
    while True:
        for ip in TARGETS:
            print(f"Pinguje {ip} ...")
            try:
                resp = ping(ip, count=1, timeout=1)
                if resp.success():
                    # int tylko, bez miejsc po przecinku!
                    rtt = int(round(resp.rtt_avg_ms))
                else:
                    rtt = "timeout"
            except Exception as e:
                print(f"Błąd pingu do {ip}: {e}")
                rtt = "timeout"

            log_ping(ip, rtt)

            # Wysyłaj tylko jeśli wartość się zmieniła
            prev = last_values.get(ip, None)
            if rtt != prev:
                topic_state = f"{DISCOVERY_PREFIX}/sensor/ping_{ip.replace('.', '_')}/state"
                print(f"[STATE] {ip}: wysyłam state: {rtt} (poprzedni: {prev})")
                client.publish(topic_state, str(rtt), retain=True)
                last_values[ip] = rtt
            else:
                print(f"[STATE] {ip}: brak zmiany, nie wysyłam (ostatni: {prev})")
        cleanup_logs(KEEP_DAYS)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()