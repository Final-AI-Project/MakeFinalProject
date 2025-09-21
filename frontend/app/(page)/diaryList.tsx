// app/(page)/diaryList.tsx
import React, { useMemo, useState } from "react";
import {
	View,
	Text,
	StyleSheet,
	FlatList,
	Pressable,
	useColorScheme,
	Image,
} from "react-native";
import { useRouter } from "expo-router";
import Colors from "../../constants/Colors";
import { Picker } from "@react-native-picker/picker";

// ─────────────────────────────────────────────────────────────────────────────
// ① Types
// ─────────────────────────────────────────────────────────────────────────────
type Diary = {
	id: string;
	title: string;          // 목록 제목
	date: string;           // "YYYY-MM-DD"
	plant?: string;         // 식물 별명/품종
	photoUri?: string|null; // 썸네일
	content?: string;       // 본문 (리스트에선 말줄임)
};

// ─────────────────────────────────────────────────────────────────────────────
// ② Component
// ─────────────────────────────────────────────────────────────────────────────
export default function DiaryList() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const router = useRouter();

	// TODO(실데이터): 서버에서 일기 목록을 가져오세요.
	const raw = useMemo<Diary[]>(
		() => [
			{
				id: "1",
				title: "초록이의 새로운 잎",
				date: "2025-09-10",
				plant: "초록이",
				photoUri: null, // 예시: 이미지 없을 때
				content:
					"오늘은 초록이에게 물을 주고 잎을 닦아줬다. 새로 올라오는 잎이 꽤 커서 기대된다. 해가 조금만 더 들어오면 좋을 텐데...",
			},
			{
				id: "2",
				title: "복덩이 분갈이",
				date: "2025-09-12",
				plant: "복덩이",
				photoUri: "https://picsum.photos/seed/plant2/200/200",
				content:
					"분갈이를 하고 나니 뿌리 상태가 훨씬 좋아 보였다. 배수층을 충분히 깔아줬고 마사토를 조금 섞었다.",
			},
			{
				id: "3",
				title: "초록이 물 주기",
				date: "2025-09-18",
				plant: "초록이",
				photoUri: "https://picsum.photos/seed/plant3/200/200",
				content:
					"겉흙이 마르고 가벼워져서 물을 듬뿍 줌. 잎 뒷면 해충은 없는지 확인했는데 이상 없음.",
			},
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
	// NOTE: 작성/상세 단일 페이지가 /(page)/diary 라는 전제
	const openDiary = (item: Diary) => {
		router.push({ pathname: "/(page)/diary", params: { id: item.id } });
	};

	return (
		<View style={[styles.container, { backgroundColor: theme.bg }]}>
			{/* 상단: 정렬 셀렉트 + 일기 쓰기 버튼 */}
			<View style={[styles.topBar, { backgroundColor: theme.bg }]}>
				<View
					style={[
					 styles.leftSelect,
					 { borderColor: theme.border, backgroundColor: theme.bg },
					]}
				>
					<Picker
						selectedValue={sortBy}
						onValueChange={(v) => setSortBy(v as "date" | "plant")}
						mode="dropdown"
						dropdownIconColor={theme.text}
						style={[styles.picker, { color: theme.text, backgroundColor: theme.bg }]}
					>
						<Picker.Item label="날짜별" value="date" />
						<Picker.Item label="식물별" value="plant" />
					</Picker>
				</View>

				<Pressable
					onPress={() => router.push("/(page)/diary")}
					style={[
						styles.writeBtn,
						{ borderColor: theme.border, backgroundColor: theme.graybg },
					]}
				>
					<Text style={[styles.writeBtnText, { color: theme.text }]}>일기 쓰기</Text>
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
						<View style={styles.cardRow}>
							{/* 썸네일 */}
							{item.photoUri ? (
								<Image
									source={{ uri: item.photoUri }}
									style={styles.thumb}
									resizeMode="cover"
								/>
							) : (
								<View
									style={[
										styles.thumb,
										{
											backgroundColor: theme.graybg,
											alignItems: "center",
											justifyContent: "center",
										},
									]}
								>
									<Text style={{ fontSize: 12, color: theme.text, opacity: 0.6 }}>
										No Image
									</Text>
								</View>
							)}

							{/* 내용 */}
							<View style={styles.cardBody}>
								<Text style={[styles.cardTitle, { color: theme.text }]} numberOfLines={1} ellipsizeMode="tail">
									{item.title}
								</Text>

								<Text style={[styles.cardMeta, { color: theme.text, opacity: 0.7 }]} numberOfLines={1}>
									{[item.plant, item.date].filter(Boolean).join(" · ")}
								</Text>

								{Boolean(item.content) && (
									<Text
										style={[styles.cardContent, { color: theme.text, opacity: 0.9 }]}
										numberOfLines={2}
										ellipsizeMode="tail"
									>
										{item.content}
									</Text>
								)}
							</View>
						</View>
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

	// 상단 바: 좌측 셀렉트, 우측 "일기 쓰기" 버튼
	topBar: {
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "space-between",
		paddingHorizontal: 16,
		paddingTop: 16,
		paddingBottom: 8,
		gap: 12,
	},
	leftSelect: {
		flex: 1,
		paddingVertical:0,
		borderWidth: 1,
		borderRadius: 10,
		overflow: "hidden",
		height: 40,
		justifyContent: "center",
	},
	picker: {
		width: "100%",
		paddingVertical:0,
	},
	writeBtn: {
		paddingHorizontal: 14,
		height: 40,
		borderRadius: 10,
		borderWidth: 1,
		alignItems: "center",
		justifyContent: "center",
	},
	writeBtnText: {
		fontSize: 14,
		fontWeight: "700",
	},

	// 카드
	card: {
		minHeight: 72,
		borderWidth: 1,
		borderRadius: 12,
		paddingHorizontal: 12,
		paddingVertical: 10,
	},
	cardRow: {
		flexDirection: "row",
		gap: 12,
	},
	thumb: {
		width: 56,
		height: 56,
		borderRadius: 10,
		overflow: "hidden",
	},
	cardBody: {
		flex: 1,
		minHeight: 56,
		justifyContent: "center",
	},
	cardTitle: {
		fontSize: 15,
		fontWeight: "800",
		marginBottom: 2,
	},
	cardMeta: {
		fontSize: 12,
		marginBottom: 6,
	},
	cardContent: {
		fontSize: 13,
		lineHeight: 18,
	},

	// FAB
	fab: {
		position: "absolute",
		right: 16,
		bottom: 90,
		width: 75,
		height: 75,
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
