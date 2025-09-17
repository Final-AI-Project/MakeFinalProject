// app/(page)/(stackless)/plant-new.tsx
import React, { useMemo, useState, useEffect } from "react";
import {
	View,
	Text,
	StyleSheet,
	ScrollView,
	KeyboardAvoidingView,
	Platform,
	TextInput,
	Pressable,
	Image,
	Alert,
	ActivityIndicator,
	Modal,
	TouchableOpacity,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useRouter } from "expo-router";
import { useColorScheme } from "react-native";
import Colors from "../../../constants/Colors";

// 꾸미기 이미지 (카메라 화면과 동일 자산)
import classifiercharacter from "../../../assets/images/classifier_setting.png";
import classifiercharacterWeapon from "../../../assets/images/classifier_weapon.png";
import classifiercharacterHand from "../../../assets/images/classifier_hand.png";

// Reanimated
import Animated, {
	useSharedValue,
	useAnimatedStyle,
	withTiming,
	withRepeat,
	withSequence,
	withDelay,
	Easing,
	cancelAnimation,
} from "react-native-reanimated";

type IndoorOutdoor = "indoor" | "outdoor" | null;

const SPECIES = [
	"몬스테라","스투키","금전수","선인장","호접란","테이블야자",
	"홍콩야자","스파티필럼","관음죽","벵갈고무나무","올리브나무","디펜바키아","보스턴고사리",
] as const;

