import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.device_profiles.base_spec import MotorTechnicalSpecs

# Mapeando dinamicamente a raiz do repositório (subindo 2 níveis a partir de shared_infra)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    """
    Soberania de Dados e Configuração: 
    O Pydantic centraliza a gestão de segredos e URLs, garantindo que o sistema 
    seja portável entre ambientes (Dev, Staging, Produção).
    """
    # Seletor de Perfil: Define qual motor o sistema está simulando/monitorando no momento
    active_motor_profile: str = os.getenv("ACTIVE_MOTOR_PROFILE", "motor_modelo_a")
    
    # Infraestrutura de Comunicação e Persistência
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/neondb")
    mqtt_broker_url: str = os.getenv("MQTT_BROKER_URL", "mqtt://localhost:1883")
    opcua_server_url: str = os.getenv("OPCUA_SERVER_URL", "opc.tcp://localhost:4840/freeopcua/server/")
    
    # Armazenamento de Arquivos (Manuais, Schematics e PDFs)
    r2_access_key_id: str = os.getenv("R2_ACCESS_KEY_ID", "")
    r2_secret_access_key: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
    r2_endpoint_url: str = os.getenv("R2_ENDPOINT_URL", "")
    r2_bucket_name: str = os.getenv("R2_BUCKET_NAME", "forzy-manuais")
    
    # Política de CORS para segurança do Frontend
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "*")

    # Notificações / Alertas (Telegram)
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    @property
    def specs(self) -> MotorTechnicalSpecs:
        """
        Camada de Abstração Zero-Hardcode: 
        Lê dinamicamente o arquivo JSON de especificações técnicas do motor 
        selecionado, permitindo trocar o ativo sem alterar uma linha de código.
        """
        path = ROOT_DIR / "backend" / "device_profiles" / self.active_motor_profile / "technical_specs.json"
        return MotorTechnicalSpecs.load_from_json(path)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

# Singleton global para acesso centralizado às configurações
settings = Settings()

def get_active_profile_path() -> Path:
    """Retorna o caminho do diretório de assets do motor ativo."""
    return ROOT_DIR / "backend" / "device_profiles" / settings.active_motor_profile
