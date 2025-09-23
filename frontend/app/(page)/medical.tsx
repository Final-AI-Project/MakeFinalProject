// app/(page)/medical.tsx
import React, {
	useCallback,
	useEffect,
	useMemo,
	useRef,
	useState,
} from "react";
import {
	View,
	Text,
	StyleSheet,
	Image,
	Pressable,
	Animated,
	RefreshControl,
	ActivityIndicator,
	useColorScheme,
	SectionList,
	Easing,
} from "react-native";
import Colors from "../../constants/Colors";
import { useRouter } from "expo-router";
import arrowDownW from "../../assets/images/w_arrow_down.png";
import arrowDownD from "../../assets/images/d_arrow_down.png";
import medicalSetting from "../../assets/images/medical_setting.png";
import { getToken } from "../../libs/auth";

// ─────────────────────────────────────────────────────────────────────────────
// 타입
// ─────────────────────────────────────────────────────────────────────────────
type Candidate = {
	id: string;
	code?: string;
	name: string;
	desc?: string;
	confidence?: number; // 0~1
};

type Diagnosis = {
	id: string;
	photoUri?: string | null;
	nickname: string;
	diagnosedAt: string; // "YYYY-MM-DD" or ISO
	diseaseName: string; // 대표 1순위 병명
	details?: string;
	candidates?: Candidate[]; // 상위 후보 (1~3개 렌더)
};

type SpeciesSection = { title: string; data: Diagnosis[] };

// ─────────────────────────────────────────────────────────────────────────────
// 유틸/환경
// ─────────────────────────────────────────────────────────────────────────────
const API_BASE = process.env.EXPO_PUBLIC_API_BASE_URL;

/**
 * ▷▷▷ TODO(REAL_API):
 *  1) 운영 전환 시 아래 플래그를 이렇게 맞춰라
 *     - FORCE_DEMO = false
 *     - USE_DEMO_ON_ERROR = false  (원한다면 true 유지해서 에러시 데모로 대체)
 *     - USE_DEMO_WHEN_EMPTY = false(원한다면 true 유지해서 빈 응답시 데모로 대체)
 */
const FORCE_DEMO = false; // true: 항상 DEMO_DATA만 사용 (개발/시연용)
const USE_DEMO_ON_ERROR = true; // true: API 에러 시 DEMO_DATA로 대체
const USE_DEMO_WHEN_EMPTY = true; // true: API가 빈 배열이면 DEMO_DATA로 대체