export default function PlantNew() {
	const router = useRouter();
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];

	const [imageUri, setImageUri] = useState<string | null>(null);
	const [species, setSpecies] = useState<string>("");
	const [nickname, setNickname] = useState<string>("");
	const [startedAt, setStartedAt] = useState<string>("");

	// 🔹 촬영/선택 중 로딩 (1단계)
	const [busy, setBusy] = useState(false);

	// 🔹 결과 모달(2단계) — 텍스트 없이 꾸미기 이미지만 노출
	const [resultVisible, setResultVisible] = useState(false);

	// ======= Reanimated (모달 꾸미기 애니) =======
	const weaponAngle = useSharedValue(0);
	const handY = useSharedValue(0);
	const W = 75, H = 70; // weapon 이미지 크기

	// 무기: 45° ↔ 0° 무한 반복 + 시작 딜레이/홀드
	function startWeaponLoop({
		startDelay = 300, // 시작 대기
		hold = 200,       // 각 상태 머무름
		up = 220,         // 0→45
		down = 220,       // 45→0
	} = {}) {
		weaponAngle.value = 0;
		const seq = withSequence(
			withTiming(45, { duration: up, easing: Easing.out(Easing.cubic) }),
			withDelay(hold, withTiming(0, { duration: down, easing: Easing.in(Easing.cubic) })),
			withDelay(hold, withTiming(0, { duration: 0 }))
		);
		weaponAngle.value = withDelay(startDelay, withRepeat(seq, -1, false));
	}

	// 손: 위로 살짝 바운스 무한 반복
	function startHandLoop() {
		handY.value = withRepeat(
			withSequence(
				withTiming(-2, { duration: 250, easing: Easing.inOut(Easing.quad) }),
				withTiming( 0, { duration: 600, easing: Easing.inOut(Easing.quad) }),
				withTiming( 0, { duration: 250, easing: Easing.inOut(Easing.quad) }),
			),
			-1, false
		);
	}

	// 모달 열릴 때 시작 / 닫히면 정지 및 초기화
	useEffect(() => {
		if (resultVisible) {
			startWeaponLoop();
			startHandLoop();
		} else {
			cancelAnimation(weaponAngle);
			cancelAnimation(handY);
			weaponAngle.value = 0;
			handY.value = 0;
		}
	}, [resultVisible]);

	// bottom-right 축 회전
	const weaponAnimatedStyle = useAnimatedStyle(() => ({
		transform: [
			{ translateX:  (W / 2) + 10 },
			{ translateY:  (H / 2) + 10 },
			{ rotate: `${weaponAngle.value}deg` },
			{ translateX: -(W / 2) + 10 },
			{ translateY: -(H / 2) + 10 },
		],
	}));
	const handAnimatedStyle = useAnimatedStyle(() => ({
		transform: [{ translateY: handY.value }],
	}));
	// ============================================

	const isKnownSpecies = useMemo(
		() => (species ? (SPECIES as readonly string[]).includes(species) : true),
		[species],
	);
	const isAllFilled = Boolean(imageUri && species.trim() && nickname.trim() && startedAt.trim());
	const isDateLike = useMemo(() => {
		if (!startedAt) return true;
		return /^\d{4}-\d{2}-\d{2}$/.test(startedAt);
	}, [startedAt]);

	function handlePickImage() {
		if (Platform.OS === "web") {
			pickFromLibrary();
			return;
		}
		Alert.alert("사진 등록", "사진을 불러올 방법을 선택하세요.", [
			{ text: "사진 찍기", onPress: takePhoto },
			{ text: "앨범 선택", onPress: pickFromLibrary },
			{ text: "취소", style: "cancel" },
		]);
	}

	// 📸 갤러리/카메라 모두 1단계 로딩 → 2단계 모달(꾸미기)로 동일 처리
	async function pickFromLibrary() {
		const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
		if (status !== "granted") {
			Alert.alert("권한 필요", "앨범 접근 권한을 허용해주세요.");
			return;
		}
		setBusy(true);
		try {
			const res = await ImagePicker.launchImageLibraryAsync({
				allowsEditing: true,
				quality: 0.9,
				mediaTypes: ImagePicker.MediaTypeOptions.Images,
				aspect: [1, 1],
			});
			if (!res.canceled && res.assets?.[0]?.uri) {
				setImageUri(res.assets[0].uri);
				// 1단계 로딩 끝 → 2단계 모달
				setTimeout(() => setResultVisible(true), 80);
			}
		} finally {
			setBusy(false);
		}
	}

	async function takePhoto() {
		const { status } = await ImagePicker.requestCameraPermissionsAsync();
		if (status !== "granted") {
			Alert.alert("권한 필요", "카메라 권한을 허용해주세요.");
			return;
		}
		setBusy(true);
		try {
			const res = await ImagePicker.launchCameraAsync({
				allowsEditing: true,
				quality: 0.9,
				aspect: [1, 1],
			});
			if (!res.canceled && res.assets?.[0]?.uri) {
				setImageUri(res.assets[0].uri);
				// 1단계 로딩 끝 → 2단계 모달
				setTimeout(() => setResultVisible(true), 80);
			}
		} finally {
			setBusy(false);
		}
	}

	function handleSubmit() {
		if (!isAllFilled) return;
		if (!isDateLike) {
			Alert.alert("날짜 형식 확인", "날짜는 YYYY-MM-DD 형식으로 입력해주세요.");
			return;
		}
		Alert.alert("등록 완료", "새 식물이 등록되었습니다! (로컬 처리 가정)", [
			{ text: "확인", onPress: () => router.replace("/(page)/home") },
		]);
	}

	function formatDateInput(text: string): string {
		const digits = text.replace(/\D/g, "").slice(0, 8);
		if (digits.length <= 4) return digits;
		if (digits.length <= 6) return `${digits.slice(0, 4)}-${digits.slice(4)}`;
		return `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6, 8)}`;
	}

	return (
		<KeyboardAvoidingView
			style={[styles.container, { backgroundColor: theme.bg }]}
			behavior={Platform.select({ ios: "padding", android: "height" })}
		>
			<ScrollView keyboardShouldPersistTaps="handled" keyboardDismissMode="interactive" contentContainerStyle={{ paddingBottom: 120 }}>
				{/* 사진 */}
				<View style={styles.photoBox}>
					<Pressable
						onPress={handlePickImage}
						disabled={busy}
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

					{/* 1단계 로딩 오버레이 */}
					{busy && (
						<View style={styles.busyOverlay}>
							<ActivityIndicator size="large" />
						</View>
					)}
				</View>

				{/* 입력들 */}
				<View style={styles.inputArea}>
					{/* 품종 분류 */}
					<View style={styles.field}>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>품종 분류</Text>
						<TextInput
							placeholder="직접입력 (예: 몬스테라)"
							placeholderTextColor="#909090"
							value={species}
							onChangeText={setSpecies}
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
					<View style={styles.field}>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>내 식물 별명</Text>
						<TextInput
							placeholder="예: 몬몬이"
							placeholderTextColor="#909090"
							value={nickname}
							onChangeText={setNickname}
							style={[styles.input, { color: theme.text, borderColor: theme.border }]}
						/>
					</View>

					{/* 키우기 시작한 날 */}
					<View style={styles.field}>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>키우기 시작한 날</Text>
						<TextInput
							placeholder="YYYY-MM-DD"
							placeholderTextColor="#909090"
							value={startedAt}
							onChangeText={(text) => setStartedAt(formatDateInput(text))}
							keyboardType="number-pad"
							maxLength={10}
							style={[styles.input, { color: theme.text, borderColor: theme.border }]}
						/>
						{startedAt.length > 0 && !isDateLike && (
							<Text style={styles.warn}>YYYY-MM-DD 형식으로 입력해주세요.</Text>
						)}
					</View>
				</View>
			</ScrollView>

			{/* 하단 고정 버튼 영역 */}
			<View style={[styles.bottomBar, { backgroundColor: theme.bg }]}>
				<Pressable onPress={() => router.replace("/(page)/home")} style={[styles.cancelBtn, { borderColor: theme.border }]}>
					<Text style={[styles.cancelText, { color: theme.text }]}>취소</Text>
				</Pressable>

				<Pressable
					disabled={!isAllFilled || !isDateLike}
					onPress={handleSubmit}
					style={[styles.submitBtn, { backgroundColor: !isAllFilled || !isDateLike ? theme.graybg : theme.primary }]}
				>
					<Text style={[styles.submitText, { color: theme.text }]}>등록하기</Text>
				</Pressable>
			</View>

			{/* 2단계: 결과 모달(꾸미기) */}
			<Modal visible={resultVisible} transparent animationType="fade" onRequestClose={() => setResultVisible(false)}>
				<View style={styles.modalBackdrop}>
					<View style={[styles.modalCard, { backgroundColor: theme.bg }]}>
						<Text style={[styles.modalTitle, { color: theme.text }]}>분류 결과</Text>

						<View style={styles.imageDecoBox}>
							<Image source={classifiercharacter} style={styles.imageDeco} resizeMode="contain" />
							<Animated.Image
								source={classifiercharacterWeapon}
								style={[styles.imageWeapon, weaponAnimatedStyle]}
								resizeMode="contain"
							/>
							<Animated.Image
								source={classifiercharacterHand}
								style={[styles.imageHand, handAnimatedStyle]}
								resizeMode="contain"
							/>
						</View>

						<View style={styles.modalRow}>
							<TouchableOpacity
								style={[styles.btn, { backgroundColor: "#5f6368" }]}
								onPress={handlePickImage}
								activeOpacity={0.9}
							>
								<Text style={styles.btnText}>다시 촬영</Text>
							</TouchableOpacity>
							<Pressable
								style={[styles.btn, { backgroundColor: theme.primary, flex: 1 }]}
								onPress={() => setResultVisible(false)}
							>
								<Text style={styles.btnText}>확인</Text>
							</Pressable>
						</View>
					</View>
				</View>
			</Modal>
		</KeyboardAvoidingView>
	);
}

