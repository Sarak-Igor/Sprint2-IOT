import json
import socket
import threading

import paho.mqtt.client as mqtt
import pytest
from fastapi.testclient import TestClient

from api.index import app
from backend.shared_infra.config import settings

CONTROL_TOPIC = "Forzy/config/device"


def _broker_host_port():
    host, port = settings.mqtt_broker_url.replace("mqtt://", "").split(":")
    return host, int(port)


def _broker_reachable():
    host, port = _broker_host_port()
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _broker_reachable(),
    reason=(
        "Broker MQTT indisponível em settings.mqtt_broker_url — suba `docker-compose up -d` "
        "para rodar este teste de integração real (test-integracao-api)."
    ),
)


def test_post_config_publishes_to_real_broker(tmp_path, monkeypatch):
    monkeypatch.setattr("api.index.CONFIG_FILE", tmp_path / "simulator_config.json")
    host, port = _broker_host_port()

    received_payloads = []
    message_arrived = threading.Event()
    subscriber = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def on_message(_client, _userdata, msg):
        received_payloads.append(msg.payload.decode())
        message_arrived.set()

    subscriber.on_message = on_message
    subscriber.connect(host, port)
    subscriber.subscribe(CONTROL_TOPIC)
    subscriber.loop_start()

    try:
        with TestClient(app) as client:
            response = client.post("/api/config", json={"running": True, "interval": 7})
            assert response.status_code == 200
            arrived = message_arrived.wait(timeout=5.0)
    finally:
        subscriber.loop_stop()
        subscriber.disconnect()

    assert arrived, (
        "Broker não entregou a mensagem publicada por POST /api/config a tempo"
    )
    assert json.loads(received_payloads[0]) == {"measurement_interval_ms": 7000}
