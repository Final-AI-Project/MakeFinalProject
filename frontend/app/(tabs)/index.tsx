// app/(tabs)/index.tsx
import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, StyleSheet, Dimensions, ActivityIndicator, Pressable, Image } from 'react-native';
import Carousel from 'react-native-reanimated-carousel';
import dayjs from 'dayjs';

const { width } = Dimensions.get('window');

/** 🔑 기상청 인증키: 공공데이터포털 발급키를 URL-인코딩해서 넣어주세요. */
const KMA_SERVICE_KEY = "GTr1cI7Wi0FRbOTFBaUzUCzCDP4OnyyEmHnn11pxCUC5ehG5bQnbyztgeydnOWz1O04tjw1SE5RsX8RNo6XCgQ==";

/** 기상청 단기예보 엔드포인트 */
const KMA_ENDPOINT = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst";

/** (서울 서초구 중심 좌표 예시) — 실시간 위치 불필요, 고정 지역 사용 */
const FIXED_LOCATION = {
    label: "서울시 - 서초구",
    lat: 37.4836,  // 서초구청 인근 위도
    lon: 127.0327, // 서초구청 인근 경도
};

/** 위/경도 ↔ KMA 격자 변환 (Lambert Conformal Conic DFS) */
function dfs_xy_conv(mode: "toXY" | "toLL", v1: number, v2: number) {
    const RE = 6371.00877, GRID = 5.0, SLAT1 = 30.0, SLAT2 = 60.0, OLON = 126.0, OLAT = 38.0, XO = 43, YO = 136;
    const DEGRAD = Math.PI / 180.0, RADDEG = 180.0 / Math.PI;
    const re = RE / GRID, slat1 = SLAT1 * DEGRAD, slat2 = SLAT2 * DEGRAD, olon = OLON * DEGRAD, olat = OLAT * DEGRAD;
    let sn = Math.tan(Math.PI * 0.25 + slat2 * 0.5) / Math.tan(Math.PI * 0.25 + slat1 * 0.5);
    sn = Math.log(Math.cos(slat1) / Math.cos(slat2)) / Math.log(sn);
    let sf = Math.tan(Math.PI * 0.25 + slat1 * 0.5);
    sf = Math.pow(sf, sn) * Math.cos(slat1) / sn;
    let ro = Math.tan(Math.PI * 0.25 + olat * 0.5);
    ro = re * sf / Math.pow(ro, sn);

    if (mode === "toXY") {
        const lat = v1, lon = v2;
        let ra = Math.tan(Math.PI * 0.25 + (lat) * DEGRAD * 0.5);
        ra = re * sf / Math.pow(ra, sn);
        let theta = lon * DEGRAD - olon;
        if (theta > Math.PI) theta -= 2.0 * Math.PI;
        if (theta < -Math.PI) theta += 2.0 * Math.PI;
        theta *= sn;
        const nx = Math.floor(ra * Math.sin(theta) + XO + 0.5);
        const ny = Math.floor(ro - ra * Math.cos(theta) + YO + 0.5);
        return { nx, ny };
    } else {
        const x = v1, y = v2;
        const xn = x - XO, yn = ro - y + YO;
        let ra = Math.sqrt(xn * xn + yn * yn);
        if (sn < 0.0) ra = -ra;
        let alat = Math.pow((re * sf / ra), (1.0 / sn));
        alat = 2.0 * Math.atan(alat) - Math.PI * 0.5;
        let theta = 0.0;
        if (Math.abs(xn) <= 0.0) {
            theta = 0.0;
        } else {
            if (Math.abs(yn) <= 0.0) {
                theta = Math.PI * 0.5;
                if (xn < 0.0) theta = -theta;
            } else theta = Math.atan2(xn, yn);
        }
        const alon = theta / sn + olon;
        const lat = alat * RADDEG;
        const lon = alon * RADDEG;
        return { lat, lon };
    }
}

/** 단기예보 base_time(02,05,08,11,14,17,20,23시) 중 현재 시각 기준 가장 가까운 과거 시각 선택 */
function getNearestBase() {
    const now = dayjs();
    const hhmm = now.format("HHmm");
    const slots = ["0200","0500","0800","1100","1400","1700","2000","2300"]; // 단기예보 발표시각(1일 8회) :contentReference[oaicite:2]{index=2}
    let baseDate = now.format("YYYYMMDD");
    let baseTime = slots[0];
    for (const s of slots) if (parseInt(s) <= parseInt(hhmm)) baseTime = s;
    if (parseInt(hhmm) < 200) { // 00:00~01:59 → 전일 23:00
        baseDate = now.subtract(1, "day").format("YYYYMMDD");
        baseTime = "2300";
    }
    return { baseDate, baseTime };
}