function formatDate(s: string) {
	try {
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
const todayStr = new Date().toISOString().slice(0, 10);

// 닉네임에서 품종 파싱: "초코(몬스테라)" -> "몬스테라"
// 괄호가 없으면 닉네임 전체를 품종으로 간주
function extractSpecies(nickname: string) {
	const m = nickname.match(/(?:.*)\(([^)]+)\)\s*$/);
	return (m?.[1] ?? nickname ?? "기타").trim();
}

// 리스트를 품종별로 그룹화
function groupBySpecies(list: Diagnosis[]): SpeciesSection[] {
	const map = new Map<string, Diagnosis[]>();
	for (const it of list) {
		const sp = extractSpecies(it.nickname);
		if (!map.has(sp)) map.set(sp, []);
		map.get(sp)!.push(it);
	}
	return Array.from(map.entries())
		.sort((a, b) => a[0].localeCompare(b[0]))
		.map(([title, data]) => ({ title, data }));
}

// ─────────────────────────────────────────────────────────────────────────────
// 페이지
// ─────────────────────────────────────────────────────────────────────────────
export default function MedicalPage() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const router = useRouter();

	const [data, setData] = useState<Diagnosis[]>([]);
	const [loading, setLoading] = useState(true);
	const [refreshing, setRefreshing] = useState(false);
	const [error, setError] = useState<string | null>(null);

	// 아코디언 상태
	const openMap = useRef<Record<string, boolean>>({});
	const rotateMap = useRef<Record<string, Animated.Value>>({});
	const heightMap = useRef<Record<string, Animated.Value>>({});
	const contentHMap = useRef<Record<string, number>>({});
	const thumbMap = useRef<Record<string, Animated.Value>>({});

	const getThumb = (id: string) =>
		(thumbMap.current[id] ??= new Animated.Value(1));
	const getRotate = (id: string) =>
		(rotateMap.current[id] ??= new Animated.Value(0));
	const getHeight = (id: string) =>
		(heightMap.current[id] ??= new Animated.Value(0));
	const getContentH = (id: string) => contentHMap.current[id] ?? 0;
	const setContentH = (id: string, h: number) => {
		contentHMap.current[id] = h;
		if (openMap.current[id]) getHeight(id).setValue(h);
	};
	const getOpen = (id: string) => !!openMap.current[id];
	const setOpen = (id: string, val: boolean) => (openMap.current[id] = val);

	// 데이터 로드
	const fetchData = useCallback(async () => {
		/**
		 * ▷▷▷ TODO(REAL_API):
		 *  - 운영에서 "데모 먼저 보여주기"가 싫다면, 아래 setData(DEMO_DATA)를 삭제해라.
		 *  - 개발/시연에선 즉시 DEMO 보이게 두는 게 편함.
		 */
		setData(DEMO_DATA);

		// 강제 데모 모드
		if (FORCE_DEMO) {
			setError(null);
			setLoading(false);
			return;
		}

		if (!API_BASE) {
			setError(
				"EXPO_PUBLIC_API_BASE_URL이 설정되어 있지 않습니다. (데모 데이터 표시)"
			);
			setLoading(false);
			return;
		}

		try {
			setError(null);
			setLoading(true);

			// 실제 백엔드 API 호출
			const token = await getToken();
			if (!token) {
				throw new Error("로그인이 필요합니다.");
			}

			const res = await fetch(`${API_BASE}/medical/diagnoses`, {
				method: "GET",
				headers: {
					Authorization: `Bearer ${token}`,
					"Content-Type": "application/json",
				},
			});

			if (!res.ok) throw new Error(`HTTP ${res.status}`);

			const raw = await res.json().catch(() => []);
			const arr: Diagnosis[] = Array.isArray(raw) ? raw : [];

			if (arr.length === 0) {
				// 빈 응답 처리
				if (USE_DEMO_WHEN_EMPTY) {
					// 데모 유지
					setError(null);
				} else {
					setData([]); // 진짜로 "비어 있음"을 보여주고 싶을 때
				}
			} else {
				const normalized = arr.map((it, idx) => ({
					...it,
					id: it.id ?? `diag_${idx}`,
					diagnosedAt: formatDate(it.diagnosedAt),
				}));
				setData(normalized);
			}
		} catch (e: any) {
			// 에러 처리
			if (USE_DEMO_ON_ERROR) {
				setError((e?.message ?? "데이터 로딩 실패") + " (데모 데이터 표시)");
				// 데모 유지
			} else {
				setError(e?.message ?? "데이터 로딩 실패");
				setData([]); // 진짜 에러면 빈 화면을 원할 때
			}
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

	const sections = useMemo(() => groupBySpecies(data), [data]);
	
	// 왼쪽 하단 이미지 둥둥 애니메이션 (y축 보빙)
	const bob = useRef(new Animated.Value(0)).current;
	useEffect(() => {
		const loop = Animated.loop(
			Animated.sequence([
				// 천천히 2시(약 60deg)까지
				Animated.timing(bob, {
					toValue: 1,
					duration: 2000,
					easing: Easing.out(Easing.quad),
					useNativeDriver: true,
				}),
				// 빠르게 원위치(0deg)로 복귀
				Animated.timing(bob, {
					toValue: 0,
					duration: 280,
					easing: Easing.in(Easing.cubic),
					useNativeDriver: true,
				}),
			])
		);
		loop.start();
		return () => loop.stop();
	}, [bob]);

	// 각도로 변환 (0deg ↔ 60deg)
	const bobRotate = bob.interpolate({
		inputRange: [0, 1],
		outputRange: ["0deg", "10deg"],
	});

	// 아이템 렌더
	const renderItem = useCallback(
		({ item }: { item: Diagnosis }) => {
			const rotate = getRotate(item.id);
			const height = getHeight(item.id);

			// 썸네일 애니메이션 (열리면 숨김)
			const thumb = getThumb(item.id);
			const thumbW = thumb.interpolate({
				inputRange: [0, 1],
				outputRange: [0, 72],
			});
			const thumbMR = thumb.interpolate({
				inputRange: [0, 1],
				outputRange: [0, 10],
			});

			const arrowRotate = rotate.interpolate({
				inputRange: [0, 1],
				outputRange: ["0deg", "540deg"],
			});

			const toggle = () => {
				const next = !getOpen(item.id);
				setOpen(item.id, next);

				if (next) rotate.setValue(0);
				Animated.timing(rotate, {
					toValue: next ? 1 : 0,
					duration: 260,
					useNativeDriver: true,
				}).start();

				Animated.timing(thumb, {
					toValue: next ? 0 : 1,
					duration: 200,
					useNativeDriver: false,
				}).start();

				const targetH = next ? getContentH(item.id) : 0;
				Animated.timing(height, {
					toValue: targetH,
					duration: 220,
					useNativeDriver: false,
				}).start();
			};

			return (
				<View style={{ marginBottom: 14 }}>
					<View
						style={[
							styles.card,
							{ borderColor: theme.border, backgroundColor: theme.bg },
						]}
					>
						<Pressable onPress={toggle}>
							<View style={styles.row}>
								{/* 왼쪽 썸네일: width/marginRight 애니메이션으로 숨김 */}
								<Animated.View
									style={[
										styles.left,
										{ width: thumbW, marginRight: thumbMR, overflow: "hidden" },
									]}
								>
									<View style={[styles.photo, { borderColor: theme.border }]}>
										{item.photoUri ? (
											<Image
												source={{ uri: item.photoUri }}
												style={{ width: "100%", height: "100%", borderRadius: 8 }}
											/>
										) : (
											<View style={styles.placeholder}>
												<Text style={{ color: theme.text }}>사진</Text>
											</View>
										)}
									</View>
								</Animated.View>

								<View style={styles.right}>
									<View style={[styles.box, { borderColor: theme.border }]}>
										<Text
											numberOfLines={1}
											style={[styles.title, { color: theme.text }]}
										>
											{item.nickname} / {formatDate(item.diagnosedAt)}
										</Text>
									</View>
									<View
										style={[
											styles.box,
											{ borderColor: theme.border, marginTop: 6 },
										]}
									>
										<Text numberOfLines={1} style={[styles.sub, { color: theme.text }]}>
											{item.diseaseName}
										</Text>
									</View>
								</View>
							</View>
						</Pressable>

						<Animated.View style={{ height: height, overflow: "hidden" }}>
							<View
								style={styles.accWrap}
								onLayout={(e) => {
									const h = e.nativeEvent.layout.height;
									setContentH(item.id, h);
								}}
							>
								{/* 1) 큰 사진 박스 */}
								<View style={[styles.accPhotoBox, { borderColor: theme.border }]}>
									{item.photoUri ? (
										<Image
											source={{ uri: item.photoUri }}
											style={{ width: "100%", height: "100%" }}
											resizeMode="cover"
										/>
									) : (
										<Text style={[styles.accPhotoText, { color: theme.text }]}>
											사진
										</Text>
									)}
								</View>

								{/* 2) 별명/날짜 표시 */}
								<View
									style={[
										styles.accRow,
										{ borderColor: theme.border, backgroundColor: theme.bg },
									]}
								>
									<Text style={[styles.accRowText, { color: theme.text }]}>
										내 식물 별명 / 진단 날짜(당일): {item.nickname} / {todayStr}
									</Text>
								</View>

								{/* 3) 후보 병충해 1~3 */}
								{(item.candidates ?? [])
									.slice(0, 3)
									.map((d, i) => (
										<View
											key={d.id}
											style={[
												styles.accRow,
												{ borderColor: theme.border, backgroundColor: theme.bg },
											]}
										>
											<Text style={[styles.accRowText, { color: theme.text }]}>
												{i + 1}. {d.name} : {d.desc ?? "-"}
												{typeof d.confidence === "number"
													? ` (${Math.round(d.confidence * 100)}%)`
													: ""}
											</Text>
										</View>
									))}
							</View>
						</Animated.View>

						<Pressable onPress={toggle} style={styles.arrow} hitSlop={8}>
							<Animated.View style={{ transform: [{ rotate: arrowRotate }] }}>
								<Image
									source={scheme === "dark" ? arrowDownD : arrowDownW}
									style={styles.arrowImg}
									resizeMode="contain"
								/>
							</Animated.View>
						</Pressable>
					</View>
				</View>
			);
		},
		[scheme, theme]
	);

	if (loading) {
		return (
			<View style={[styles.center, { backgroundColor: theme.bg }]}>
				<ActivityIndicator size="large" />
				<Text style={{ color: theme.text, marginTop: 8 }}>불러오는 중…</Text>
			</View>
		);
	}

	return (
		<View style={[styles.container, { backgroundColor: theme.bg }]}>
			<SectionList
				sections={sections}
				keyExtractor={(item) => item.id}
				renderItem={renderItem}
				renderSectionHeader={() => null}
				contentContainerStyle={{ padding: 16, paddingBottom: 24 }}
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

			{/* ✅ 고정 FAB: 병충해 진단 상세로 이동 */}
			<Pressable
				onPress={() => router.push("/(page)/(stackless)/medical-detail")}
				style={({ pressed }) => [
					styles.fab,
					{
						opacity: pressed ? 0.85 : 1,
						backgroundColor: theme.primary ?? "#00c73c",
					},
				]}
				android_ripple={{ color: "#ffffff22", borderless: false }}
				hitSlop={8}
				accessibilityRole="button"
				accessibilityLabel="병충해 진단하기로 이동"
			>
				<Text style={styles.fabPlus}>+</Text>
				<Text style={styles.fabLabel}>진단하기</Text>
			</Pressable>

			{/* ⬅️ 왼쪽 하단 고정: medicalSetting 이미지 버튼 */}
			<View style={styles.leftDeco} pointerEvents="none">
				<Animated.Image
					source={medicalSetting}
					style={[styles.leftDecoImg, { transform: [{ rotate: bobRotate }] }]}
					resizeMode="contain"
				/>
			</View>

		</View>
	);
}

// ─────────────────────────────────────────────────────────────────────────────
// DEMO_DATA
// ─────────────────────────────────────────────────────────────────────────────
const DEMO_DATA: Diagnosis[] = [
	{
		id: "diag_001",
		nickname: "초코(몬스테라)",
		diagnosedAt: "2025-09-18T10:20:00+09:00",
		diseaseName: "잎마름병",
		details: "엽연 갈변과 건조 흔적이 관찰됨. 통풍 부족 및 과습 의심.",
		photoUri: "https://picsum.photos/seed/plant1/480/360",
		candidates: [
			{
				id: "cand_001",
				code: "leaf_blight",
				name: "잎마름병",
				desc: "가장자리 갈변·마름",
				confidence: 0.87,
			},
			{
				id: "cand_002",
				code: "powdery_mildew",
				name: "흰가루병",
				desc: "백색 분말성 균총",
				confidence: 0.08,
			},
			{
				id: "cand_003",
				code: "scale_insect",
				name: "깍지벌레",
				desc: "줄기·잎의 흰 혹",
				confidence: 0.05,
			},
		],
	},
	{
		id: "diag_002",
		nickname: "토리(올리브나무)",
		diagnosedAt: "2025-09-17",
		diseaseName: "진딧물",
		details: "잎 뒷면 점착 물질과 굴절광 반사. 그을음병 동반 가능.",
		photoUri: "https://picsum.photos/seed/plant2/480/360",
		candidates: [
			{
				id: "cand_004",
				code: "aphid",
				name: "진딧물",
				desc: "연한 새순 부위 군집",
				confidence: 0.76,
			},
			{
				id: "cand_005",
				code: "spider_mite",
				name: "응애",
				desc: "미세한 점상 피해",
				confidence: 0.14,
			},
			{
				id: "cand_006",
				code: "thrips",
				name: "총채벌레",
				desc: "은백색 변색 스트리크",
				confidence: 0.1,
			},
		],
	},
	{
		id: "diag_003",
		nickname: "토리(올리브나무)",
		diagnosedAt: "2025-09-17",
		diseaseName: "진딧물",
		details: "잎 뒷면 점착 물질과 굴절광 반사. 그을음병 동반 가능.",
		photoUri: "https://picsum.photos/seed/plant3/480/360",
		candidates: [
			{
				id: "cand_007",
				code: "aphid",
				name: "진딧물",
				desc: "연한 새순 부위 군집",
				confidence: 0.76,
			},
			{
				id: "cand_008",
				code: "spider_mite",
				name: "응애",
				desc: "미세한 점상 피해",
				confidence: 0.14,
			},
			{
				id: "cand_009",
				code: "thrips",
				name: "총채벌레",
				desc: "은백색 변색 스트리크",
				confidence: 0.1,
			},
		],
	},
];

// ─────────────────────────────────────────────────────────────────────────────
// 스타일
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
	container: { flex: 1, paddingBottom: 120 },
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
	box: {
		borderWidth: 1,
		borderRadius: 8,
		paddingHorizontal: 10,
		paddingVertical: 8,
	},
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

	accWrap: { paddingTop: 8, paddingBottom: 12 },
	accPhotoBox: {
		borderWidth: 1,
		borderRadius: 8,
		height: 160,
		alignItems: "center",
		justifyContent: "center",
		marginBottom: 10,
		backgroundColor: "#eee",
	},
	accPhotoText: { fontSize: 14 },
	accRow: {
		borderWidth: 1,
		borderRadius: 8,
		paddingHorizontal: 12,
		paddingVertical: 10,
		marginBottom: 8,
	},
	accRowText: { fontSize: 14, lineHeight: 20 },

	sectionHeader: {
		borderWidth: 1,
		borderRadius: 8,
		paddingHorizontal: 10,
		paddingVertical: 6,
		marginBottom: 10,
	},
	sectionHeaderText: {
		fontSize: 13,
		fontWeight: "700",
		opacity: 0.8,
	},

	fab: {
		position: "absolute",
		right: 18,
		bottom: 85,
		borderRadius: 28,
		paddingHorizontal: 16,
		height: 56,
		minWidth: 56,
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "center",

		// iOS shadow
		shadowColor: "#000",
		shadowOpacity: 0.18,
		shadowRadius: 6,
		shadowOffset: { width: 0, height: 2 },
		// Android shadow
		elevation: 3,
	},
	fabPlus: {
		fontSize: 22,
		fontWeight: "800",
		color: "#fff",
		marginRight: 8,
		lineHeight: 22,
	},
	fabLabel: {
		fontSize: 15,
		fontWeight: "700",
		color: "#fff",
	},
	leftDeco: {
		position: "absolute",
		left: 8,
		bottom: 60,
		width: 64,
		height: 64,
		alignItems: "center",
		justifyContent: "center",
	},
	leftDecoImg: {
		width: 150,
		height: 150,
	},
});
