# app/eta.py
from typing import List, Tuple

def compute_eta_from_path(path: List[float], theta_min: float) -> Tuple[float, float]:
    # 단순 위임: 향후 불확실성/PI를 여기에서 통합 관리
    from .baseline import eta_to_threshold
    return eta_to_threshold(path, theta_min)
