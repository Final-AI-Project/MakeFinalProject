// app/(page)/(stackless)/plant-new.tsx
// ─────────────────────────────────────────────────────────────────────────────
// ① Imports
// ─────────────────────────────────────────────────────────────────────────────
import React, { useMemo, useState, useRef, useEffect } from "react";
import {
	View, Text, StyleSheet, ScrollView,
	TextInput, Pressable, Image, Alert, ActivityIndicator,
	Platform, Dimensions, KeyboardAvoidingView, Keyboard, StatusBar,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useRouter } from "expo-router";
import { useColorScheme } from "react-native";
import Colors from "../../../constants/Colors";

// 공통 모달
import ClassifierResultModal, { ClassifyResult } from "../../../components/common/ClassifierResultModal";

type IndoorOutdoor = "indoor" | "outdoor" | null;

const SPECIES = [
	"몬스테라","스투키","금전수","선인장","호접란","테이블야자",
	"홍콩야자","스파티필럼","관음죽","벵갈고무나무","올리브나무","디펜바키아","보스턴고사리",
] as const;

// (카메라와 동일한 가짜 분류기)
function mockClassify(_uri: string): ClassifyResult {
	const pool = [
		"몬스테라","스투키","금전수","선인장","호접란","테이블야자",
		"홍콩야자","스파티필럼","관음죽","벵갈고무나무","올리브나무","디펜바키아","보스턴고사리",
	] as const;
	const species = pool[Math.floor(Math.random() * pool.length)];
	const confidence = Math.round(70 + Math.random() * 29);
	return { species, confidence };
}

