import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from backend.apps.ingestion_service import main as main_module

# NOTA (assunção do executor): o checklist de specs/02-ingestion-service.md §4 descreve
# o comportamento do "script principal" sob MOCK_ENABLED, que vive em main.py — não em
# mock_provider.py/chaos_generator.py, os dois arquivos que a plan nomeia em §5.2. Como a
# lógica testável desses dois itens só existe em main.py, testo-a aqui, dentro do mesmo
# diretório backend/apps/ingestion_service/tests/ (interpretação conservadora, registrada
# no resumo de execução).


# --- item (a): não gera nenhuma mensagem quando MOCK_ENABLED == false ---


@pytest.mark.asyncio
async def test_main_disabled_mock_never_starts_provider(monkeypatch):
    monkeypatch.setenv("MOCK_ENABLED", "false")

    with patch.object(main_module, "MqttMockProvider") as mock_provider_cls:
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(main_module.main(), timeout=0.05)

    mock_provider_cls.assert_not_called()


# --- item (b): conecta ao broker e inicia o loop assíncrono quando MOCK_ENABLED == true ---


@pytest.mark.asyncio
async def test_main_enabled_mock_starts_provider_loop(monkeypatch):
    monkeypatch.setenv("MOCK_ENABLED", "true")
    fake_provider = AsyncMock()

    with patch.object(
        main_module, "MqttMockProvider", return_value=fake_provider
    ) as mock_provider_cls:
        await main_module.main()

    mock_provider_cls.assert_called_once()
    fake_provider.start_loop.assert_awaited_once()
