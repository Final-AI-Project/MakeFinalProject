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
	diagnosedAt: string;		// "YYYY-MM-DD" or ISO
	diseaseName: string;		// 대표 1순위 병명
	details?: string;
	candidates?: Candidate[]; // 상위 후보 (1~3개 렌더)
};

// ─────────────────────────────────────────────────────────────────────────────
// 유틸/환경
// ─────────────────────────────────────────────────────────────────────────────
const API_BASE = process.env.EXPO_PUBLIC_API_BASE_URL;

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

// ─────────────────────────────────────────────────────────────────────────────
// 페이지 (분리 컴포넌트 없이 전체 처리)
// ─────────────────────────────────────────────────────────────────────────────
export default function MedicalPage() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];

	// 데이터
	const [data, setData] = useState<Diagnosis[]>([]);
	const [loading, setLoading] = useState(true);
	const [refreshing, setRefreshing] = useState(false);
	const [error, setError] = useState<string | null>(null);

	// 목록 스크롤 & 위치 맵
	const listRef = useRef<FlatList<Diagnosis>>(null);
	const yMap = useRef<Record<string, number>>({});					// 아이템 카드의 시작 Y(리스트 기준)
	const imgYOffsetMap = useRef<Record<string, number>>({}); // 아코디언 내부 '큰 사진'의 Y(콘텐츠 내부 기준)

	// 아코디언 상태/애니메이션 맵
	const openMap = useRef<Record<string, boolean>>({});
	const rotateMap = useRef<Record<string, Animated.Value>>({});
	const heightMap = useRef<Record<string, Animated.Value>>({});
	const contentHMap = useRef<Record<string, number>>({});
	const isMineMap = useRef<Record<string, boolean>>({}); // “내 식물인지” 토글

	const getRotate = (id: string) => (rotateMap.current[id] ??= new Animated.Value(0));
	const getHeight = (id: string) => (heightMap.current[id] ??= new Animated.Value(0));
	const getContentH = (id: string) => contentHMap.current[id] ?? 0;
	const setContentH = (id: string, h: number) => {
		if (!contentHMap.current[id]) contentHMap.current[id] = h;
	};
	const getOpen = (id: string) => !!openMap.current[id];
	const setOpen = (id: string, val: boolean) => (openMap.current[id] = val);
	const getIsMine = (id: string) => (id in isMineMap.current ? isMineMap.current[id] : true);
	const toggleIsMine = (id: string) => (isMineMap.current[id] = !getIsMine(id));

	// 데이터 로드
	const fetchData = useCallback(async () => {
		if (!API_BASE) {
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
			const normalized = json.map((it, idx) => ({
				...it,
				id: it.id ?? `diag_${idx}`,
				diagnosedAt: formatDate(it.diagnosedAt),
			}));
			setData(normalized);
		} catch (e: any) {
			setError(e?.message ?? "데이터 로딩 실패");
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

	// 아이템 렌더
	const renderItem = useCallback(
		({ item }: { item: Diagnosis }) => {
			const rotate = getRotate(item.id);
			const height = getHeight(item.id);
			const arrowRotate = rotate.interpolate({
				inputRange: [0, 1],
				outputRange: ["0deg", "540deg"],
			});

			const candidates = (item.candidates ?? []).slice(0, 3);

			const onRegister = () => {
				// TODO: 서버 등록 API 연결
				console.log("등록", {
					id: item.id,
					isMine: getIsMine(item.id),
					nickname: item.nickname,
					date: todayStr,
					candidates,
				});
			};
			const onCancel = () => {
				// TODO: 원하는 동작
				console.log("취소", { id: item.id });
			};

			const toggle = () => {
				const next = !getOpen(item.id);
				setOpen(item.id, next);

				// 회전
				if (next) rotate.setValue(0);
				Animated.timing(rotate, {
					toValue: next ? 1 : 0,
					duration: 260,
					useNativeDriver: true,
				}).start();

				// 높이
				Animated.timing(height, {
					toValue: next ? getContentH(item.id) : 0,
					duration: 220,
					useNativeDriver: false,
				}).start();

				// 펼칠 때: 200ms 지연 후, 아코디언 내부 '큰 사진'을 화면 상단으로 스크롤
				if (next) {
					const baseY = yMap.current[item.id] ?? 0;					 // 카드 시작 Y
					const innerY = imgYOffsetMap.current[item.id] ?? 0; // 콘텐츠 내부 큰 사진 Y
					const pad = 16;																		 // contentContainerStyle padding 보정
					const target = Math.max(baseY + innerY - pad, 0);

					setTimeout(() => {
						listRef.current?.scrollToOffset({ offset: target, animated: true });
					}, 200); // ← 요청: 0.2초 딜레이
				}
			};

			return (
				<View
					style={{ marginBottom: 14 }}
					onLayout={(e) => {
						// 아이템 카드의 시작 Y
						yMap.current[item.id] = e.nativeEvent.layout.y;
					}}
				>
					<View style={[styles.card, { borderColor: theme.border, backgroundColor: theme.bg }]}>
						{/* 상단 요약 (사진 + 텍스트 2줄) */}
						<Pressable onPress={toggle}>
							<View style={styles.row}>
								{/* 왼쪽 사진(작은 썸네일) */}
								<View style={styles.left}>
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
								</View>

								{/* 오른쪽 상/하 텍스트 */}
								<View style={styles.right}>
									<View style={[styles.box, { borderColor: theme.border }]}>
										<Text numberOfLines={1} style={[styles.title, { color: theme.text }]}>
											{item.nickname} / {formatDate(item.diagnosedAt)}
										</Text>
									</View>
									<View style={[styles.box, { borderColor: theme.border, marginTop: 6 }]}>
										<Text numberOfLines={1} style={[styles.sub, { color: theme.text }]}>
											{item.diseaseName}
										</Text>
									</View>
								</View>
							</View>
						</Pressable>

						{/* 숨김 측정용: 아코디언 실제 구조와 동일하게 렌더해서 높이/이미지 오프셋 측정 */}
						<View
							style={{ position: "absolute", left: -9999, opacity: 0 }}
							onLayout={(e) => {
								if (!contentHMap.current[item.id]) {
									setContentH(item.id, e.nativeEvent.layout.height);
								}
							}}
						>
							<View style={styles.accWrap}>
								{/* 1) 큰 사진 박스 (숨김측정용 래퍼로 감싸서 내부 Y 저장) */}
								<View
									onLayout={(e) => {
										// 아코디언 콘텐츠 내부에서 '큰 사진'이 시작되는 Y값
										imgYOffsetMap.current[item.id] = e.nativeEvent.layout.y;
									}}
								>
									<View style={[styles.accPhotoBox, { borderColor: theme.border }]}>
										{item.photoUri ? (
											<Image
												source={{ uri: item.photoUri }}
												style={{ width: "100%", height: "100%" }}
												resizeMode="cover"
											/>
										) : (
											<Text style={[styles.accPhotoText, { color: theme.text }]}>사진</Text>
										)}
									</View>
								</View>

								{/* 2) 내 식물인지 선택(표시용) */}
								<View style={[styles.accRow, { borderColor: theme.border, backgroundColor: theme.bg }]}>
									<Text style={[styles.accRowText, { color: theme.text }]}>
										내 식물인지 선택 ({getIsMine(item.id) ? "내꺼로 저장" : "다른 식물이면 등록 안 함"})
									</Text>
								</View>

								{/* 3) 별명/날짜 선택(표시용) */}
								<View style={[styles.accRow, { borderColor: theme.border, backgroundColor: theme.bg }]}>
									<Text style={[styles.accRowText, { color: theme.text }]}>
										내 식물 별명 선택 / 진단 날짜(당일): {item.nickname} / {todayStr}
									</Text>
								</View>

								{/* 4) 후보 병충해 1~3 */}
								{(item.candidates ?? []).slice(0, 3).map((d, i) => (
									<View
										key={d.id}
										style={[styles.accRow, { borderColor: theme.border, backgroundColor: theme.bg }]}
									>
										<Text style={[styles.accRowText, { color: theme.text }]}>
											{i + 1}. {d.name} : {d.desc ?? "-"}
											{typeof d.confidence === "number" ? ` (${Math.round(d.confidence * 100)}%)` : ""}
										</Text>
									</View>
								))}

								{/* 5) 등록 / 취소 (표시용) */}
								<View style={styles.accActions}>
									<View style={[styles.accBtn, styles.accBtnPrimary]}>
										<Text style={styles.accBtnPrimaryText}>등록(일단 여기 위치)</Text>
									</View>
									<View style={[styles.accBtn, styles.accBtnGhost]}>
										<Text style={[styles.accBtnGhostText, { color: theme.text }]}>취소</Text>
									</View>
								</View>
							</View>
						</View>

						{/* 아코디언 펼침 영역 */}
						<Animated.View style={{ height: height, overflow: "hidden" }}>
							<View style={styles.accWrap}>
								{/* 1) 큰 사진 박스 */}
								<View style={[styles.accPhotoBox, { borderColor: theme.border }]}>
									{item.photoUri ? (
										<Image
											source={{ uri: item.photoUri }}
											style={{ width: "100%", height: "100%" }}
											resizeMode="cover"
										/>
									) : (
										<Text style={[styles.accPhotoText, { color: theme.text }]}>사진</Text>
									)}
								</View>

								{/* 2) 내 식물인지 선택 (토글) */}
								<Pressable
									onPress={() => {
										toggleIsMine(item.id);
										if (!getOpen(item.id)) contentHMap.current[item.id] = 0; // 접힌 상태라면 다음 펼침 때 재측정 가능
									}}
									style={[styles.accRow, { borderColor: theme.border, backgroundColor: theme.bg }]}
								>
									<Text style={[styles.accRowText, { color: theme.text }]}>
										내 식물인지 선택 ({getIsMine(item.id) ? "내꺼로 저장" : "다른 식물이면 등록 안 함"})
									</Text>
								</Pressable>

								{/* 3) 별명/날짜 선택(표시용) */}
								<View style={[styles.accRow, { borderColor: theme.border, backgroundColor: theme.bg }]}>
									<Text style={[styles.accRowText, { color: theme.text }]}>
										내 식물 별명 선택 / 진단 날짜(당일): {item.nickname} / {todayStr}
									</Text>
								</View>

								{/* 4) 후보 병충해 1~3 */}
								{(item.candidates ?? []).slice(0, 3).map((d, i) => (
									<View
										key={d.id}
										style={[styles.accRow, { borderColor: theme.border, backgroundColor: theme.bg }]}
									>
										<Text style={[styles.accRowText, { color: theme.text }]}>
											{i + 1}. {d.name} : {d.desc ?? "-"}
											{typeof d.confidence === "number" ? ` (${Math.round(d.confidence * 100)}%)` : ""}
										</Text>
									</View>
								))}

								{/* 5) 등록 / 취소 */}
								<View style={styles.accActions}>
									<Pressable onPress={onRegister} style={[styles.accBtn, styles.accBtnPrimary]}>
										<Text style={styles.accBtnPrimaryText}>등록(일단 여기 위치)</Text>
									</Pressable>
									<Pressable onPress={onCancel} style={[styles.accBtn, styles.accBtnGhost]}>
										<Text style={[styles.accBtnGhostText, { color: theme.text }]}>취소</Text>
									</Pressable>
								</View>
							</View>
						</Animated.View>

						{/* 화살표 버튼 (클릭 시 토글) */}
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
			{error ? (
				<View style={[styles.errorBox, { borderColor: theme.border, backgroundColor: theme.bg }]}>
					<Text style={{ color: theme.text }}>⚠️ {error}</Text>
				</View>
			) : null}

			<FlatList
				ref={listRef} // ← 스크롤 제어
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

// ─────────────────────────────────────────────────────────────────────────────
// DEMO_DATA (백엔드 스펙과 동일 스키마)
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
			{ id: "cand_001", code: "leaf_blight", name: "잎마름병", desc: "가장자리 갈변·마름", confidence: 0.87 },
			{ id: "cand_002", code: "powdery_mildew", name: "흰가루병", desc: "백색 분말성 균총", confidence: 0.08 },
			{ id: "cand_003", code: "scale_insect", name: "깍지벌레", desc: "줄기·잎의 흰 혹", confidence: 0.05 },
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
			{ id: "cand_004", code: "aphid", name: "진딧물", desc: "연한 새순 부위 군집", confidence: 0.76 },
			{ id: "cand_005", code: "spider_mite", name: "응애", desc: "미세한 점상 피해", confidence: 0.14 },
			{ id: "cand_006", code: "thrips", name: "총채벌레", desc: "은백색 변색 스트리크", confidence: 0.10 },
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
			{ id: "cand_007", code: "aphid", name: "진딧물", desc: "연한 새순 부위 군집", confidence: 0.76 },
			{ id: "cand_008", code: "spider_mite", name: "응애", desc: "미세한 점상 피해", confidence: 0.14 },
			{ id: "cand_009", code: "thrips", name: "총채벌레", desc: "은백색 변색 스트리크", confidence: 0.10 },
		],
	},
];

// ─────────────────────────────────────────────────────────────────────────────
// 스타일
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
	container: { flex: 1, paddingBottom: 50 },
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

	// 아코디언 펼침 영역
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
	accActions: {
		flexDirection: "row",
		gap: 8,
		marginTop: 4,
	},
	accBtn: {
		flex: 1,
		height: 40,
		borderRadius: 8,
		alignItems: "center",
		justifyContent: "center",
	},
	accBtnPrimary: { backgroundColor: "#00ac47" },
	accBtnPrimaryText: { color: "#fff", fontWeight: "600" },
	accBtnGhost: { borderWidth: 1 },
	accBtnGhostText: { fontWeight: "600" },
});
