import csv, asyncio
from app.calibrator import RhCalibrator
from app.k_regressor import KRegressor
from app.features import calc_vpd
from app.model_store import upsert_model_state

LOCATION_ID = 1

async def main():
    # 1) RH 보정 초기화
    cal = RhCalibrator()
    with open("data/processed/calib_rh_sample.csv","r",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cal.update(float(r["outdoor_rh_pct"]), float(r["indoor_rh_pct"]))
    await upsert_model_state(LOCATION_ID, "rh_cal", {"a":cal.a,"b":cal.b,"lr":cal.lr})

    # 2) k 회귀 초기화
    reg = KRegressor()
    with open("data/processed/k_reg_samples.csv","r",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            vpd = float(r["vpd_kpa"])
            reg.partial_fit(vpd, float(r["temp_c"]), float(r["rh_pct"]),
                            float(r["irradiance_wpm2"]), float(r["fan_on"]),
                            float(r["k_per_hour"]))
    await upsert_model_state(LOCATION_ID, "k_reg", {
        "is_fit": reg.is_fit,
        "coef_": reg.model.coef_.tolist(),
        "intercept_": float(reg.model.intercept_),
    })
    print("bootstrap done.")

if __name__ == "__main__":
    asyncio.run(main())
