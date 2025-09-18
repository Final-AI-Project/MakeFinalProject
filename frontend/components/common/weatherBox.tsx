// components/common/weatherBox.tsx

import React, { useEffect, useMemo, useState } from "react";
import { View, Text, StyleSheet, ActivityIndicator, Image, Pressable } from "react-native";
import dayjs from "dayjs";

/** ========= 타입 ========= */
export type Period = "day" | "night";
export type StateClass = "clear" | "overcast" | "rain" | "rain_snow" | "snow" | "shower" | "etc";

export type WeatherBoxProps = {
	/** 공공데이터포털 KMA 키 (URL-인코딩된 값 권장: encodeURIComponent) */
	serviceKey: string;
	/** 위치: lat/lon 또는 nx/ny (라벨 포함). 미지정 시 서초구 기본 */
	location?: { lat: number; lon: number; label: string } | { nx: number; ny: number; label: string };
	/** 에러 시 "다시 시도" 버튼 표시 여부 (기본 true) */
	showRetryButton?: boolean;
};

const KMA_ENDPOINT = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst";

// PNG 아이콘 (프로젝트 구조: /assets/images/*)
const ICON_CLEAR_DAY	 = require("../../assets/images/clearDay.png");
const ICON_CLEAR_NIGHT = require("../../assets/images/clearNight.png");
const ICON_OVERCAST		= require("../../assets/images/overcast.png");
const ICON_RAIN				= require("../../assets/images/rain.png");
const ICON_RAIN_SNOW	 = require("../../assets/images/rain_snow.png");
const ICON_SNOW				= require("../../assets/images/snow.png");
const ICON_SHOWER			= require("../../assets/images/shower.png");
const ICON_ETC				 = require("../../assets/images/etc.png");

/** ========= 좌표 변환 (위/경도 <-> KMA 격자) ========= */
function dfs_xy_conv(mode: "toXY" | "toLL", v1: number, v2: number) {
	const RE = 6371.00877, GRID = 5.0, SLAT1 = 30.0, SLAT2 = 60.0, OLON = 126.0, OLAT = 38.0, XO = 43, YO = 136;
	const DEGRAD = Math.PI / 180.0, RADDEG = 180.0 / Math.PI;
	const re = RE / GRID, slat1 = SLAT1 * DEGRAD, slat2 = SLAT2 * DEGRAD, olon = OLON * DEGRAD, olat = OLAT * DEGRAD;
	let sn = Math.tan(Math.PI * 0.25 + slat2 * 0.5) / Math.tan(Math.PI * 0.25 + slat1 * 0.5);
	sn = Math.log(Math.cos(slat1) / Math.cos(slat2)) / Math.log(sn);
	let sf = Math.tan(Math.PI * 0.25 + slat1 * 0.5); sf = Math.pow(sf, sn) * Math.cos(slat1) / sn;
	let ro = Math.tan(Math.PI * 0.25 + olat * 0.5);	ro = re * sf / Math.pow(ro, sn);

	if (mode === "toXY") {
		const lat = v1, lon = v2;
		let ra = Math.tan(Math.PI * 0.25 + lat * DEGRAD * 0.5); ra = re * sf / Math.pow(ra, sn);
		let theta = lon * DEGRAD - olon; if (theta > Math.PI) theta -= 2 * Math.PI; if (theta < -Math.PI) theta += 2 * Math.PI;
		theta *= sn;
		const nx = Math.floor(ra * Math.sin(theta) + XO + 0.5);
		const ny = Math.floor(ro - ra * Math.cos(theta) + YO + 0.5);
		return { nx, ny };
	} else {
		const x = v1, y = v2;
		const xn = x - XO, yn = ro - y + YO;
		let ra = Math.sqrt(xn * xn + yn * yn); if (sn < 0.0) ra = -ra;
		let alat = Math.pow((re * sf / ra), (1.0 / sn)); alat = 2.0 * Math.atan(alat) - Math.PI * 0.5;
		let theta = 0.0;
		if (Math.abs(xn) <= 0.0) { theta = 0.0; }
		else { if (Math.abs(yn) <= 0.0) { theta = Math.PI * 0.5; if (xn < 0.0) theta = -theta; } else theta = Math.atan2(xn, yn); }
		const alon = theta / sn + olon;
		const lat = alat * RADDEG, lon = alon * RADDEG;
		return { lat, lon };
	}
}

