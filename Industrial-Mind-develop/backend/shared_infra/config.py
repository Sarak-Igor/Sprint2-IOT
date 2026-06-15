import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Mapeando dinamicamente a raiz do repositório (subindo 2 níveis a partir de shared_infra)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    """
    Classe central de configurações. O Pydantic irá procurar essas 
    variáveis no ambiente do sistema ou no arquivo .env.
    """
    # Usamos alias para garantir que DATABASE_URL (maiúsculo) no Vercel mapeie para database_url
    active_motor_profile: str = os.getenv("ACTIVE_MOTOR_PROFILE", "motor_modelo_A")
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/neondb")
    mqtt_broker_url: str = os.getenv("MQTT_BROKER_URL", "mqtt://localhost:1883")
    opcua_server_url: str = os.getenv("OPCUA_SERVER_URL", "opc.tcp://localhost:4840/freeopcua/server/")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

# Instância Singleton global
settings = Settings()

def get_active_profile_path() -> Path:
    """
    Retorna o caminho absoluto para a pasta de abstração do motor atualmente ativo.
    """
    return ROOT_DIR / "backend" / "device_profiles" / settings.active_motor_profile
