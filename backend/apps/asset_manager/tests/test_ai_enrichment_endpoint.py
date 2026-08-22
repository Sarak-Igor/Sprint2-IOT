import uuid
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.apps.asset_manager.domain.ai_enrichment import MotorEnrichmentError
from backend.apps.asset_manager.domain.entities import MotorSpecEnrichment
from backend.apps.asset_manager.web import router as router_module
from backend.shared_infra.database_client.postgresql import get_db


class _FakeResult:
    """Dublê do retorno de session.execute(select(...)) — só o que o router usa."""

    def __init__(self, items):
        self._items = list(items)

    def scalars(self):
        return self

    def all(self):
        return self._items

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None


class FakeAssetSession:
    """Dublê da sessão SQLAlchemy assíncrona: identifica a tabela pelo SQL renderizado do
    Select e responde com dados fixos; registra add/commit em memória. Mock só de I/O externo
    (banco) — a lógica de orquestração do endpoint roda de verdade."""

    def __init__(self, variables, sensor):
        self._variables = variables
        self._sensor = sensor
        self.added = []
        self.commits = 0

    async def execute(self, stmt):
        sql = str(stmt)
        if "data_variables" in sql:
            return _FakeResult(self._variables)
        if "sensor_hardware" in sql:
            return _FakeResult([self._sensor] if self._sensor else [])
        return _FakeResult([])

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.commits += 1

    async def refresh(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()


def _fake_variable(name):
    return SimpleNamespace(id=uuid.uuid4(), name=name, unit="C")


def _fake_sensor():
    return SimpleNamespace(id=uuid.uuid4(), model_name="Generic Sensor")


def _build_client(session):
    app = FastAPI()
    app.include_router(router_module.router, prefix="/api")

    async def _override_get_db():
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    return TestClient(app)


def _sample_enrichment(known_variable_name):
    return MotorSpecEnrichment(
        brand="WEG",
        model="W22",
        power_hp=100.0,
        rpm_nominal=1750.0,
        ip_rating="IP55",
        threshold_suggestions={
            known_variable_name: {"nominal": 70.0, "warning": 80.0, "critical": 90.0},
            "Variável Inventada Pelo LLM": {"nominal": 1.0},
        },
    )


def test_create_asset_with_ai_enrichment_persists_model_and_asset():
    temperature = _fake_variable("Temperatura")
    session = FakeAssetSession(variables=[temperature], sensor=_fake_sensor())
    client = _build_client(session)

    with patch.object(
        router_module,
        "enrich_motor_specs",
        return_value=_sample_enrichment("Temperatura"),
    ) as mock_enrich:
        response = client.post(
            "/api/assets",
            json={
                "name": "Motor Linha 3",
                "location": "Galpão B",
                "description": "WEG W22 100cv trifásico IP55",
            },
        )

    assert response.status_code == 200
    mock_enrich.assert_called_once_with("WEG W22 100cv trifásico IP55", ["Temperatura"])

    body = response.json()
    assert body["name"] == "Motor Linha 3"
    assert body["status"] == "operational"
    assert str(temperature.id) in body["applied_thresholds"]
    assert "Variável Inventada Pelo LLM" not in str(body["applied_thresholds"])

    added_types = [type(obj).__name__ for obj in session.added]
    assert "MotorModelDB" in added_types
    assert "TelemetryMappingDB" in added_types


def test_create_asset_with_ai_enrichment_returns_503_when_llm_unavailable():
    session = FakeAssetSession(variables=[], sensor=None)
    client = _build_client(session)

    with patch.object(
        router_module,
        "enrich_motor_specs",
        side_effect=MotorEnrichmentError("OPENROUTER_API_KEY não configurada"),
    ):
        response = client.post(
            "/api/assets",
            json={
                "name": "Motor X",
                "location": "Setor 1",
                "description": "motor genérico",
            },
        )

    assert response.status_code == 503
    assert session.added == []


def test_create_asset_with_ai_enrichment_rejects_short_description():
    session = FakeAssetSession(variables=[], sensor=None)
    client = _build_client(session)

    with patch.object(router_module, "enrich_motor_specs") as mock_enrich:
        response = client.post(
            "/api/assets",
            json={"name": "Motor X", "location": "Setor 1", "description": "ab"},
        )

    assert response.status_code == 422
    mock_enrich.assert_not_called()
