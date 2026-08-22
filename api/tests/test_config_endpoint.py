from unittest.mock import patch

from fastapi.testclient import TestClient

from api.index import app, mqtt_client

# NOTA: TestClient é usado sem "with" para não disparar o evento "startup" (que chamaria
# mqtt_client.connect()/loop_start() de verdade, contra um broker que não existe neste
# ambiente de teste). A rota POST /api/config só depende de mqtt_client.publish(), mockado
# em cada teste.
client = TestClient(app)


def test_post_config_with_interval_publishes_expected_mqtt_schema(
    tmp_path, monkeypatch
):
    monkeypatch.setattr("api.index.CONFIG_FILE", tmp_path / "simulator_config.json")

    with patch.object(mqtt_client, "publish") as mock_publish:
        response = client.post("/api/config", json={"running": True, "interval": 5})

    assert response.status_code == 200
    mock_publish.assert_called_once_with(
        "Forzy/config/device", '{"measurement_interval_ms": 5000}'
    )


def test_post_config_without_interval_does_not_publish_to_mqtt(tmp_path, monkeypatch):
    monkeypatch.setattr("api.index.CONFIG_FILE", tmp_path / "simulator_config.json")

    with patch.object(mqtt_client, "publish") as mock_publish:
        response = client.post("/api/config", json={"running": False})

    assert response.status_code == 200
    mock_publish.assert_not_called()


def test_post_config_still_persists_simulator_config_json(tmp_path, monkeypatch):
    config_file = tmp_path / "simulator_config.json"
    monkeypatch.setattr("api.index.CONFIG_FILE", config_file)

    with patch.object(mqtt_client, "publish"):
        client.post("/api/config", json={"running": True, "interval": 3})

    assert config_file.exists()
    assert '"interval": 3' in config_file.read_text(encoding="utf-8")
