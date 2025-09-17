// app/(page)/(stackless)/diary.tsx

// ─────────────────────────────────────────────────────────────────────────────
// ① Imports
// ─────────────────────────────────────────────────────────────────────────────
import React, { useMemo, useRef, useState } from "react";
import {
	View, Text, StyleSheet, ScrollView, KeyboardAvoidingView, Platform,
	TextInput, Pressable, Image, Alert, ActivityIndicator, TouchableOpacity, Animated, Easing,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useColorScheme } from "react-native";
import { useRouter } from "expo-router";
import Colors from "../../constants/Colors";
import { fetchSimpleWeather } from "../../components/common/weatherBox";

// ─────────────────────────────────────────────────────────────────────────────
// ② Helpers & Types
// ─────────────────────────────────────────────────────────────────────────────
type Weather = "맑음" | "흐림" | "비" | "눈" | null;

const todayStr = () => {
	const d = new Date();
	const yyyy = d.getFullYear();
	const mm = String(d.getMonth() + 1).padStart(2, "0");
	const dd = String(d.getDate()).padStart(2, "0");
	return `${yyyy}-${mm}-${dd}`;
};

/** 인라인 드롭다운(모달 없이) */
function InlineSelect<T extends string>({
	label, value, options, onChange, placeholder = "선택하세요", theme,
}: {
	label: string;
	value: T | null;
	options: { label: string; value: T }[];
	onChange: (v: T) => void;
	placeholder?: string;
	theme: typeof Colors.light;
}) {
	const [open, setOpen] = useState(false);
	return (
		<View style={styles.field}>
			<Text style={[styles.sectionLabel, { color: theme.text }]}>{label}</Text>
			<Pressable onPress={() => setOpen(v => !v)} style={[styles.input, { borderColor: theme.border }]}>
				<Text style={{ color: theme.text }}>
					{value ? options.find(o => o.value === value)?.label : placeholder}
				</Text>
			</Pressable>
			{open && (
				<View style={[styles.dropdownPanel, { borderColor: theme.border }]}>
					{options.map(opt => (
						<Pressable
							key={opt.value}
							onPress={() => { onChange(opt.value); setOpen(false); }}
							style={[styles.dropdownItem, { backgroundColor: theme.bg }]}
						>
							<Text style={{ color: theme.text }}>{opt.label}</Text>
						</Pressable>
					))}
				</View>
			)}
		</View>
	);
}

/** 하단 슬라이드 토스트 */
function BottomToast({ visible, text, onClose, theme }: {
	visible: boolean;
	text: string;
	onClose: () => void;
	theme: typeof Colors.light;
}) {
	const slide = useRef(new Animated.Value(0)).current;
	React.useEffect(() => {
		Animated.timing(slide, {
			toValue: visible ? 1 : 0,
			duration: 280,
			easing: visible ? Easing.out(Easing.cubic) : Easing.in(Easing.cubic),
			useNativeDriver: true,
		}).start();
	}, [visible]);
	const translateY = slide.interpolate({ inputRange: [0, 1], outputRange: [80, 0] });
	const opacity = slide.interpolate({ inputRange: [0, 1], outputRange: [0, 1] });
	// @ts-ignore 내부값 확인용
	if (!visible && slide._value === 0) return null;
	return (
		<Animated.View style={[styles.toastWrap, { transform: [{ translateY }], opacity }]}>
			<View style={[styles.toastCard, { backgroundColor: theme.text === "#1a1a1a" ? "#1f2937" : "#0f172a" }]}>
				<Text style={styles.toastTitle}>AI 코멘트</Text>
				<Text style={styles.toastText}>{text || "임시 응답 텍스트가 없습니다."}</Text>
				<TouchableOpacity style={styles.toastClose} onPress={onClose} activeOpacity={0.9}>
					<Text style={styles.toastCloseText}>닫기</Text>
				</TouchableOpacity>
			</View>
		</Animated.View>
	);
}

