# app/service.py
"""
FastAPI 서비스 엔드포인트 (운영중 학습 포함 버전)

포함 기능
- /predict                 : JSON(history/forecast/meta) 기반 예측
- /predict/{plant_id}      : DB의 장소/실내외 + Provider 예보 기반 예측
- /ingest/indoor_rh        : 실외→실내 RH 보정(온라인 학습)
- /ingest/soil             : soil 로그 기반 k-회귀(온라인 학습)
- startup/shutdown         : aiomysql 풀 초기화/종료
"""
from typing import List, Tuple, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ----- 내부 모듈 -----
from .schemas import (
    PredictRequest,
    PredictResponse,
    SensorPoint,
    PotMeta,
    WeatherPoint,
)
from .features import calc_vpd, rolling_k_estimate
from .baseline import rule_of_thumb_k, forecast_soil_path
from .eta import compute_eta_from_path
from .calibrator import RhCalibrator
from .k_regressor import KRegressor
from .config import settings
from .db import (
    init_db_pool,
    close_db_pool,
    get_plant_meta,
    get_latest_indoor_rh,
)
from .model_store import upsert_model_state, load_model_state
from .providers.weather_provider import get_weather_provider
# ====== Geocoding ======
from .providers.geocoder import get_geocoder
from .geo_cache import geocode_cache_get, geocode_cache_put
from .db import insert_location

# ----- 앱 및 Provider -----
app = FastAPI(title="PlantCare ETA API (with Online Learning)")
weather_provider = get_weather_provider()

# ----- 직렬화/역직렬화 유틸 -----
def rhcal_to_dict(cal: RhCalibrator) -> dict:
    return {"a": cal.a, "b": cal.b, "lr": cal.lr}

def rhcal_from_dict(d: Optional[dict]) -> RhCalibrator:
    if not d:
        return RhCalibrator()
    return RhCalibrator(a=float(d.get("a", 0.8)),
                        b=float(d.get("b", 5.0)),
                        lr=float(d.get("lr", 1e-3)))

def kreg_to_dict(reg: KRegressor) -> dict:
    d = {"is_fit": reg.is_fit}
    if reg.is_fit:
        import numpy as np
        d["coef_"] = getattr(reg.model, "coef_", np.zeros(5)).tolist()
        d["intercept_"] = float(getattr(reg.model, "intercept_", 0.0))
    return d

def kreg_from_dict(d: Optional[dict]) -> KRegressor:
    import numpy as np
    reg = KRegressor()
    if d and d.get("is_fit"):
        reg.is_fit = True
        reg.model.coef_ = np.array(d["coef_"], dtype=float)
        reg.model.intercept_ = float(d["intercept_"])
    return reg

# ----- DB 풀 라이프사이클 -----
@app.on_event("startup")
async def on_startup():
    await init_db_pool()

@app.on_event("shutdown")
async def on_shutdown():
    await close_db_pool()


# ======================================================================
# 1) 기존 JSON 기반 예측
# ======================================================================
@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    """
    클라이언트가 history/forecast/meta를 직접 보내는 간단 모드.
    - history: 시간 오름차순 권장
    - forecast: 있으면 첫 시점의 VPD로 k 보정, 없으면 보수적 기본값 사용
    """
    history = sorted(req.history, key=lambda x: x.ts)
    last_soil = history[-1].soil_moist_pct

    # 최근 k 추정 (롤링)
    recent = [p.soil_moist_pct for p in history[-12:]]  # 최근 12시간 가정
    est = rolling_k_estimate(recent, dt_hours=1.0)

    theta_inf = max(0.0, min(last_soil - 10.0, req.meta.theta_min_pct - 2.0))
    k_est = None
    if est:
        k_est, theta_inf_est = est
        theta_inf = max(0.0, min(theta_inf, theta_inf_est + 1.0))

    # 예보가 있으면 첫 시점으로 k 보정, 없으면 기본값
    if req.forecast:
        ft0 = sorted(req.forecast, key=lambda x: x.ts)[0]
        vpd0 = calc_vpd(ft0.outdoor_temp_c, ft0.outdoor_rh_pct)
        k_use = k_est or rule_of_thumb_k(vpd0)
        horizon = max(1, len(req.forecast))
    else:
        k_use = k_est or 0.02
        horizon = 72

    # 향후 경로 & ETA
    path = forecast_soil_path(last_soil, theta_inf, k_use, horizon_hours=horizon)
    eta_p50, eta_p90 = compute_eta_from_path(path, req.meta.theta_min_pct)

    return PredictResponse(eta_hours_p50=eta_p50,
                           eta_hours_p90=eta_p90,
                           path=path)


