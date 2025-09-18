// app/(page)/medical.tsx
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
	View,
	Text,
	StyleSheet,
	Image,
	Pressable,
	Animated,
	FlatList,
	RefreshControl,
	ActivityIndicator,
	useColorScheme,
} from "react-native";
import Colors from "../../constants/Colors";
import arrowDownW from "../../assets/images/w_arrow_down.png";
import arrowDownD from "../../assets/images/d_arrow_down.png";

// ─────────────────────────────────────────────────────────────────────────────
// ① 타입 & 상수
// ─────────────────────────────────────────────────────────────────────────────
type Diagnosis = {
	id: string;
	photoUri?: string | null;
	nickname: string;
	diagnosedAt: string;   // "YYYY-MM-DD" 혹은 ISO
	diseaseName: string;
	details?: string;      // 펼침 영역에 표시할 상세 내용
};

// 환경변수: EXPO_PUBLIC_API_BASE_URL (예: http://192.168.0.5:8000)
// GET ${EXPO_PUBLIC_API_BASE_URL}/medical/diagnoses → Diagnosis[] 형태 기대
const API_BASE = process.env.EXPO_PUBLIC_API_BASE_URL;

// ─────────────────────────────────────────────────────────────────────────────
// ② 로컬 전용 아코디언 카드
// ─────────────────────────────────────────────────────────────────────────────
function DiseaseAccordionCardLocal({
	photoUri,
	nickname,
	diagnosedAt,
	diseaseName,
	children,
}: {
	photoUri?: string | null;
	nickname: string;
	diagnosedAt: string;
	diseaseName: string;
	children?: React.ReactNode;
}) {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];

	const [open, setOpen] = useState(false);
	const rotate = useRef(new Animated.Value(0)).current;
	const height = useRef(new Animated.Value(0)).current;
	const contentH = useRef(0);

	const arrowRotate = rotate.interpolate({
		inputRange: [0, 1],
		outputRange: ["0deg", "540deg"], // 펼침 시 1 → 540deg
	});

	const toggle = useCallback(() => {
		setOpen((prev) => {
			const next = !prev;

			// 회전
			if (next) rotate.setValue(0);
			Animated.timing(rotate, {
				toValue: next ? 1 : 0,
				duration: 260,
				useNativeDriver: true,
			}).start();

			// 높이
			Animated.timing(height, {
				toValue: next ? contentH.current : 0,
				duration: 220,
				useNativeDriver: false, // height는 false
			}).start();

			return next;
		});
	}, [rotate, height]);

	return (
		<View style={[styles.card, { borderColor: theme.border, backgroundColor: theme.bg }]}>
			{/* 상단(왼쪽 사진 + 오른쪽 상/하 텍스트) */}
			<View style={styles.row}>
				<View style={styles.left}>
					<View style={[styles.photo, { borderColor: theme.border }]}>
						{photoUri ? (
							<Image source={{ uri: photoUri }} style={{ width: "100%", height: "100%", borderRadius: 8 }} />
						) : (
							<View style={styles.placeholder}>
								<Text style={{ color: theme.text }}>사진</Text>
							</View>
						)}
					</View>
				</View>

				<View style={styles.right}>
					<View style={[styles.box, { borderColor: theme.border }]}>
						<Text numberOfLines={1} style={[styles.title, { color: theme.text }]}>
							{nickname} / {diagnosedAt}
						</Text>
					</View>
					<View style={[styles.box, { borderColor: theme.border, marginTop: 6 }]}>
						<Text numberOfLines={1} style={[styles.sub, { color: theme.text }]}>{diseaseName}</Text>
					</View>
				</View>
			</View>

			{/* 화살표 버튼 */}
			<Pressable onPress={toggle} style={styles.arrow} hitSlop={8}>
				<Animated.View style={{ transform: [{ rotate: arrowRotate }] }}>
					<Image
						source={scheme === "dark" ? arrowDownD : arrowDownW}
						style={styles.arrowImg}
						resizeMode="contain"
					/>
				</Animated.View>
			</Pressable>

			{/* 숨김 측정용: Animated 컨테이너 바깥에서 한 번 높이 측정 */}
			<View
				style={{ position: "absolute", left: -9999, opacity: 0 }}
				onLayout={(e) => {
					if (!contentH.current) contentH.current = e.nativeEvent.layout.height;
				}}
			>
				<View style={{ paddingTop: 8, paddingBottom: 12 }}>{children}</View>
			</View>

			{/* 아코디언 펼침 영역 */}
			<Animated.View style={{ height, overflow: "hidden" }}>
				<View style={{ paddingTop: 8, paddingBottom: 12 }}>{children}</View>
			</Animated.View>
		</View>
	);
}