// ─────────────────────────────────────────────────────────────────────────────
// ③ Component
// ─────────────────────────────────────────────────────────────────────────────
export default function Diary() {
	// Theme & Router
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const router = useRouter();

	// 폼 상태
	const [photoUri, setPhotoUri] = useState<string | null>(null);
	const [title, setTitle] = useState("");
	const [selectedPlant, setSelectedPlant] = useState<string | null>(null);
	const [date] = useState(todayStr());
	const [weather, setWeather] = useState<Weather>(null);	 // 자동/readonly
	const [body, setBody] = useState("");

	// 기타 UI
	const [busy, setBusy] = useState(false);
	const [aiDraft, setAiDraft] = useState("오늘은 통풍만 잘 시켜주세요. 물은 내일 추천! 🌤️");
	const [toastVisible, setToastVisible] = useState(false);

	// 내 식물(별명) — TODO: 실제 내 식물 리스트로 교체
	const myPlants = useMemo(
		() => [
			{ label: "초록이 (몬스테라)", value: "초록이" },
			{ label: "복덩이 (금전수)", value: "복덩이" },
		],
		[]
	);

	// 날씨 자동 채움 (WeatherBox 렌더링 없이)
	React.useEffect(() => {
		(async () => {
			const w = await fetchSimpleWeather(
				"GTr1cI7Wi0FRbOTFBaUzUCzCDP4OnyyEmHnn11pxCUC5ehG5bQnbyztgeydnOWz1O04tjw1SE5RsX8RNo6XCgQ==",
				{ lat: 37.4836, lon: 127.0326, label: "서울시 - 서초구" }
			);
			if (w) setWeather(prev => prev ?? w);
		})();
	}, []);

	// 제출 버튼 활성 조건
	const canSubmit = Boolean(photoUri && title.trim() && selectedPlant && date && weather && body.trim());

	// 사진 선택
	const pickImage = async () => {
		const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
		if (status !== "granted") return Alert.alert("권한 필요", "앨범 접근 권한을 허용해주세요.");
		setBusy(true);
		try {
			const res = await ImagePicker.launchImageLibraryAsync({
				allowsEditing: true, quality: 0.9, mediaTypes: ["images"], aspect: [1, 1],
			});
				if (!res.canceled && res.assets?.[0]?.uri) setPhotoUri(res.assets[0].uri);
		} finally { setBusy(false); }
	};

	// 등록
	const handleSubmit = async () => {
		if (!canSubmit) return;
		// TODO: 서버 저장 API
		// await fetch("...", { method:"POST", body: JSON.stringify({ photoUri, title, selectedPlant, date, weather, body }) });
		Alert.alert("등록 완료", "일기가 임시로 저장되었습니다.");
		setToastVisible(true);
	};

	return (
		<KeyboardAvoidingView
			style={[styles.container, { backgroundColor: theme.bg }]}
			behavior={Platform.select({ ios: "padding", android: "height" })}
		>
			<ScrollView keyboardShouldPersistTaps="handled" keyboardDismissMode="interactive" contentContainerStyle={{ paddingBottom: 120 }}>
				{/* 사진 등록 */}
				<View style={styles.photoBox}>
					<Pressable
						onPress={pickImage}
						disabled={busy}
						style={[styles.photoPlaceholder, { borderColor: theme.border, backgroundColor: theme.graybg }]}
					>
						{photoUri ? (
							<>
								<Image source={{ uri: photoUri }} style={styles.photo} resizeMode="cover" />
								<View style={[styles.changeBadge, { borderColor: theme.border, backgroundColor: theme.bg + "cc" }]}>
									<Text style={[styles.changeBadgeText, { color: theme.text }]}>사진 변경</Text>
								</View>
							</>
						) : (
							<>
								<Text style={{ color: theme.text, fontSize: 40 }}>+</Text>
								<Text style={{ color: theme.text, marginTop: 4 }}>사진을 등록하세요</Text>
							</>
						)}
					</Pressable>

					{busy && (
						<View style={styles.busyOverlay}>
							<ActivityIndicator size="large" />
						</View>
					)}
				</View>

				{/* 입력들 */}
				<View style={styles.inputArea}>
					{/* 제목 */}
					<View style={styles.field}>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>제목</Text>
						<TextInput
							placeholder="제목을 입력하세요"
							placeholderTextColor="#909090"
							value={title}
							onChangeText={setTitle}
							style={[styles.input, { color: theme.text, borderColor: theme.border }]}
							returnKeyType="next"
						/>
					</View>

					{/* 내 식물(별명) */}
					<InlineSelect
						label="내 식물(별명)"
						value={selectedPlant}
						options={myPlants}
						onChange={setSelectedPlant}
						placeholder="내 식물을 선택하세요"
						theme={theme}
					/>

					{/* 날짜 (읽기전용) */}
					<View style={styles.field}>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>날짜</Text>
						<TextInput
							value={date}
							editable={false}
							style={[styles.input, { color: theme.text, borderColor: theme.border, opacity: 0.85 }]}
						/>
					</View>

					{/* 날씨 (자동/읽기전용) */}
					<View style={styles.field}>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>날씨</Text>
						<TextInput
							value={weather ?? ""}
							editable={false}
							placeholder="조회 중…"
							placeholderTextColor="#909090"
							style={[styles.input, { color: theme.text, borderColor: theme.border, opacity: 0.85 }]}
						/>
					</View>

					{/* 일기 내용 */}
					<View style={styles.field}>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>일기 내용</Text>
						<TextInput
							placeholder="오늘의 식물 이야기를 적어주세요…"
							placeholderTextColor="#909090"
							value={body}
							onChangeText={setBody}
							multiline
							textAlignVertical="top"
							style={[styles.input, { color: theme.text, borderColor: theme.border, minHeight: 180, lineHeight: 22 }]}
						/>
					</View>

					{/* 임시 LLM 응답 텍스트 (토스트에 표시) */}
					<View style={styles.field}>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>AI 응답(임시)</Text>
						<TextInput
							placeholder="등록 후 토스트에 표시될 임시 텍스트"
							placeholderTextColor="#909090"
							value={aiDraft}
							onChangeText={setAiDraft}
							style={[styles.input, { color: theme.text, borderColor: theme.border }]}
						/>
					</View>
				</View>
			</ScrollView>

			{/* 하단 버튼 */}
			<View style={[styles.bottomBar, { backgroundColor: theme.bg }]}>
				<Pressable onPress={() => router.back()} style={[styles.cancelBtn, { borderColor: theme.border }]}>
					<Text style={[styles.cancelText, { color: theme.text }]}>취소</Text>
				</Pressable>
				<Pressable
					disabled={!canSubmit}
					onPress={handleSubmit}
					style={[styles.submitBtn, { backgroundColor: !canSubmit ? theme.graybg : theme.primary }]}
				>
					<Text style={[styles.submitText, { color: theme.text }]}>등록</Text>
				</Pressable>
			</View>

			{/* 토스트 */}
			<BottomToast visible={toastVisible} text={aiDraft} onClose={() => setToastVisible(false)} theme={theme} />
		</KeyboardAvoidingView>
	);
}

