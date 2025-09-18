# app/baseline.py
from typing import List, Tuple
import numpy as np
from .features import calc_vpd, rolling_k_estimate

def rule_of_thumb_k(vpd_kpa: float) -> float:
    """데이터 부족 시 임시 k 산식(보수적으로 시작)."""
    # 실내 화분 기준: 0.01~0.06/h 사이 범위에서 VPD에 비례
    return float(np.clip(0.015 + 0.02 * vpd_kpa, 0.005, 0.06))

def forecast_soil_path(
    last_soil_pct: float,
    theta_inf: float,
    k_per_hour: float,
    horizon_hours: int = 72,
) -> List[float]:
    xs = np.arange(1, horizon_hours + 1, dtype=float)
    path = theta_inf + (last_soil_pct - theta_inf) * np.exp(-k_per_hour * xs)
    return path.tolist()

def eta_to_threshold(path: List[float], theta_min: float, dt_hours=1.0) -> Tuple[float, float]:
    """P50=Pth, P90=여유 잡은 값(보수적 보정)."""
    for i, v in enumerate(path, start=1):
        if v <= theta_min:
            p50 = i * dt_hours
            p90 = p50 * 0.8  # 보수적(조금 더 빠르게 경보) → 추후 교정
            return p50, p90
    return float('inf'), float('inf')
