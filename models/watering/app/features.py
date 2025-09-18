# app/features.py
import numpy as np

def calc_vpd(temp_c: float, rh_pct: float) -> float:
    """증기압차(VPD, kPa). 간단 Tetens."""
    es = 0.6108 * np.exp((17.27 * temp_c) / (temp_c + 237.3))
    ea = es * (rh_pct / 100.0)
    return max(0.0, es - ea)

def rolling_k_estimate(soil_series, dt_hours=1.0):
    """
    최근 구간 지수건조 k 추정(최소제곱).
    soil_series: 최근 N개 soil_moist_pct(내림차순 시간)
    """
    y = np.array(soil_series, dtype=float)
    if len(y) < 5 or np.any(y <= 0):
        return None
    # 로그차분 근사: y_t ≈ y_inf + (y0 - y_inf)*exp(-k t)
    # y_inf를 0~min(y) 근방으로 가정하는 간이식(보정은 추후)
    y_inf = max(0.0, y.min() - 1.0)
    x = np.arange(len(y)) * dt_hours
    z = np.log(np.clip(y - y_inf, 1e-6, None))
    # 선형회귀: z = a - k t
    A = np.vstack([np.ones_like(x), -x]).T
    coef, *_ = np.linalg.lstsq(A, z, rcond=None)
    k = max(0.0, coef[1])
    return k, y_inf
