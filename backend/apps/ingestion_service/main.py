import sys
import asyncio
from pathlib import Path

# Configura o PYTHONPATH para enxergar a pasta 'backend'
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from backend.apps.ingestion_service.adapters.mock_provider import MqttMockProvider
from backend.shared_infra.config import settings


async def main():
    if settings.simulation_mode == "HARDWARE":
        print(
            "Modo Hardware Ativo - Simulador Python desabilitado via SIMULATION_MODE=HARDWARE."
        )
        # Mantém vivo para o Docker não cair (loop infinito inofensivo)
        while True:
            await asyncio.sleep(3600)

    print("Iniciando Ingestion Service (Modo MQTT com Gerador de Caos)...")
    provider = MqttMockProvider()
    await provider.start_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServiço de Ingestão encerrado pelo usuário.")