// ─────────────────────────────────────────────────────────────────────────────
// ③ Component
// ─────────────────────────────────────────────────────────────────────────────
export default function PlantNew() {
	// Theme & Router
	const router = useRouter();
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];

	// 상단 오프셋 (SafeAreaProvider 없이)
	const topOffset = Platform.OS === "android" ? (StatusBar.currentHeight ?? 0) : 0;

	// Form states
	const [imageUri, setImageUri] = useState<string | null>(null);
	const [species, setSpecies] = useState<string>("");
	const [nickname, setNickname] = useState<string>("");
	const [startedAt, setStartedAt] = useState<string>("");

	// UI states
	const [busy, setBusy] = useState(false);
	const [resultVisible, setResultVisible] = useState(false);
	const [result, setResult] = useState<ClassifyResult | null>(null);

	// Scroll helpers
	const scrollRef = useRef<ScrollView>(null);
	const fieldY = useRef<Record<string, number>>({});
	function onFieldLayout(key: string, y: number) { fieldY.current[key] = y; }
	function scrollToField(key: string, inputHeight = 56) {
		const y = fieldY.current[key] ?? 0;
		const screenH = Dimensions.get("window").height;
		const targetY = Math.max(0, y - screenH / 3 + inputHeight / 2);
		scrollRef.current?.scrollTo({ y: targetY, animated: true });
	}

	// Validation
	const isKnownSpecies = useMemo(
		() => (species ? (SPECIES as readonly string[]).includes(species) : true),
		[species]
	);
	const isAllFilled = Boolean(imageUri && species.trim() && nickname.trim() && startedAt.trim());
	const isDateLike = useMemo(() => !startedAt || /^\d{4}-\d{2}-\d{2}$/.test(startedAt), [startedAt]);

	// Utils
	function formatDateInput(text: string): string {
		const digits = text.replace(/\D/g, "").slice(0, 8);
		if (digits.length <= 4) return digits;
		if (digits.length <= 6) return `${digits.slice(0, 4)}-${digits.slice(4)}`;
		return `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6, 8)}`;
	}

	// Image pick
	function handlePickImage() {
		if (Platform.OS === "web") return void pickFromLibrary();
		Alert.alert("사진 등록", "사진을 불러올 방법을 선택하세요.", [
			{ text: "사진 찍기", onPress: takePhoto },
			{ text: "앨범 선택", onPress: pickFromLibrary },
			{ text: "취소", style: "cancel" },
		]);
	}
	async function pickFromLibrary() {
		const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
		if (status !== "granted") return Alert.alert("권한 필요", "앨범 접근 권한을 허용해주세요.");
		setBusy(true);
		try {
			const res = await ImagePicker.launchImageLibraryAsync({
				allowsEditing: true, quality: 0.9, mediaTypes: ImagePicker.MediaTypeOptions.Images, aspect: [1, 1],
			});
			if (!res.canceled && res.assets?.[0]?.uri) {
				setImageUri(res.assets[0].uri);
				const r = mockClassify(res.assets[0].uri);
				setResult(r);
				setTimeout(() => setResultVisible(true), 80);
			}
		} finally { setBusy(false); }
	}
	async function takePhoto() {
		const { status } = await ImagePicker.requestCameraPermissionsAsync();
		if (status !== "granted") return Alert.alert("권한 필요", "카메라 권한을 허용해주세요.");
		setBusy(true);
		try {
			const res = await ImagePicker.launchCameraAsync({ allowsEditing: true, quality: 0.9, aspect: [1, 1] });
			if (!res.canceled && res.assets?.[0]?.uri) {
				setImageUri(res.assets[0].uri);
				const r = mockClassify(res.assets[0].uri);
				setResult(r);
				setTimeout(() => setResultVisible(true), 80);
			}
		} finally { setBusy(false); }
	}

	// Submit
	function handleSubmit() {
		if (!isAllFilled) return;
		if (!isDateLike) return Alert.alert("날짜 형식 확인", "날짜는 YYYY-MM-DD 형식으로 입력해주세요.");
		Keyboard.dismiss();
		Alert.alert("등록 완료", "새 식물이 등록되었습니다! (로컬 처리 가정)", [
			{ text: "확인", onPress: () => router.replace("/(page)/home") },
		]);
	}

	// Render
	return (
		<KeyboardAvoidingView
			style={{ flex: 1, backgroundColor: theme.bg }}
			behavior={Platform.select({ ios: "padding", android: "height" })}  // ← 동일화
			keyboardVerticalOffset={topOffset}
		>
			<ScrollView
				ref={scrollRef}
				keyboardDismissMode={Platform.select({ ios: "interactive", android: "none" })} // ← 스치면 내려가지 않게
				keyboardShouldPersistTaps="handled" // ← 인풋 터치 유지
			>
				{/* 사진 */}
				<View style={styles.photoBox}>
					<Pressable
						onPress={handlePickImage}
						disabled={busy}
						onStartShouldSetResponder={() => false}
						style={[styles.photoPlaceholder, { borderColor: theme.border, backgroundColor: theme.graybg }]}
					>
						{imageUri ? (
							<>
								<Image source={{ uri: imageUri }} style={styles.photo} resizeMode="cover" />
								<View style={[styles.changeBadge, { borderColor: theme.border, backgroundColor: theme.bg + "cc" }]}>
									<Text style={[styles.changeBadgeText, { color: theme.text }]}>사진 변경</Text>
								</View>
							</>
						) : (
							<>
								<Text style={{ color: theme.text, fontSize: 40 }}>+</Text>
								<Text style={{ color: theme.text, marginTop: 4 }}>키우는 식물을 자랑해주세요!</Text>
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
					{/* 품종 분류 */}
					<View style={styles.field} onLayout={(e) => onFieldLayout("species", e.nativeEvent.layout.y)}>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>품종 분류</Text>
						<TextInput
							placeholder="직접입력 (예: 몬스테라)"
							placeholderTextColor="#909090"
							value={species}
							onChangeText={setSpecies}
							onFocus={() => scrollToField("species")}
							style={[styles.input, { color: theme.text, borderColor: theme.border }]}
						/>
						<Text style={[styles.notice, { color: theme.text }]}>
							* 직접입력 시 올바른 품종정보나 생육정보의 제공이 어려울 수 있습니다.
						</Text>
						{species.trim().length > 0 && !isKnownSpecies && (
							<Text style={styles.warn}>
								* 데이터 베이스에 없는 식물입니다. 식물주님의 품종을 학습하여 조만간 업데이트 하겠습니다.
							</Text>
						)}
					</View>

					{/* 별명 */}
					<View style={styles.field} onLayout={(e) => onFieldLayout("nickname", e.nativeEvent.layout.y)}>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>내 식물 별명</Text>
						<TextInput
							placeholder="예: 몬몬이"
							placeholderTextColor="#909090"
							value={nickname}
							onChangeText={setNickname}
							onFocus={() => scrollToField("nickname")}
							style={[styles.input, { color: theme.text, borderColor: theme.border }]}
						/>
					</View>

					{/* 키우기 시작한 날 */}
					<View style={styles.field} onLayout={(e) => onFieldLayout("startedAt", e.nativeEvent.layout.y)}>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>키우기 시작한 날</Text>
						<TextInput
							placeholder="YYYY-MM-DD"
							placeholderTextColor="#909090"
							value={startedAt}
							onChangeText={(text) => setStartedAt(formatDateInput(text))}
							onFocus={() => scrollToField("startedAt")}
							keyboardType="number-pad"
							maxLength={10}
							style={[styles.input, { color: theme.text, borderColor: theme.border }]}
						/>
						{startedAt.length > 0 && !isDateLike && (
							<Text style={styles.warn}>YYYY-MM-DD 형식으로 입력해주세요.</Text>
						)}
					</View>
				
					{/* 하단 고정 버튼 (키보드 높이만큼 자동 상승) */}
					<View style={ styles.bottomBar }>
						<Pressable
							onPress={() => { Keyboard.dismiss(); router.replace("/(page)/home"); }}
							style={[styles.cancelBtn, { borderColor: theme.border }]}
						>
							<Text style={[styles.cancelText, { color: theme.text }]}>취소</Text>
						</Pressable>
						<Pressable
							disabled={!isAllFilled || !isDateLike}
							onPress={handleSubmit}
							style={[styles.submitBtn, { backgroundColor: !isAllFilled || !isDateLike ? theme.graybg : theme.primary }]}
						>
							<Text style={[styles.submitText, { color: "#fff" }]}>등록하기</Text>
						</Pressable>
					</View>
				</View>
			</ScrollView>

			{/* 공통 Result Modal */}
			<ClassifierResultModal
				visible={resultVisible}
				theme={theme}
				result={result}
				onClose={() => setResultVisible(false)}
				onRetake={handlePickImage}
			/>
		</KeyboardAvoidingView>
	);
}

// ─────────────────────────────────────────────────────────────────────────────
// ④ Styles
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
	container: { flex: 1 },

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
	input: { height:50, borderWidth: 1, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 12 },
	notice: { fontSize: 12, marginTop: 6 },
	warn: { fontSize: 12, marginTop: 6, color: "#d93025" },
	bottomBar: { flexDirection: "row", gap: 8, alignItems: "center", marginTop:40,},

	cancelBtn: { flex: 1, borderWidth: 1, borderRadius: 12, alignItems: "center", justifyContent: "center", paddingVertical: 14 },
	cancelText: { fontSize: 15, fontWeight: "600" },
	submitBtn: { flex: 2, borderRadius: 12, alignItems: "center", justifyContent: "center", paddingVertical: 14 },
	submitText: { fontWeight: "700", fontSize: 16 },

	changeBadge: { position: "absolute", right: 10, bottom: 10, borderWidth: 1, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6 },
	changeBadgeText: { fontSize: 12, fontWeight: "700" },
});