# ======================================================================
# 2) DB/위치 기반 예측 (운영중 학습 상태 사용)
# ======================================================================
@app.post("/predict/{plant_id}", response_model=PredictResponse)
async def predict_by_plant(plant_id: int, req: PredictRequest) -> PredictResponse:
    """
    DB의 장소/실내외 정보를 사용하여 서버가 직접 예보를 가져오고(Provider),
    실내면 RH 보정을 적용한 뒤 기존 파이프라인으로 ETA를 계산합니다.
    - req.history: 센서에서 온 최근 로그(필수)
    - forecast: 본 엔드포인트에서는 무시(서버가 채움)
    """
    meta_db = await get_plant_meta(plant_id)
    if not meta_db:
        raise HTTPException(status_code=404, detail="plant not found")

    lat, lon = float(meta_db["lat"]), float(meta_db["lon"])
    is_indoor = bool(meta_db["is_indoor"])
    theta_min = float(meta_db["theta_min_pct"])
    location_id = int(meta_db["location_id"])

    # 장소별 모델 상태 로드
    rh_state = await load_model_state(location_id, "rh_cal")
    rh_cal = rhcal_from_dict(rh_state)

    k_state = await load_model_state(location_id, "k_reg")
    k_reg = kreg_from_dict(k_state)

    # 위치 기반 예보 조회
    forecast = await weather_provider.get_forecast(lat, lon, settings.kma_hours)

    # 실내면 RH 보정 적용 (실외 RH -> 실내 RH)
    if is_indoor and forecast:
        adjusted: List[WeatherPoint] = []
        for w in forecast:
            rh_in = rh_cal.predict(w.outdoor_rh_pct)
            adjusted.append(WeatherPoint(
                ts=w.ts,
                outdoor_temp_c=w.outdoor_temp_c,
                outdoor_rh_pct=rh_in,  # 보정된 '실내' RH를 같은 필드에 탑재
                irradiance_wpm2=w.irradiance_wpm2
            ))
        forecast = adjusted

    # 기존 파이프라인 재사용
    history = sorted(req.history, key=lambda x: x.ts)
    if not history:
        raise HTTPException(status_code=400, detail="history is required")

    last_soil = history[-1].soil_moist_pct

    # 최근 k 추정
    recent = [p.soil_moist_pct for p in history[-12:]]
    est = rolling_k_estimate(recent, dt_hours=1.0)

    theta_inf = max(0.0, min(last_soil - 10.0, theta_min - 2.0))
    k_est = None
    if est:
        k_est, theta_inf_est = est
        theta_inf = max(0.0, min(theta_inf, theta_inf_est + 1.0))

    # k 회귀가 학습되어 있으면 사용 → 없으면 k_est → 없으면 규칙
    if forecast:
        ft0 = forecast[0]
        vpd0 = calc_vpd(ft0.outdoor_temp_c, ft0.outdoor_rh_pct)
        k_hat = k_reg.predict_k(vpd0, ft0.outdoor_temp_c, ft0.outdoor_rh_pct) if k_reg.is_fit else None
        k_use = k_hat or k_est or rule_of_thumb_k(vpd0)
        horizon = len(forecast)
    else:
        # Provider가 빈 응답일 때도 안전하게 동작
        k_use = k_est or 0.02
        horizon = 72

    path = forecast_soil_path(last_soil, theta_inf, k_use, horizon_hours=horizon)
    eta_p50, eta_p90 = compute_eta_from_path(path, theta_min)

    return PredictResponse(eta_hours_p50=eta_p50,
                           eta_hours_p90=eta_p90,
                           path=path)


# ======================================================================
# 3) 운영중 온라인 학습 엔드포인트
# ======================================================================

# --- 3-1) 실내 RH 보정 업데이트 (실외/실내 RH 한 쌍) ---
class IndoorRhIn(BaseModel):
    location_id: int
    ts: int
    outdoor_rh_pct: float = Field(ge=0, le=100)
    indoor_rh_pct: float = Field(ge=0, le=100)

@app.post("/ingest/indoor_rh")
async def ingest_indoor_rh(body: IndoorRhIn):
    """
    실외 RH(예보/관측)과 실내 RH(센서)를 매칭하여 보정계수 a,b를 1스텝 업데이트.
    장소별 모델 상태는 model_state 테이블에 JSON으로 저장됩니다.
    """
    rh_state = await load_model_state(body.location_id, "rh_cal")
    cal = rhcal_from_dict(rh_state)
    cal.update(body.outdoor_rh_pct, body.indoor_rh_pct)
    await upsert_model_state(body.location_id, "rh_cal", rhcal_to_dict(cal))
    return {"ok": True, "a": cal.a, "b": cal.b}