const styles = StyleSheet.create({
	container: { flex: 1 },

	sectionLabel: { fontSize: 16, fontWeight: "700", marginBottom: 8 },
	helper: { fontSize: 12, marginBottom: 8, opacity: 0.8 },

	photoBox: { alignItems: "center", position: "relative", height: 260, marginTop: 12 },
	photo: { position: "absolute", left: 0, top: 0, width: "100%", height: 260, resizeMode: "cover" },
	photoPlaceholder: { width: "100%", height: 260, alignItems: "center", justifyContent: "center" },

	// 1단계 로딩 오버레이
	busyOverlay: {
		position: "absolute",
		left: 0,
		right: 0,
		top: 0,
		bottom: 0,
		alignItems: "center",
		justifyContent: "center",
		backgroundColor: "rgba(0,0,0,0.08)",
		borderRadius: 12,
	},

	inputArea: { paddingHorizontal: 24 },
	field: { marginTop: 24 },
	input: { borderWidth: 1, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 12 },
	notice: { fontSize: 12, marginTop: 6 },
	warn: { fontSize: 12, marginTop: 6, color: "#d93025" },
	smallLabel: { fontSize: 13, fontWeight: "600", marginTop: 8 },
	radioRow: { flexDirection: "row", gap: 8, marginTop: 10 },
	radio: { paddingVertical: 10, paddingHorizontal: 14, borderRadius: 10, borderWidth: 1 },

	bottomBar: {
		position: "absolute",
		left: 0,
		right: 0,
		bottom: 0,
		flexDirection: "row",
		gap: 8,
		padding: 12,
	},
	cancelBtn: { flex: 1, borderWidth: 1, borderRadius: 12, alignItems: "center", justifyContent: "center", paddingVertical: 14 },
	cancelText: { fontSize: 15, fontWeight: "600" },
	submitBtn: { flex: 2, borderRadius: 12, alignItems: "center", justifyContent: "center", paddingVertical: 14 },
	submitText: { fontWeight: "700", fontSize: 16 },
	changeBadge: { position: "absolute", right: 10, bottom: 10, borderWidth: 1, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6 },
	changeBadgeText: { fontSize: 12, fontWeight: "700" },

	/* modal */
	modalBackdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.4)", alignItems: "center", justifyContent: "center", padding: 24 },
	modalCard: { width: "100%", borderRadius: 16, paddingTop: 20, paddingHorizontal: 20, paddingBottom: 20, borderWidth: 1, borderColor: "#e0e0e0" },
	modalTitle: { fontSize: 16, fontWeight: "700", marginBottom: 8 },

	imageDecoBox: { display: "flex", flexDirection: "row", justifyContent: "flex-end", position: "relative" },
	imageDeco: { width: 200, height: 170 },

	// weapon: bottom-right 기준 위치 (무기 크기: 75x70)
	imageWeapon: { position: "absolute", right: 128, bottom: 77, width: 75, height: 70 },

	// hand: 살짝 바운스
	imageHand: { position: "absolute", right: 20, bottom: 73, width: 28 },

	modalRow: { flexDirection: "row", gap: 8, },
	btn: { flex: 1, height: 44, borderRadius: 12, alignItems: "center", justifyContent: "center" },
	btnText: { color: "#fff", fontSize: 15, fontWeight: "700" },
});