/** 낮/밤 표시 **/
const ICON_SUN  = require('../../assets/images/sun.png');
const ICON_MOON = require('../../assets/images/moon.png');
const ICON_CLOUD = require('../../assets/images/overcast.png');
function getDayNight(fcstTime: string) {
	const hour = parseInt(fcstTime.slice(0,2), 10);
	return hour >= 6 && hour < 20
		? { period: "day" as const, label: "낮" as const }
		: { period: "night" as const, label: "밤" as const };
}
// 낮/밤 + 날씨별 아이콘 선택
	function pickWeatherIcon(period?: 'day' | 'night', stateClass?: StateClass) {
		if (period === 'night') return ICON_MOON; // 밤은 달로 고정

		// 낮일 때:
		switch (stateClass) {
			case 'clear':     return ICON_SUN;   // 맑음 → 해
			case 'overcast':
			case 'rain':
			case 'rain_snow':
			case 'snow':
			case 'shower':    return ICON_CLOUD; // 낮 + 구름/비/눈/소나기 → 구름
			default:          return ICON_SUN;   // 기본값
		}
}



/** 상태 매핑 (문구 + 스타일 클래스) */
function mapStateFromCodes(pty?: string, sky?: string) {
    if (!pty && !sky) return { label: "-", stateClass: "etc" };
    if (pty && pty !== "0") {
        switch (pty) {
            case "1": return { label: "비", stateClass: "rain" };
            case "2": return { label: "비/눈", stateClass: "rain_snow" };
            case "3": return { label: "눈", stateClass: "snow" };
            case "4": return { label: "소나기", stateClass: "shower" };
            case "5": return { label: "빗방울", stateClass: "rain" };
            case "6": return { label: "빗방울/눈날림", stateClass: "rain_snow" };
            case "7": return { label: "눈날림", stateClass: "snow" };
            default:  return { label: `강수(${pty})`, stateClass: "etc" };
        }
    }
    // PTY=0 → SKY 기준
    switch (sky) {
        case "1": return { label: "맑음", stateClass: "clear" };
        case "4": return { label: "흐림", stateClass: "overcast" };
        default:  return { label: "-", stateClass: "etc" };
    }
}

/** 화면 상태 타입 */
type TodayBox = {
    locationLabel: string;   // "서울시 - 서초구"
    time: string;            // 예보시각(HH:mm)
    tempC?: string;          // ℃
    stateText: string;       // 상태 한글 ("맑음", "비" 등)
    stateClass: string;      // 스타일 클래스("clear" | "rain" | ...)
	label?: "낮" | "밤";
  	period?: "day" | "night";
};

