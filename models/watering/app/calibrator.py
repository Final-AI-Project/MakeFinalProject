# app/calibrator.py
import numpy as np

class RhCalibrator:
    """
    y = a * outdoor_rh + b  (online 업데이트)
    기본값: a=0.8, b=5 → '실내 RH가 대체로 낮다' 가정
    """
    def __init__(self, a: float = 0.8, b: float = 5.0, lr: float = 1e-3):
        self.a = a
        self.b = b
        self.lr = lr

    def predict(self, outdoor_rh: float) -> float:
        return float(np.clip(self.a * outdoor_rh + self.b, 15.0, 85.0))

    def update(self, outdoor_rh: float, indoor_rh_obs: float):
        """실내 센서가 있을 때만 호출. 온라인 경사 하강."""
        yhat = self.predict(outdoor_rh)
        err = indoor_rh_obs - yhat
        self.a += self.lr * err * outdoor_rh
        self.b += self.lr * err
