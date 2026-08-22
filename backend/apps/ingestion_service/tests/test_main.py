import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from backend.apps.ingestion_service import main as main_module

# NOTA (herdada da caracterização de plan-11, atualizada pela plan-01): o gate do script
# principal vivia em MOCK_ENABLED (env var lida direto via os.getenv, fora do Pydantic) e
# passou a viver em settings.simulation_mode (Literal["MOCK", "HARDWARE"], Fail-Fast via
# shared_infra/config.py) — Regra 4 de specs/specs/03-migracao-simulador-esp32.md. Os dois
# testes abaixo substituem os testes de caracterização de MOCK_ENABLED com a mesma cobertura
# (gate desligado / gate ligado), adaptados ao novo mecanismo.


# --- SIMULATION_MODE == "HARDWARE": não instancia nem publica via MqttMockProvider ---


@pytest.mark.asyncio
async def test_main_hardware_mode_never_starts_provider(monkeypatch):
    monkeypatch.setattr(main_module.settings, "simulation_mode", "HARDWARE")

    with patch.object(main_module, "MqttMockProvider") as mock_provider_cls:
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(main_module.main(), timeout=0.05)

    mock_provider_cls.assert_not_called()


# --- SIMULATION_MODE == "MOCK": conecta ao broker e inicia o loop assíncrono ---


@pytest.mark.asyncio
async def test_main_mock_mode_starts_provider_loop(monkeypatch):
    monkeypatch.setattr(main_module.settings, "simulation_mode", "MOCK")
    fake_provider = AsyncMock()

    with patch.object(
        main_module, "MqttMockProvider", return_value=fake_provider
    ) as mock_provider_cls:
        await main_module.main()

    mock_provider_cls.assert_called_once()
    fake_provider.start_loop.assert_awaited_once()