export default function Home() {
    // 기존 슬라이드/인디케이터 유지  :contentReference[oaicite:3]{index=3}
    const [activeIndex, setActiveIndex] = useState(0);
    const slides = useMemo(() => ([
        { key: '1', label: 'Hello Carousel', bg: '#9DD6EB' },
        { key: '2', label: 'Beautiful', bg: '#97CAE5' },
        { key: '3', label: 'And simple', bg: '#92BBD9' },
    ]), []);

    // 날씨 박스 상태
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [box, setBox] = useState<TodayBox | null>(null);

    async function loadWeather() {
        setLoading(true); setError(null);
        try {
            // 고정 위치 → 격자 변환
            const { nx, ny } = dfs_xy_conv("toXY", FIXED_LOCATION.lat, FIXED_LOCATION.lon) as { nx: number; ny: number };

            // 발표시각 결정(가장 가까운 과거 발표시각)  :contentReference[oaicite:4]{index=4}
            const { baseDate, baseTime } = getNearestBase();

            // API 호출
            const params = new URLSearchParams({
                serviceKey: KMA_SERVICE_KEY,
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
            if (!res.ok) throw new Error(`KMA 응답 오류 ${res.status}`);
            const json = await res.json();
            const items = json?.response?.body?.items?.item ?? [];

            // 동일 fcstDate/time 별로 카테고리 묶기
            const grouped = new Map<string, Record<string,string>>();
            for (const it of items as any[]) {
                const key = `${it.fcstDate}-${it.fcstTime}`;
                if (!grouped.has(key)) grouped.set(key, {});
                grouped.get(key)![it.category] = String(it.fcstValue);
            }
            const sorted = Array.from(grouped.entries()).sort((a,b)=>a[0].localeCompare(b[0]));

            // 현재 시각 이후 첫 슬롯 선택, 없으면 첫 슬롯
            const nowHHmm = dayjs().format("HHmm");
            let picked = sorted.find(([k]) => parseInt(k.split("-")[1]) >= parseInt(nowHHmm)) ?? sorted[0];

            if (picked) {
                const [key, vals] = picked;
                const [, hhmm] = key.split("-");
                const { label, stateClass } = mapStateFromCodes(vals["PTY"], vals["SKY"]);
                setBox({
                    locationLabel: FIXED_LOCATION.label,
                    time: `${hhmm.slice(0,2)}:${hhmm.slice(2)}`,
                    tempC: vals["TMP"],
                    stateText: label,
                    stateClass,
					...getDayNight(hhmm),
                });
            } else {
                setBox(null);
            }
        } catch (e: any) {
            setError(e?.message ?? String(e));
            setBox(null);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => { loadWeather(); }, []);





	useEffect(() => {
		// 프로젝트에서 쓰는 상태 클래스 집합에 맞춰 매핑
		const labelMap = {
			clear: "맑음",
			overcast: "흐림",
			rain: "비",
			rain_snow: "비/눈",
			snow: "눈",
			shower: "소나기",
			etc: "-",
		} as const;

		type Period = "day" | "night";
		type StateClass = keyof typeof labelMap;

		// 📌 (낮/밤, 날씨) 시나리오 적용
		function setWeatherScenario(period: Period, stateClass: StateClass, opts?: {
			tempC?: string | number;
			time?: string;              // "14:00" 형식 추천 (없으면 기존 유지)
			locationLabel?: string;     // 지역명 바꾸고 싶을 때만
			stateText?: string;         // 라벨 커스텀 시
		}) {
			setBox(prev => {
				if (!prev) return prev;
				return {
					...prev,
					period,
					stateClass,
					tempC: opts?.tempC !== undefined ? String(opts.tempC) : prev.tempC,
					time: opts?.time ?? prev.time,
					locationLabel: opts?.locationLabel ?? prev.locationLabel,
					stateText: opts?.stateText ?? labelMap[stateClass],
				};
			});
			console.log("[scenario]", { period, stateClass, ...opts });
		}

		// ✅ 바로 쓰기 편한 단축함수
		function setDayWeather(stateClass: StateClass, opts?: Parameters<typeof setWeatherScenario>[2]) {
			setWeatherScenario("day", stateClass, opts);
		}
		function setNightWeather(stateClass: StateClass, opts?: Parameters<typeof setWeatherScenario>[2]) {
			setWeatherScenario("night", stateClass, opts);
		}

		// 콘솔에서 호출할 수 있도록 전역 등록
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		(globalThis as any).setWeatherScenario = setWeatherScenario;
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		(globalThis as any).setDayWeather = setDayWeather;
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		(globalThis as any).setNightWeather = setNightWeather;

		console.log(
			'%cready: setDayWeather("clear") / setNightWeather("rain") / setWeatherScenario("night","snow",{tempC:0})',
			'background:#222;color:#0f0;padding:2px 6px;border-radius:4px;'
		);

		return () => {
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			delete (globalThis as any).setWeatherScenario;
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			delete (globalThis as any).setDayWeather;
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			delete (globalThis as any).setNightWeather;
		};
	}, []);













    return (
        <View style={styles.container}>
            {/* ✅ 날씨 박스: 고정 지역(서울시 - 서초구), 상태, 기온, 상태 클래스에 따른 스타일 */}
            <View
				style={[
					styles.weatherBoxRoot,
					box?.period === 'night' ? styles.weatherBoxRootNight : styles.weatherBoxRootDay,
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
                        <Pressable onPress={loadWeather} style={styles.weatherBoxButton}><Text style={styles.weatherBoxButtonText}>다시 시도</Text></Pressable>
                    </View>
                )}
                {!loading && !error && box && (
                    <View
						style={[
							box?.period === 'night' ? styles.weatherBoxRootNight : styles.weatherBoxRootDay
						]}
					>
						{box?.period === 'night' ? (
							<Image source={ICON_MOON} style={styles.weatherBoxIcon} resizeMode="contain" />
						) : (
							<Image source={ICON_SUN}  style={styles.weatherBoxIcon} resizeMode="contain" />
						)}
						<Image
							source={pickWeatherIcon(box?.period, box?.stateClass)}
							style={styles.weatherBoxIcon}
							resizeMode="contain"
						/>
                        <Text style={[styles.weatherBoxLocationLabel, box?.period === 'day' && styles.weatherBoxTextOnDay]}>
							{box.locationLabel}
						</Text>

						{/* ⬇ 상태 문구 (낮/밤 표기 포함) */}
						<Text style={[styles.weatherBoxStatus, box?.period === 'day' && styles.weatherBoxTextOnDay]}>
							{box.stateText} ({box?.period === 'day' ? '낮' : '밤'})
						</Text>

						{/* ⬇ 온도 */}
						<Text style={[styles.weatherBoxTemp, box?.period === 'day' && styles.weatherBoxTextOnDay]}>
							{box.tempC ?? '-'}℃
						</Text>

						{/* ⬇ 예보 시각 */}
						<Text style={[styles.weatherBoxTime, box?.period === 'day' && styles.weatherBoxTextOnDay]}>
							예보시각 {box.time}
						</Text>
                    </View>
                )}
                {!loading && !error && !box && (
                    <Text style={styles.weatherBoxDim}>표시할 예보가 없습니다.</Text>
                )}
            </View>

            {/* ⬇️ 아래는 네가 주었던 캐러셀 뼈대 그대로 유지  :contentReference[oaicite:5]{index=5} */}
            <View style={styles.carouselRoot}>
                <Carousel
                    loop
                    width={width - 32}
                    height={250}
                    data={slides}
                    scrollAnimationDuration={700}
                    onSnapToItem={(index) => setActiveIndex(index)}
                    renderItem={({ item }) => (
                        <View style={[styles.carouselSlide, { backgroundColor: item.bg }]}>
                            <Text style={styles.carouselSlideText}>{item.label}</Text>
                        </View>
                    )}
                />
                <View style={styles.carouselDots}>
                    {slides.map((_, i) => (
                        <View key={i} style={[styles.carouselDot, i === activeIndex && styles.carouselDotActive]} />
                    ))}
                </View>
            </View>
        </View>
    );
}

/** 기본 스타일 + 상태 클래스 테마 */
const styles = StyleSheet.create({
    container: {
        flex: 1,
        alignItems: 'stretch',
        backgroundColor: '#f0f0f0',
        padding:24,
    },
    weatherBoxRoot: {
        minHeight: 150,
        borderRadius: 16,
        padding:16,
		marginBottom:15,
    },
	weatherBoxRootDay: {
		backgroundColor: '#00e1ff',
	},
	weatherBoxRootNight: {
		backgroundColor: '#1a2430',
		elevation: 3,
	},
	weatherBoxTextOnDay: {},
    weatherBoxCenter: { alignItems: 'center', justifyContent: 'center' },
    weatherBoxDim: { marginTop: 6, color: '#9aa4b2' },
    weatherBoxError: { color: '#ff6b6b', marginBottom: 8 },
	weatherBoxButton: {
		marginTop: 12,
		borderRadius: 10,
		backgroundColor: '#1f6feb',
		alignItems: 'center',
	},
	weatherBoxButtonText: {
		color: 'white',
		fontWeight: '600',
	},
    weatherBoxLocationLabel: { color: '#fff', fontSize: 16, fontWeight: '700' },
    weatherBoxStatus: { color: '#e7edf6', fontSize: 14, marginTop: 6 },
    weatherBoxStateClass: { color: '#9aa4b2', fontSize: 12 },
    weatherBoxTemp: { color: '#fff', fontSize: 36, fontWeight: '800', marginTop: 8 },
    weatherBoxTime: { color: '#fff', marginTop: 4, fontSize: 12 },
	weatherBoxIcon: {
		width:90,
		height:90,
		position: 'absolute',
		top: 8,
		right: 8,
	},

    carouselRoot: {
        height: 250,
        alignSelf: 'stretch',
        marginTop: 4,
        marginBottom: 8,
        justifyContent: 'center',
        alignItems: 'center',
    },
    carouselSlide: {
        flex: 1,
        borderRadius:16,
        justifyContent: 'center',
        alignItems: 'center',
    },
    carouselSlideText: { color: '#fff', fontSize: 28, fontWeight: 'bold' },
    carouselDots: { position: 'absolute', bottom: 8, flexDirection: 'row', gap: 6 },
    carouselDot: { width: 6, height: 6, borderRadius: 4, backgroundColor: '#cfcfcf' },
    carouselDotActive: { backgroundColor: '#333' },

});

// 낮/밤 + 날씨별 배경색(루트에 추가로 머지)
const dayWeatherBgTheme: Record<StateClass, object> = {
  clear:     { backgroundColor: '#00e1ff' },
  overcast:  { backgroundColor: '#E6E9EF' },
  rain:      { backgroundColor: '#DDE9F6' },
  rain_snow: { backgroundColor: '#DCE6F2' },
  snow:      { backgroundColor: '#EEF3F9' },
  shower:    { backgroundColor: '#D9E8FB' },
  etc:       { }, // 추가 없음
};

const nightWeatherBgTheme: Record<StateClass, object> = {
  clear:     { backgroundColor: '#1a2430' },
  overcast:  { backgroundColor: '#151A22' },
  rain:      { backgroundColor: '#0F1A2A' },
  rain_snow: { backgroundColor: '#102034' },
  snow:      { backgroundColor: '#172234' },
  shower:    { backgroundColor: '#10223A' },
  etc:       { }, // 추가 없음
};