/** ========= 유틸 ========= */
function getNearestBase() {
	// 02,05,08,11,14,17,20,23시 중 현재 시각 기준 가장 가까운 과거 발표시각
	const now = dayjs();
	const hhmm = now.format("HHmm");
	const slots = ["0200","0500","0800","1100","1400","1700","2000","2300"];
	let baseDate = now.format("YYYYMMDD");
	let baseTime = slots[0];
	for (const s of slots) if (parseInt(s) <= parseInt(hhmm)) baseTime = s;
	if (parseInt(hhmm) < 200) { baseDate = now.subtract(1, "day").format("YYYYMMDD"); baseTime = "2300"; }
	return { baseDate, baseTime };
}

function getDayNight(fcstTimeHHmm: string): Period {
	const h = parseInt(fcstTimeHHmm.slice(0,2), 10);
	return (h >= 6 && h < 19) ? "day" : "night";
}

function mapStateFromCodes(pty?: string, sky?: string): { label: string; stateClass: StateClass } {
	// PTY 우선
	if (pty && pty !== "0") {
		switch (pty) {
			case "1": return { label: "비",		 stateClass: "rain" };
			case "2": return { label: "비/눈",	stateClass: "rain_snow" };
			case "3": return { label: "눈",		 stateClass: "snow" };
			case "4": return { label: "소나기", stateClass: "shower" };
			case "5": return { label: "빗방울", stateClass: "rain" };
			case "6": return { label: "빗/눈날",stateClass: "rain_snow" };
			case "7": return { label: "눈날림", stateClass: "snow" };
			default:	return { label: "-",			stateClass: "etc" };
		}
	}
	// PTY=0 → SKY 기준
	if (sky === "1") return { label: "맑음", stateClass: "clear" };
	if (sky === "3" || sky === "4") return { label: "흐림", stateClass: "overcast" };
	return { label: "-", stateClass: "etc" };
}

function pickWeatherIcon(period?: Period, stateClass?: StateClass) {
	if (stateClass === "clear") return period === "night" ? ICON_CLEAR_NIGHT : ICON_CLEAR_DAY;
	switch (stateClass) {
		case "overcast":	return ICON_OVERCAST;
		case "rain":			return ICON_RAIN;
		case "rain_snow": return ICON_RAIN_SNOW;
		case "snow":			return ICON_SNOW;
		case "shower":		return ICON_SHOWER;
		case "etc":
		default:					return ICON_ETC;
	}
}

function pickContainerVariant(period: Period, stateClass: StateClass) {
	if (period === "night") return "night" as const;
	return stateClass === "clear" ? ("day" as const) : ("dayCloudy" as const);
}

/** ========= 데이터 모델 ========= */
type Box = {
	locationLabel: string;
	time: string;			 // HH:mm
	tempC?: string;
	stateText: string;
	stateClass: StateClass;
	period: Period;
};

