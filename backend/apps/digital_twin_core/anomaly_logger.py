import json
import logging
from datetime import datetime
from pathlib import Path

# Configuração de Logs Industriais
log_path = Path(__file__).parent.parent.parent.parent / "logs"
log_path.mkdir(exist_ok=True)

logging.basicConfig(
    filename=log_path / "anomaly_events.log",
    level=logging.WARNING,
    format='%(asctime)s - [ANOMALY] - %(message)s'
)

class AnomalyEventLogger:
    """
    Simula uma automação RPA que registra eventos críticos em log e
    prepara o gatilho para ações corretivas automáticas.
    """
    
    @staticmethod
    def log_critical_event(asset_tag: str, sensor: str, value: float, limit: float):
        message = {
            "timestamp": datetime.now().isoformat(),
            "asset_tag": asset_tag,
            "sensor": sensor,
            "value": value,
            "limit": limit,
            "status": "CRITICAL",
            "action_taken": "Automated Alert Dispatched"
        }
        
        log_entry = f"Ativo: {asset_tag} | Sensor: {sensor} | Valor: {value} (Limite: {limit})"
        logging.warning(log_entry)
        
        # Em uma versão real, aqui poderíamos integrar com Selenium/RPA para abrir um chamado
        print(f"[RPA EVENT] Registro de anomalia gerado para {asset_tag}")
        return message

if __name__ == "__main__":
    # Teste rápido
    AnomalyEventLogger.log_critical_event("WEG_W22_01", "temp_windings", 156.5, 155.0)
