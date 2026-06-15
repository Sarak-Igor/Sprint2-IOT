class MetricConverter:
    """
    Realiza a normalização e conversão de sinais brutos para unidades do SI.
    Seguindo o princípio de Zero Hardcode, as regras podem ser expandidas.
    """
    
    @staticmethod
    def raw_to_celsius(raw_value: float) -> float:
        """Exemplo de conversão de sinal linear para Celsius"""
        # Supondo entrada de 0-1023 (10 bit) para 0-200°C
        return round((raw_value / 1023.0) * 200.0, 2)

    @staticmethod
    def normalize_vibration(vibration_raw: float) -> float:
        """Normaliza valores de vibração para mm/s RMS"""
        return round(vibration_raw, 4)

    @staticmethod
    def calculate_efficiency(output_power: float, input_power: float) -> float:
        """Calcula eficiência energética"""
        if input_power == 0:
            return 0.0
        return round((output_power / input_power) * 100, 2)