/** ========= 메인 컴포넌트 ========= */
export default function WeatherBox(props: WeatherBoxProps) {
	const { serviceKey, showRetryButton = true } = props;

	// 기본: 서울 서초구
	const defaultLoc = useMemo(() => ({
		lat: 37.4836, lon: 127.0327, label: "서울시 - 서초구"
	}), []);
	const loc = props.location ?? defaultLoc;

	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [box, setBox] = useState<Box | null>(null);

	async function load() {
		try {
			setLoading(true); setError(null);

			// 좌표 준비 (nx, ny)
			let nx: number, ny: number, label: string;
			if ("nx" in loc && "ny" in loc) {
				nx = (loc as any).nx; ny = (loc as any).ny; label = (loc as any).label;
			} else {
				const { nx: _nx, ny: _ny } = dfs_xy_conv("toXY", (loc as any).lat, (loc as any).lon) as { nx: number; ny: number };
				nx = _nx; ny = _ny; label = (loc as any).label;
			}

			const { baseDate, baseTime } = getNearestBase();
			const params = new URLSearchParams({
				serviceKey,
				pageNo: "1",
				numOfRows: "1000",
				dataType: "JSON",
				base_date: baseDate,
				base_time: baseTime,
				nx: String(nx),
				ny: String(ny),
			});
			const url = `${KMA_ENDPOINT}?${params.toString()}`;
			const res = await fetch(url);
			if (!res.ok) throw new Error(`KMA ${res.status}`);

			const json = await res.json();
			const items = json?.response?.body?.items?.item ?? [];

			// 시간대별 카테고리 묶기
			const grouped = new Map<string, Record<string,string>>();
			for (const it of items as any[]) {
				const key = `${it.fcstDate}-${it.fcstTime}`;
				if (!grouped.has(key)) grouped.set(key, {});
				grouped.get(key)![it.category] = String(it.fcstValue);
			}
			const sorted = Array.from(grouped.entries()).sort((a,b)=>a[0].localeCompare(b[0]));

			// 현재 이후 첫 슬롯, 없으면 첫 슬롯
			const nowHHmm = dayjs().format("HHmm");
			const picked = sorted.find(([k]) => parseInt(k.split("-")[1]) >= parseInt(nowHHmm)) ?? sorted[0];
			if (!picked) throw new Error("예보 없음");

			const [key, vals] = picked;
			const [, hhmm] = key.split("-");
			const { label: stateText, stateClass } = mapStateFromCodes(vals["PTY"], vals["SKY"]);
			const period = getDayNight(hhmm);

			setBox({
				locationLabel: label,
				time: `${hhmm.slice(0,2)}:${hhmm.slice(2)}`,
				tempC: vals["TMP"],
				stateText,
				stateClass,
				period,
			});
		} catch (e: any) {
			setError(e?.message ?? String(e));
			setBox(null);
		} finally {
			setLoading(false);
		}
	}

	useEffect(() => { load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [serviceKey, JSON.stringify(loc)]);

	const variant = box ? pickContainerVariant(box.period, box.stateClass) : "day";
	const icon = pickWeatherIcon(box?.period, box?.stateClass);

	return (
		<View
			style={[
				styles.weatherBoxRoot,
				variant === "night" ? styles.weatherBoxRootNight
				: variant === "day" ? styles.weatherBoxRootDay
				: styles.weatherBoxRootDayCloudy
			]}
		>
			{loading && (
				<View style={styles.weatherBoxCenter}>
					<ActivityIndicator />
					<Text style={styles.weatherBoxDim}>불러오는 중…</Text>
				</View>
			)}
			{!loading && error && (
				<View style={styles.weatherBoxCenter}>
					<Text style={styles.weatherBoxError}>에러: {error}</Text>
					{showRetryButton && (
						<Pressable onPress={load} style={styles.weatherBoxButton}>
							<Text style={styles.weatherBoxButtonText}>다시 시도</Text>
						</Pressable>
					)}
				</View>
			)}
			{!loading && !error && box && (
				<>
					<Image source={icon} style={styles.weatherBoxIcon} resizeMode="contain" />
					<Text style={[
						styles.weatherBoxLocationLabel,
						box.period === "day" && styles.weatherBoxTextOnDay
					]}>
						{box.locationLabel}
					</Text>
					<Text style={[
						styles.weatherBoxStatus,
						box.period === "day" && styles.weatherBoxTextOnDay
					]}>
						{box.stateText} ({box.period === "day" ? "낮" : "밤"})
					</Text>
					<Text style={[
						styles.weatherBoxTemp,
						box.period === "day" && styles.weatherBoxTextOnDay
					]}>
						{box.tempC ?? "-"}℃
					</Text>
					<Text style={[
						styles.weatherBoxTime,
						box.period === "day" && styles.weatherBoxTextOnDay
					]}>
						예보시각 {box.time}
					</Text>
				</>
			)}
		</View>
	);
}

/** ========= 스타일 ========= */
const styles = StyleSheet.create({
	weatherBoxRoot: {
		minHeight: 150,
		borderRadius: 14,
		padding: 16,
		marginBottom: 12,
	},
	weatherBoxRootDay: {
		backgroundColor: "#abf5ff", borderWidth: 1, borderColor: "#dfe9f2",
	},
	weatherBoxRootDayCloudy: {
		backgroundColor: "#E6E9EF", borderWidth: 1, borderColor: "#cfd6df",
	},
	weatherBoxRootNight: {
		backgroundColor: "#151A22", borderWidth: 1, borderColor: "#293043",
		shadowColor: "#000", shadowOpacity: 0.25, shadowRadius: 8, shadowOffset: { width: 0, height: 3 }, elevation: 3,
	},

	weatherBoxCenter: { alignItems: "center", justifyContent: "center" },
	weatherBoxDim: { marginTop: 6, color: "#9aa4b2" },
	weatherBoxError: { color: "#ff6b6b", marginBottom: 8 },

	weatherBoxIcon: { width: 80, height: 80, position: "absolute", top: 12, right: 12, opacity: 0.95 },

	weatherBoxLocationLabel: { color: "#fff", fontSize: 16, fontWeight: "700" },
	weatherBoxStatus: { color: "#e7edf6", fontSize: 14, marginTop: 6 },
	weatherBoxTemp: { color: "#fff", fontSize: 36, fontWeight: "800", marginTop: 8 },
	weatherBoxTime: { color: "#c7d2e1", marginTop: 4, fontSize: 12 },

	weatherBoxTextOnDay: { color: "#0e1a2b" },

	weatherBoxButton: {
		marginTop: 12,
		paddingHorizontal: 14,
		paddingVertical: 10,
		borderRadius: 10,
		backgroundColor: "#1f6feb",
		alignItems: "center",
	},
	weatherBoxButtonText: { color: "white", fontWeight: "600" },
});

/* ============================================================================
	 ⬇️ 여기가 추가된 부분: 간단 날씨 API (맑음/흐림/비/눈)
	 ============================================================================ */
export async function fetchSimpleWeather(
	serviceKey: string,
	location: { lat: number; lon: number; label: string } | { nx: number; ny: number; label: string }
): Promise<"맑음" | "흐림" | "비" | "눈" | null> {
	try {
		// 좌표 준비
		let nx: number, ny: number;
		if ("nx" in location && "ny" in location) {
			nx = (location as any).nx; ny = (location as any).ny;
		} else {
			const p = dfs_xy_conv("toXY", (location as any).lat, (location as any).lon) as { nx: number; ny: number };
			nx = p.nx; ny = p.ny;
		}

		const { baseDate, baseTime } = getNearestBase();
		const params = new URLSearchParams({
			serviceKey,
			pageNo: "1",
			numOfRows: "1000",
			dataType: "JSON",
			base_date: baseDate,
			base_time: baseTime,
			nx: String(nx),
			ny: String(ny),
		});
		const url = `${KMA_ENDPOINT}?${params.toString()}`;
		const res = await fetch(url);
		if (!res.ok) throw new Error(`KMA ${res.status}`);
		const json = await res.json();
		const items = json?.response?.body?.items?.item ?? [];

		// 시간대별 묶기
		const grouped = new Map<string, Record<string, string>>();
		for (const it of items as any[]) {
			const key = `${it.fcstDate}-${it.fcstTime}`;
			if (!grouped.has(key)) grouped.set(key, {});
			grouped.get(key)![it.category] = String(it.fcstValue);
		}
		const sorted = Array.from(grouped.entries()).sort((a, b) => a[0].localeCompare(b[0]));

		const nowHHmm = dayjs().format("HHmm");
		const picked = sorted.find(([k]) => parseInt(k.split("-")[1]) >= parseInt(nowHHmm)) ?? sorted[0];
		if (!picked) return null;

		const [, vals] = picked;
		const { stateClass } = mapStateFromCodes(vals["PTY"], vals["SKY"]);

		// 간단 라벨로 축약
		if (stateClass === "clear") return "맑음";
		if (stateClass === "overcast") return "흐림";
		if (stateClass === "snow") return "눈";
		// rain / shower / rain_snow / etc → “비”로 통합
		return "비";
	} catch {
		return null;
	}
}
