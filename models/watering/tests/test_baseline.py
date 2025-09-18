# tests/test_baseline.py
from app.baseline import forecast_soil_path, eta_to_threshold

def test_eta_basic():
    path = forecast_soil_path(last_soil_pct=35, theta_inf=10, k_per_hour=0.02, horizon_hours=72)
    p50, p90 = eta_to_threshold(path, theta_min=18.0)
    assert p50 > 0