// ─────────────────────────────────────────────────────────────────────────────
// ③ 페이지: 데이터 로딩 + 리스트 렌더
// ─────────────────────────────────────────────────────────────────────────────
export default function MedicalPage() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];

	const [data, setData] = useState<Diagnosis[]>([]);
	const [loading, setLoading] = useState(true);
	const [refreshing, setRefreshing] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const fetchData = useCallback(async () => {
		if (!API_BASE) {
			// 환경변수 미설정 시 안내 + 데모 데이터로 대체
			setError("EXPO_PUBLIC_API_BASE_URL이 설정되어 있지 않습니다.");
			setData(DEMO_DATA);
			setLoading(false);
			return;
		}

		try {
			setError(null);
			setLoading(true);
			const res = await fetch(`${API_BASE}/medical/diagnoses`, { method: "GET" });
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			const json: Diagnosis[] = await res.json();

			// 안전 장치: id가 없으면 생성
			const normalized = json.map((it, idx) => ({
				...it,
				id: it.id ?? `diag_${idx}`,
			}));

			setData(normalized);
		} catch (e: any) {
			setError(e?.message ?? "데이터 로딩 실패");
			// 실패 시 데모 데이터로라도 표시
			setData(DEMO_DATA);
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => {
		fetchData();
	}, [fetchData]);

	const onRefresh = useCallback(async () => {
		setRefreshing(true);
		await fetchData();
		setRefreshing(false);
	}, [fetchData]);

	const renderItem = useCallback(({ item }: { item: Diagnosis }) => {
		return (
			<View style={{ marginBottom: 14 }}>
				<DiseaseAccordionCardLocal
					photoUri={item.photoUri}
					nickname={item.nickname}
					diagnosedAt={formatDate(item.diagnosedAt)}
					diseaseName={item.diseaseName}
				>
					<Text style={{ color: theme.text, lineHeight: 20 }}>
						{item.details ?? "상세 정보가 없습니다."}
					</Text>
				</DiseaseAccordionCardLocal>
			</View>
		);
	}, [theme.text]);

	if (loading) {
		return (
			<View style={[styles.center, { backgroundColor: theme.bg }]}>
				<ActivityIndicator size="large" />
				<Text style={{ color: theme.text, marginTop: 8 }}>불러오는 중…</Text>
			</View>
		);
	}

	return (
		<View style={[styles.screen, { backgroundColor: theme.bg }]}>
			{error ? (
				<View style={[styles.errorBox, { borderColor: theme.border, backgroundColor: theme.bg }]}>
					<Text style={{ color: theme.text }}>⚠️ {error}</Text>
				</View>
			) : null}

			<FlatList
				data={data}
				keyExtractor={(item) => item.id}
				contentContainerStyle={{ padding: 16, paddingBottom: 24 }}
				renderItem={renderItem}
				refreshControl={
					<RefreshControl
						refreshing={refreshing}
						onRefresh={onRefresh}
						tintColor={scheme === "dark" ? "#fff" : "#000"}
					/>
				}
				ListEmptyComponent={
					<View style={[styles.center, { paddingTop: 40 }]}>
						<Text style={{ color: theme.text }}>표시할 진단이 없습니다.</Text>
					</View>
				}
			/>
		</View>
	);
}

// 날짜 포맷 보정(YYYY-MM-DD or ISO → YYYY-MM-DD)
function formatDate(s: string) {
	try {
		// 이미 YYYY-MM-DD면 그대로
		if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
		const d = new Date(s);
		if (Number.isNaN(d.getTime())) return s;
		const y = d.getFullYear();
		const m = String(d.getMonth() + 1).padStart(2, "0");
		const dd = String(d.getDate()).padStart(2, "0");
		return `${y}-${m}-${dd}`;
	} catch {
		return s;
	}
}

// 데모 데이터 (서버 미연결/실패 시 표시)
const DEMO_DATA: Diagnosis[] = [
	{
		id: "1",
		nickname: "초코(몬스테라)",
		diagnosedAt: "2025-09-18",
		diseaseName: "잎마름병(추정)",
		details: "가장자리 갈변/마름. 통풍 개선 및 관수 간격 조정 권장. 필요시 주1회 살균제.",
		photoUri: undefined,
	},
	{
		id: "2",
		nickname: "토리(올리브나무)",
		diagnosedAt: "2025-09-17",
		diseaseName: "진딧물",
		details: "잎 뒷면 점착 물질·흑색곰팡이 동반 가능. 미지근한 물로 세척 후 살충비누 도포.",
		photoUri: undefined,
	},
];

// ─────────────────────────────────────────────────────────────────────────────
// ④ 스타일
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
	screen: { flex: 1 },
	center: { flex: 1, alignItems: "center", justifyContent: "center" },

	card: { borderWidth: 1, borderRadius: 12, padding: 12 },
	row: { flexDirection: "row" },
	left: { marginRight: 10, justifyContent: "center" },
	photo: {
		width: 72,
		height: 72,
		borderWidth: 1,
		borderRadius: 8,
		overflow: "hidden",
		backgroundColor: "#ddd",
		alignItems: "center",
		justifyContent: "center",
	},
	placeholder: { flex: 1, alignItems: "center", justifyContent: "center" },
	right: { flex: 1 },
	box: { borderWidth: 1, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 8 },
	title: { fontSize: 15, fontWeight: "600" },
	sub: { fontSize: 15, fontWeight: "500" },
	arrow: {
		alignSelf: "center",
		marginTop: 8,
		padding: 6,
		width: 36,
		height: 36,
		alignItems: "center",
		justifyContent: "center",
	},
	arrowImg: { width: 24, height: 24 },
	errorBox: {
		margin: 16,
		padding: 12,
		borderRadius: 10,
		borderWidth: 1,
	},
});