// ─────────────────────────────────────────────────────────────────────────────
// ④ Styles (plant-new.tsx 톤과 동일 스케일)
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
	container: { flex: 1, paddingBottom: 40 },

	sectionLabel: { fontSize: 16, fontWeight: "700", marginBottom: 8 },
	helper: { fontSize: 12, marginBottom: 8, opacity: 0.8 },

	photoBox: { alignItems: "center", position: "relative", height: 260, marginTop: 12 },
	photo: { position: "absolute", left: 0, top: 0, width: "100%", height: 260, resizeMode: "cover" },
	photoPlaceholder: { width: "100%", height: 260, alignItems: "center", justifyContent: "center" },

	busyOverlay: {
		position: "absolute", left: 0, right: 0, top: 0, bottom: 0,
		alignItems: "center", justifyContent: "center",
		backgroundColor: "rgba(0,0,0,0.08)", borderRadius: 12,
	},

	inputArea: { paddingHorizontal: 24 },
	field: { marginTop: 24 },
	input: { borderWidth: 1, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 12 },

	bottomBar: {
		position: "absolute", left: 0, right: 0, bottom: 68,
		flexDirection: "row", gap: 8, padding: 12,
	},
	cancelBtn: { flex: 1, borderWidth: 1, borderRadius: 12, alignItems: "center", justifyContent: "center", paddingVertical: 14 },
	cancelText: { fontSize: 15, fontWeight: "600" },
	submitBtn: { flex: 2, borderRadius: 12, alignItems: "center", justifyContent: "center", paddingVertical: 14 },
	submitText: { fontWeight: "700", fontSize: 16 },

	changeBadge: { position: "absolute", right: 10, bottom: 10, borderWidth: 1, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6 },
	changeBadgeText: { fontSize: 12, fontWeight: "700" },

	dropdownPanel: { borderWidth: 1, borderRadius: 10, overflow: "hidden", marginTop: -6 },
	dropdownItem: { paddingHorizontal: 12, paddingVertical: 12 },

	toastWrap: {
		position: "absolute", left: 0, right: 0, bottom: 16,
		alignItems: "center", justifyContent: "center", paddingHorizontal: 16,
	},
	toastCard: { maxWidth: 640, alignSelf: "stretch", marginHorizontal: 16, borderRadius: 16, padding: 14 },
	toastTitle: { color: "#fff", fontSize: 13, fontWeight: "800", marginBottom: 6, opacity: 0.9 },
	toastText: { color: "#fff", fontSize: 15, lineHeight: 22 },
	toastClose: { alignSelf: "flex-end", marginTop: 8, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8, backgroundColor: "rgba(255,255,255,0.14)" },
	toastCloseText: { color: "#fff", fontWeight: "700" },
});
