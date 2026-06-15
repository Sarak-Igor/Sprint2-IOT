import random

class ChaosGenerator:
    """Injeta anomalias aleatórias para acionar todos os alarmes do Gêmeo Digital."""
    
    def __init__(self, thresholds):
        self.thresholds = thresholds

    def apply_chaos(self, normal_val: float, sensor_type: str) -> float:
        # Variância normal de 2%
        variance = random.uniform(-0.02, 0.02)
        val = normal_val + (normal_val * variance)

        # 10% de chance de causar o Caos Absoluto em algum sensor
        if random.random() < 0.10:
            if sensor_type == "temp_windings":
                val = self.thresholds.temperature_windings_c.critical + random.uniform(1.0, 10.0)
            elif sensor_type == "temp_bearings":
                val = self.thresholds.temperature_bearings_c.critical + random.uniform(1.0, 5.0)
            elif sensor_type == "vibration":
                val = self.thresholds.vibration_rms_mm_s.critical + random.uniform(0.5, 2.0)
            elif sensor_type == "current":
                val = normal_val * 1.5 # 50% de sobrecorrente
                
        return round(val, 2)
