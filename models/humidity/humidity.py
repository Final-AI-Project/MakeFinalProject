from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, confloat
import os, json, joblib, numpy as np

# input: json
# S_now: db 타임스탬프 상 최신 humidity 컬럼 값
# S_min_user: 품종 별 습도 최적값 테이블의 min_humid 값
# temp_C: 프론트 날씨api에서 받아온 기온 값
# hour_of_day: 현재 시각(지역시각 기준)
# S_ref: 포화 상태의 센서 퍼센트값 (생략 가능)

# output: json
# eta_h: 임계 도달까지 예상 시간
# loss_rate_per_h: 예측 건조 속도 (1/h)
# (제공에 불필요한 필드는 생략합니다.)


# ============ 설정 ============
EXPORT_DIR = "humidity"
MODEL_PATH = os.path.join(EXPORT_DIR, "model.joblib")
META_PATH  = os.path.join(EXPORT_DIR, "meta.json")
EPS = 1e-6

# ============ 로드 ============
try:
    model = joblib.load(MODEL_PATH)
    with open(META_PATH, "r") as f:
        META = json.load(f)
except Exception as e:
    raise RuntimeError(f"모델/메타 로드 실패: {e}")

FEAT_COLS      = META["feat_cols"]                          # 예: ["temp_C","Rstar","sin1","cos1"]
S_DRY          = float(META["S_DRY"])
S_REF_DEFAULT  = float(META["S_REF_DEFAULT"])
ETA_CAL        = META.get("eta_calibration") or None        # {"A":..., "B":...} 또는 None

# ============ 유틸 ============
def rstar_from_S(S: float, S_ref: float, S_dry: float = S_DRY, eps: float = EPS) -> float:
    return float(np.clip((float(S) - S_dry) / max(eps, float(S_ref) - S_dry), 0.0, 1.0))

def predict_loss_rate(temp_C: float, S_now: float, hour_of_day: float, S_ref: float) -> float:
    Rstar = rstar_from_S(S_now, S_ref)
    feats = []
    for c in FEAT_COLS:
        if c == "temp_C":
            feats.append(float(temp_C))
        elif c == "Rstar":
            feats.append(float(Rstar))
        elif c == "sin1":
            feats.append(np.sin(2*np.pi*(hour_of_day/24.0)))
        elif c == "cos1":
            feats.append(np.cos(2*np.pi*(hour_of_day/24.0)))
        else:
            raise ValueError(f"알 수 없는 피처명: {c}")
    r = float(model.predict(np.array(feats, dtype=float).reshape(1, -1))[0])
    return max(0.0, r)  # 음수 방지

def hours_until_threshold(S_now: float, S_min_user: float, temp_C: float,
                          hour_of_day: float, S_ref: float):
    R_now = rstar_from_S(S_now, S_ref)
    R_min = rstar_from_S(S_min_user, S_ref)
    if R_now <= R_min:
        return 0.0, R_now, R_min, 0.0
    r_hat = predict_loss_rate(temp_C, S_now, hour_of_day, S_ref)
    if r_hat <= 1e-5:
        return 240.0, R_now, R_min, r_hat  # 상한 캡
    eta = float((R_now - R_min) / r_hat)
    return eta, R_now, R_min, r_hat

def apply_eta_calibration(eta: float) -> tuple[float, bool]:
    if ETA_CAL is None:
        return float(eta), False
    a = float(ETA_CAL.get("A", 1.0)); b = float(ETA_CAL.get("B", 0.0))
    return max(0.0, a*eta + b), True

# ============ API ============
app = FastAPI(title="Soil Moisture ETA Server", version=str(META.get("version", 1)))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

class PredictReq(BaseModel):
    S_now:  confloat(ge=0.0, le=100.0) = Field(..., description="현재 센서 퍼센트(0~100)")
    S_min_user: confloat(ge=0.0, le=100.0) = Field(..., description="임계 센서 퍼센트(0~100)")
    temp_C: float = Field(..., description="현재 기온(°C)")
    hour_of_day: confloat(ge=0.0, le=24.0) = Field(..., description="현재 시각 0~24")
    S_ref: confloat(ge=0.0, le=100.0) | None = Field(None, description="상한 센서 퍼센트(생략 시 meta 기본값)")

class PredictResp(BaseModel):
    eta_h: float
    rstar_now: float
    rstar_min: float
    loss_rate_per_h: float
    used_S_ref: float
    calibrated: bool
