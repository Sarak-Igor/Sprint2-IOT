from unittest.mock import patch

import pytest

from backend.apps.ingestion_service.adapters.mock_provider import MqttMockProvider


# --- item (b): conecta ao broker e inicia o loop assíncrono de publicação ---


@pytest.mark.asyncio
async def test_connect_calls_broker_client_and_sets_is_connected():
    provider = MqttMockProvider()

    with (
        patch.object(provider.client, "connect") as mock_connect,
        patch.object(provider.client, "loop_start") as mock_loop_start,
    ):
        await provider.connect()

    mock_connect.assert_called_once()
    mock_loop_start.assert_called_once()
    assert provider.is_connected is True


@pytest.mark.asyncio
async def test_connect_leaves_is_connected_false_on_broker_failure():
    provider = MqttMockProvider()

    with patch.object(provider.client, "connect", side_effect=ConnectionRefusedError):
        await provider.connect()  # não deve propagar a exceção

    assert provider.is_connected is False


@pytest.mark.asyncio
async def test_publish_sends_rounded_value_when_connected():
    provider = MqttMockProvider()
    provider.is_connected = True

    with patch.object(provider.client, "publish") as mock_publish:
        await provider.publish("Forzy/telemetry/sensor1", 12.345)

    mock_publish.assert_called_once_with("Forzy/telemetry/sensor1", "12.35")


@pytest.mark.asyncio
async def test_publish_is_noop_when_not_connected():
    provider = MqttMockProvider()
    provider.is_connected = False

    with patch.object(provider.client, "publish") as mock_publish:
        await provider.publish("Forzy/telemetry/sensor1", 12.345)

    mock_publish.assert_not_called()
