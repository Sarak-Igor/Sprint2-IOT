import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from backend.apps.digital_twin_core.persistence_handler import (
    MqttPersistenceHandler,
    TopicResolver,
)


class FakeMqttMessage:
    """Simula um paho.mqtt.MQTTMessage sem abrir socket nenhum."""

    def __init__(self, topic, payload_bytes):
        self.topic = topic
        self.payload = payload_bytes


class _FakeScalars:
    def __init__(self, first_value):
        self._first_value = first_value

    def first(self):
        return self._first_value


class _FakeResult:
    def __init__(self, scalar_one_or_none_value=None, scalars_first_value=None):
        self._scalar_one_or_none_value = scalar_one_or_none_value
        self._scalars_first_value = scalars_first_value

    def scalars(self):
        return _FakeScalars(self._scalars_first_value)

    def scalar_one_or_none(self):
        return self._scalar_one_or_none_value


class _FakeAsyncSession:
    """Dublê da sessão SQLAlchemy assíncrona: registra add/commit/rollback em memória."""

    def __init__(self, execute_result):
        self._execute_result = execute_result
        self.added = []
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, _stmt):
        return self._execute_result

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


def _patch_session(monkeypatch, fake_session):
    monkeypatch.setattr(
        "backend.apps.digital_twin_core.persistence_handler.AsyncSessionLocal",
        lambda: fake_session,
    )


# --- item (a): payload MQTT inválido é tratado sem exceção não tratada ---


def test_on_message_invalid_payload_does_not_raise():
    handler = MqttPersistenceHandler()
    msg = FakeMqttMessage("Forzy/telemetry/sensor1", b"{not-json-and-not-float")

    handler.on_message(client=MagicMock(), userdata=None, msg=msg)


def test_on_message_invalid_payload_skips_coroutine_dispatch():
    handler = MqttPersistenceHandler()
    handler.loop = MagicMock()
    msg = FakeMqttMessage("Forzy/telemetry/sensor1", b"{not-json-and-not-float")

    with patch(
        "backend.apps.digital_twin_core.persistence_handler.asyncio.run_coroutine_threadsafe"
    ) as mock_dispatch:
        handler.on_message(client=MagicMock(), userdata=None, msg=msg)

    mock_dispatch.assert_not_called()


def test_on_message_valid_float_payload_dispatches_coroutine():
    handler = MqttPersistenceHandler()
    handler.loop = MagicMock()
    msg = FakeMqttMessage("Forzy/telemetry/sensor1", b"23.5")

    with patch(
        "backend.apps.digital_twin_core.persistence_handler.asyncio.run_coroutine_threadsafe"
    ) as mock_dispatch:
        handler.on_message(client=MagicMock(), userdata=None, msg=msg)

    mock_dispatch.assert_called_once()
    mock_dispatch.call_args.args[
        0
    ].close()  # coroutine nunca agendada de fato (dispatch mockado)


# --- TopicResolver.resolve() (nomeado em plan §2 junto de save_telemetry) ---


@pytest.mark.asyncio
async def test_topic_resolver_resolve_returns_mapping_and_caches(monkeypatch):
    asset_id = uuid.uuid4()
    variable_id = uuid.uuid4()
    mapping = SimpleNamespace(asset_id=asset_id, variable_id=variable_id)
    fake_session = _FakeAsyncSession(_FakeResult(scalars_first_value=mapping))
    call_count = {"n": 0}

    def fake_session_factory():
        call_count["n"] += 1
        return fake_session

    monkeypatch.setattr(
        "backend.apps.digital_twin_core.persistence_handler.AsyncSessionLocal",
        fake_session_factory,
    )
    resolver = TopicResolver()

    first = await resolver.resolve("Forzy/telemetry/sensor1")
    second = await resolver.resolve("Forzy/telemetry/sensor1")

    assert first == (asset_id, variable_id)
    assert second == first
    assert call_count["n"] == 1  # segunda chamada veio do cache, sem nova sessão


@pytest.mark.asyncio
async def test_topic_resolver_resolve_returns_none_when_no_mapping(monkeypatch):
    fake_session = _FakeAsyncSession(_FakeResult(scalars_first_value=None))
    _patch_session(monkeypatch, fake_session)
    resolver = TopicResolver()

    result = await resolver.resolve("Forzy/telemetry/desconhecido")

    assert result is None


# --- item (b): limiar inferior (critical < nominal) gera alerta quando valor <= critical ---


@pytest.mark.asyncio
async def test_save_telemetry_lower_limit_critical_triggers_alert(monkeypatch):
    asset_id, variable_id = uuid.uuid4(), uuid.uuid4()
    fake_asset = SimpleNamespace(
        applied_thresholds={
            str(variable_id): {"critical": 1000.0, "warning": 1500.0, "nominal": 1800.0}
        },
        status="operational",
    )
    fake_session = _FakeAsyncSession(_FakeResult(scalar_one_or_none_value=fake_asset))
    _patch_session(monkeypatch, fake_session)
    handler = MqttPersistenceHandler()

    await handler.save_telemetry(asset_id, variable_id, 900.0)  # <= critical

    assert fake_session.committed is True
    assert len(fake_session.added) == 2  # reading + anomaly
    anomaly = fake_session.added[1]
    assert anomaly.severity == "critical"
    assert anomaly.threshold_value == 1000.0
    assert fake_asset.status == "alert"


@pytest.mark.asyncio
async def test_save_telemetry_lower_limit_warning_triggers_warning(monkeypatch):
    asset_id, variable_id = uuid.uuid4(), uuid.uuid4()
    fake_asset = SimpleNamespace(
        applied_thresholds={
            str(variable_id): {"critical": 1000.0, "warning": 1500.0, "nominal": 1800.0}
        },
        status="operational",
    )
    fake_session = _FakeAsyncSession(_FakeResult(scalar_one_or_none_value=fake_asset))
    _patch_session(monkeypatch, fake_session)
    handler = MqttPersistenceHandler()

    await handler.save_telemetry(
        asset_id, variable_id, 1400.0
    )  # <= warning, > critical

    anomaly = fake_session.added[1]
    assert anomaly.severity == "warning"
    assert fake_asset.status == "warning"


@pytest.mark.asyncio
async def test_save_telemetry_lower_limit_within_nominal_range_no_anomaly(monkeypatch):
    asset_id, variable_id = uuid.uuid4(), uuid.uuid4()
    fake_asset = SimpleNamespace(
        applied_thresholds={
            str(variable_id): {"critical": 1000.0, "warning": 1500.0, "nominal": 1800.0}
        },
        status="operational",
    )
    fake_session = _FakeAsyncSession(_FakeResult(scalar_one_or_none_value=fake_asset))
    _patch_session(monkeypatch, fake_session)
    handler = MqttPersistenceHandler()

    await handler.save_telemetry(asset_id, variable_id, 1800.0)  # dentro do nominal

    assert len(fake_session.added) == 1  # só a leitura, nenhuma anomalia
    assert fake_asset.status == "operational"
