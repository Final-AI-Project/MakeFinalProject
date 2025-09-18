# app/k_regressor.py
import numpy as np
from sklearn.linear_model import SGDRegressor

class KRegressor:
    """
    특성: [vpd, temp, rh, irradiance(결측=0), fan_on(0/1)]
    타깃: 최근 구간에서 추정된 k (per hour)
    """
    def __init__(self):
        self.model = SGDRegressor(loss="huber", alpha=1e-5, max_iter=1, learning_rate="invscaling", eta0=0.01, warm_start=True)
        self.is_fit = False

    def featurize(self, vpd, temp, rh, irr=0.0, fan_on=0.0):
        return np.array([[vpd, temp, rh, irr, fan_on]], dtype=float)

    def partial_fit(self, vpd, temp, rh, irr, fan_on, k_target):
        X = self.featurize(vpd, temp, rh, irr, fan_on)
        y = np.array([k_target], dtype=float)
        if not self.is_fit:
            self.model.partial_fit(X, y)
            self.is_fit = True
        else:
            self.model.partial_fit(X, y)

    def predict_k(self, vpd, temp, rh, irr=0.0, fan_on=0.0):
        if not self.is_fit:
            return None
        X = self.featurize(vpd, temp, rh, irr, fan_on)
        k = float(self.model.predict(X)[0])
        return float(np.clip(k, 0.003, 0.08))
