// app/(page)/diaryList.tsx
import React, { useMemo, useState } from "react";
import {
	View,
	Text,
	StyleSheet,
	FlatList,
	Pressable,
	useColorScheme,
} from "react-native";
import { useRouter } from "expo-router";
import Colors from "../../constants/Colors";

// ─────────────────────────────────────────────────────────────────────────────
// ① Types
// ─────────────────────────────────────────────────────────────────────────────
type Diary = {
	id: string;
	title: string;      // 목록에 보일 제목 (예: 일기 1번)
	date: string;       // "YYYY-MM-DD"
	plant?: string;     // 식물 별명/품종 (정렬/표시 용도)
};

// ─────────────────────────────────────────────────────────────────────────────
// ② Component
// ─────────────────────────────────────────────────────────────────────────────
export default function DiaryList() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const router = useRouter();

	// TODO(실데이터): 서버에서 내 모든 일기 목록을 가져오세요.
	// 아래는 스크린샷 맞춘 더미 데이터입니다.
	const raw = useMemo<Diary[]>(
		() => [
			{ id: "1", title: "일기 1번", date: "2025-09-10", plant: "초록이" },
			{ id: "2", title: "일기 2번", date: "2025-09-12", plant: "복덩이" },
			{ id: "3", title: "일기 3번", date: "2025-09-18", plant: "초록이" },
		],
		[]
	);

	// 정렬 상태: "date" | "plant"
	const [sortBy, setSortBy] = useState<"date" | "plant">("date");

	// 간단 정렬 (날짜 ↔ 식물명)
	const data = useMemo(() => {
		const copy = [...raw];
		if (sortBy === "date") {
			copy.sort((a, b) => (a.date < b.date ? 1 : -1)); // 최신 우선
		} else {
			copy.sort((a, b) => (a.plant ?? "").localeCompare(b.plant ?? ""));
		}
		return copy;
	}, [raw, sortBy]);

	// 항목 클릭 → 해당 일기 페이지로 이동
	// TODO(경로 확정): 기존 작성/상세 페이지 경로에 맞게 pathname만 바꾸면 됩니다.
	// - 작성/수정 단일 페이지라면: "/(page)/diary" 로 id 전달
	// - 상세 전용 페이지가 있다면: "/(page)/diary-detail" 로 변경
	const openDiary = (item: Diary) => {
		router.push({
			pathname: "/(page)/diary",
			params: { id: item.id },
		});
	};

	return (
		<View style={[styles.container, { backgroundColor: theme.bg }]}>
			{/* 제목/부제 — 스크린샷 텍스트 */}
			<View style={styles.header}>
				<Text style={[styles.title, { color: theme.text }]}>
					내 식물 전부 일기 목록
				</Text>
				<Text style={[styles.subtitle, { color: theme.text, opacity: 0.8 }]}>
					(날짜별, 식물별 정렬)
				</Text>
			</View>

			{/* 정렬 토글 (간단 텍스트 토글) — 필요 없으면 제거해도 됨 */}
			<View style={styles.sortBar}>
				<Pressable
					onPress={() => setSortBy("date")}
					style={[
						styles.sortBtn,
						{
							borderColor: theme.border,
							backgroundColor:
								sortBy === "date" ? theme.graybg : theme.bg,
						},
					]}
				>
					<Text style={{ color: theme.text }}>날짜별</Text>
				</Pressable>
				<Pressable
					onPress={() => setSortBy("plant")}
					style={[
						styles.sortBtn,
						{
							borderColor: theme.border,
							backgroundColor:
								sortBy === "plant" ? theme.graybg : theme.bg,
						},
					]}
				>
					<Text style={{ color: theme.text }}>식물별</Text>
				</Pressable>
			</View>

			{/* 리스트 */}
			<FlatList
				data={data}
				keyExtractor={(item) => item.id}
				contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 120 }}
				renderItem={({ item }) => (
					<Pressable
						onPress={() => openDiary(item)}
						style={[
							styles.card,
							{ borderColor: theme.border, backgroundColor: theme.bg },
						]}
					>
						<Text style={[styles.cardTitle, { color: theme.text }]}>
							{item.title}
						</Text>
					</Pressable>
				)}
				ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
			/>

			{/* 우하단 원형 버튼 (타임 랩스 만들기) */}
			<Pressable
				onPress={() => {
					// TODO: 타임랩스 생성 페이지 경로로 교체
					// 예) router.push("/(page)/timelapse");
				}}
				style={[
					styles.fab,
					{
						borderColor: theme.border,
						backgroundColor: theme.bg,
					},
				]}
			>
				<Text style={[styles.fabText, { color: theme.text }]}>
					타임 랩스{"\n"}만들기
				</Text>
			</Pressable>
		</View>
	);
}

// ─────────────────────────────────────────────────────────────────────────────
// ③ Styles
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
	container: { flex: 1 },
	header: {
		paddingTop: 16,
		paddingHorizontal: 16,
		paddingBottom: 8,
	},
	title: { fontSize: 18, fontWeight: "800", marginBottom: 2 },
	subtitle: { fontSize: 14 },

	sortBar: {
		flexDirection: "row",
		gap: 8,
		paddingHorizontal: 16,
		marginBottom: 12,
	},
	sortBtn: {
		borderWidth: 1,
		borderRadius: 10,
		paddingVertical: 8,
		paddingHorizontal: 12,
	},

	card: {
		minHeight: 56,
		borderWidth: 1,
		borderRadius: 10,
		justifyContent: "center",
		paddingHorizontal: 16,
	},

	cardTitle: { fontSize: 15, fontWeight: "700" },

	fab: {
		position: "absolute",
		right: 16,
		bottom: 16,
		width: 92,
		height: 92,
		borderRadius: 999,
		borderWidth: 1,
		alignItems: "center",
		justifyContent: "center",
		// 살짝 그림자
		shadowColor: "#000",
		shadowOpacity: 0.2,
		shadowRadius: 6,
		shadowOffset: { width: 0, height: 3 },
		elevation: 6,
	},
	fabText: { fontSize: 13, textAlign: "center", fontWeight: "600", lineHeight: 18 },
});