# --- 3-2) soil 로그 → k 회귀 업데이트 ---
class SoilIn(BaseModel):
    location_id: int
    ts: int
    soil_moist_pct: float = Field(ge=0, le=100)
    outdoor_temp_c: float
    outdoor_rh_pct: float
    irradiance_wpm2: float = 0.0
    fan_on: float = 0.0  # (선택) 환기/팬 이벤트 플래그

# 최근 soil N개 조회 (간단 레포)
from .db import _pool  # 연결 풀 직접 사용 (간단 구현)
async def fetch_recent_soil(location_id: int, n: int):
    q = """
      SELECT soil_moist_pct
      FROM soil_logs
      WHERE location_id=%s
      ORDER BY ts_ms DESC
      LIMIT %s
    """
    async with _pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(q, (location_id, n))
            rows = await cur.fetchall()
            rows.reverse()
            return [{"soil_moist_pct": r[0]} for r in rows]

@app.post("/ingest/soil")
async def ingest_soil(body: SoilIn):
    """
    1) soil 로그 1건을 저장
    2) 최근 윈도우(예: 12개)로 지수건조 k를 추정
    3) k를 타깃으로 KRegressor.partial_fit 수행
    4) 장소별 회귀계수(coef_, intercept_)를 model_state에 저장
    """
    # 0) 저장
    await init_db_pool()
    async with _pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO soil_logs(location_id, ts_ms, soil_moist_pct) VALUES(%s,%s,%s)",
                (body.location_id, body.ts, body.soil_moist_pct)
            )

    # 1) 최근 시계열로 k 추정
    rows = await fetch_recent_soil(body.location_id, n=12)  # 최근 12시간 가정
    series = [r["soil_moist_pct"] for r in rows]
    est = rolling_k_estimate(series, dt_hours=1.0)
    if not est:
        return {"ok": True, "msg": "not enough points for k estimate yet"}
    k_target, _theta_inf = est

    # 2) 장소별 k-회귀 모델 로드
    k_state = await load_model_state(body.location_id, "k_reg")
    reg = kreg_from_dict(k_state)

    # 3) 피처 계산 + partial_fit
    vpd = calc_vpd(body.outdoor_temp_c, body.outdoor_rh_pct)
    reg.partial_fit(vpd, body.outdoor_temp_c, body.outdoor_rh_pct,
                    body.irradiance_wpm2, body.fan_on, k_target)

    # 4) 저장
    await upsert_model_state(body.location_id, "k_reg", kreg_to_dict(reg))
    return {"ok": True, "k_target": k_target, "is_fit": reg.is_fit}

geocoder = get_geocoder()

class GeocodeIn(BaseModel):
    query: str = Field(..., min_length=2, description="사용자 입력 장소 문자열")
    is_indoor: bool = True
    save_location: bool = False   # True면 locations에 저장
    name: str | None = None       # 저장 시 표시명(없으면 query)

class GeocodeOut(BaseModel):
    lat: float
    lon: float
    address: str
    provider: str
    location_id: int | None = None

@app.post("/geocode", response_model=GeocodeOut)
async def geocode_api(body: GeocodeIn):
    # 1) 캐시 조회
    cached = await geocode_cache_get(body.query)
    if cached:
        lat, lon = cached["lat"], cached["lon"]
        address, provider = cached["address"], cached["provider"]
    else:
        # 2) 실제 지오코딩 호출
        res = await geocoder.geocode(body.query)
        if not res:
            raise HTTPException(status_code=404, detail="geocode not found")
        lat, lon = float(res["lat"]), float(res["lon"])
        address, provider = res.get("address", body.query), res.get("provider", "UNKNOWN")
        # 3) 캐시 저장
        await geocode_cache_put(body.query, {"lat": lat, "lon": lon, "address": address, "provider": provider})

    loc_id = None
    if body.save_location:
        nm = body.name or body.query
        loc_id = await insert_location(nm, lat, lon, body.is_indoor)

    return GeocodeOut(lat=lat, lon=lon, address=address, provider=provider, location_id=loc_id)

# 장소 등록(지오코딩 포함) 바로 쓰고 싶다면 별도 단축 엔드포인트도 제공
@app.post("/locations/register", response_model=GeocodeOut)
async def register_location(body: GeocodeIn):
    if not body.save_location:
        object.__setattr__(body, "save_location", True)
    return await geocode_api(body)