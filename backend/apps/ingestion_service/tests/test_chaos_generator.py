import random
from types import SimpleNamespace

from backend.apps.ingestion_service.adapters.chaos_generator import ChaosGenerator

# NOTA (achado, ver resumo de execução): ChaosGenerator não é importado por nenhum outro
# módulo do repositório (confirmado por grep) — MqttMockProvider._generate_value() reimplementa
# uma lógica de caos equivalente, sem usar esta classe. Testado aqui porque a plan nomeia
# explicitamente ChaosGenerator.apply_chaos() como alvo de caracterização.


def _thresholds():
    return SimpleNamespace(
        temperature_windings_c=SimpleNamespace(critical=120.0),
        temperature_bearings_c=SimpleNamespace(critical=90.0),
        vibration_rms_mm_s=SimpleNamespace(critical=4.5),
    )


def test_apply_chaos_without_chaos_roll_applies_only_variance(monkeypatch):
    monkeypatch.setattr(random, "uniform", lambda a, b: 0.0)
    monkeypatch.setattr(random, "random", lambda: 0.99)  # >= 0.10, sem caos
    generator = ChaosGenerator(_thresholds())

    result = generator.apply_chaos(100.0, "temp_windings")

    assert result == 100.0


def test_apply_chaos_windings_spike_uses_critical_threshold(monkeypatch):
    monkeypatch.setattr(random, "uniform", lambda a, b: a)
    monkeypatch.setattr(random, "random", lambda: 0.0)  # < 0.10, dispara caos
    generator = ChaosGenerator(_thresholds())

    result = generator.apply_chaos(100.0, "temp_windings")

    assert result == round(120.0 + 1.0, 2)


def test_apply_chaos_bearings_spike_uses_critical_threshold(monkeypatch):
    monkeypatch.setattr(random, "uniform", lambda a, b: a)
    monkeypatch.setattr(random, "random", lambda: 0.0)
    generator = ChaosGenerator(_thresholds())

    result = generator.apply_chaos(100.0, "temp_bearings")

    assert result == round(90.0 + 1.0, 2)


def test_apply_chaos_vibration_spike_uses_critical_threshold(monkeypatch):
    monkeypatch.setattr(random, "uniform", lambda a, b: a)
    monkeypatch.setattr(random, "random", lambda: 0.0)
    generator = ChaosGenerator(_thresholds())

    result = generator.apply_chaos(100.0, "vibration")

    assert result == round(4.5 + 0.5, 2)


def test_apply_chaos_current_spike_uses_150_percent_overload(monkeypatch):
    monkeypatch.setattr(random, "uniform", lambda a, b: 0.0)
    monkeypatch.setattr(random, "random", lambda: 0.0)
    generator = ChaosGenerator(_thresholds())

    result = generator.apply_chaos(100.0, "current")

    assert result == 150.0


def test_apply_chaos_unknown_sensor_type_keeps_only_variance(monkeypatch):
    monkeypatch.setattr(random, "uniform", lambda a, b: 0.0)
    monkeypatch.setattr(
        random, "random", lambda: 0.0
    )  # dispara caos, mas sem branch para o tipo
    generator = ChaosGenerator(_thresholds())

    result = generator.apply_chaos(100.0, "unknown_sensor")

    assert result == 100.0
