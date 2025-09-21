// app/(page)/(stackless)/camera.tsx
// ─────────────────────────────────────────────────────────────────────────────
// ① Imports
// ─────────────────────────────────────────────────────────────────────────────
import React, { useState, useEffect, useRef } from "react";
import { View, Text, StyleSheet, Image, Alert, useColorScheme, TouchableOpacity, ActivityIndicator } from "react-native";
import * as ImagePicker from "expo-image-picker";
import Colors from "../../constants/Colors";
import Animated, { useSharedValue, useAnimatedStyle, withRepeat, withTiming, withSequence, withDelay, Easing } from "react-native-reanimated";
import { getApiUrl } from "../../config/api";
import { getToken } from "../../libs/auth";

// 공통 모달
import ClassifierResultModal, { ClassifyResult } from "../../components/common/ClassifierResultModal";

// ─────────────────────────────────────────────────────────────────────────────
// ② Constants & Mock
// ─────────────────────────────────────────────────────────────────────────────
const SPECIES = [
	"몬스테라","스투키","금전수","선인장","호접란","테이블야자",
	"홍콩야자","스파티필럼","관음죽","벵갈고무나무","올리브나무","디펜바키아","보스턴고사리",
];

// (모델 미연동) 가짜 분류기
function mockClassify(_uri: string): ClassifyResult {
	const species = SPECIES[Math.floor(Math.random() * SPECIES.length)];
	const confidence = Math.round(70 + Math.random() * 29); // 70~99%
	return { species, confidence };
}

// ─────────────────────────────────────────────────────────────────────────────
// ③ Component
// ─────────────────────────────────────────────────────────────────────────────
export default function CameraScreen() {
	// 3-1) Theme & Animated shared values
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const weaponAngle = useSharedValue(0);
	const handY = useSharedValue(0);
	const W = 75, H = 70;

	// 3-2) Local States (UI & data)
	const [uri, setUri] = useState<string | null>(null);
	const [busy, setBusy] = useState(false);

	// 결과 모달 상태
	const [resultVisible, setResultVisible] = useState(false);
	const [result, setResult] = useState<ClassifyResult | null>(null);

	// 3-3) Handlers: 이미지 선택/초기화/카메라·갤러리 권한
	const handlePicked = async (pickedUri: string) => {
		setUri(pickedUri);
		setBusy(true);
		
		try {
			// 실제 백엔드 API 호출
			const token = await getToken();
			if (!token) {
				Alert.alert("오류", "로그인이 필요합니다.");
				return;
			}

			const formData = new FormData();
			formData.append("image", {
				uri: pickedUri,
				type: "image/jpeg",
				name: "species.jpg",
			} as any);

			const apiUrl = await getApiUrl("/plants/classify-species");
			const response = await fetch(apiUrl, {
				method: "POST",
				body: formData,
				headers: {
					Authorization: `Bearer ${token}`,
					"Content-Type": "multipart/form-data",
				},
			});

			if (!response.ok) {
				throw new Error(`분류 실패: ${response.status}`);
			}

			const result = await response.json();
			if (result.success && result.species) {
				setResult({
					species: result.species,
					confidence: result.confidence || 85,
				});
				setResultVisible(true);
			} else {
				throw new Error("분류 결과를 받을 수 없습니다.");
			}
		} catch (error) {
			console.error("분류 오류:", error);
			Alert.alert("분류 실패", "식물 분류 중 문제가 발생했습니다.");
			// 실패 시 모의 분류 결과 사용
			const r = mockClassify(pickedUri);
			setResult(r);
			setResultVisible(true);
		} finally {
			setBusy(false);
		}
	};

	const askCamera = async () => {
		const { status } = await ImagePicker.requestCameraPermissionsAsync();
		if (status !== "granted") {
			return Alert.alert("권한 필요", "카메라 권한을 허용해주세요.");
		}
		setBusy(true);
		try {
			const res = await ImagePicker.launchCameraAsync({
				quality: 0.85, exif: false, base64: false, allowsEditing: false,
			});
			if (!res.canceled) handlePicked(res.assets[0].uri);
		} finally {
			setBusy(false);
		}
	};

	const askGallery = async () => {
		const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
		if (status !== "granted") {
			return Alert.alert("권한 필요", "갤러리 접근 권한을 허용해주세요.");
		}
		setBusy(true);
		try {
			const res = await ImagePicker.launchImageLibraryAsync({
				quality: 0.85, exif: false, base64: false, allowsEditing: false,
			});
			if (!res.canceled) handlePicked(res.assets[0].uri);
		} finally {
			setBusy(false);
		}
	};

	const clearImage = () => {
		setUri(null);
		setResult(null);
		setResultVisible(false);
	};

	// 3-4) Effects: 최초 진입 시 카메라 자동 실행(1회)
	const didAutoOpen = useRef(false);
	useEffect(() => {
		if (didAutoOpen.current) return;
		didAutoOpen.current = true;
		setTimeout(() => { askCamera().catch(() => {}); }, 0);
	}, []);

	// 3-5) Animations (페이지 내 요소 용도이면 유지 — 여기서는 스타일만 남겨둠)
	useEffect(() => {
		// 페이지의 다른 요소용 애니가 있었다면 유지
		handY.value = withRepeat(
			withSequence(
				withTiming(-2, { duration: 250, easing: Easing.inOut(Easing.quad) }),
				withTiming(0,	{ duration: 600, easing: Easing.inOut(Easing.quad) }),
				withTiming(0,	{ duration: 250, easing: Easing.inOut(Easing.quad) }),
			),
			-1, false
		);
	}, []);

	const handAnimatedStyle = useAnimatedStyle(() => ({
		transform: [{ translateY: handY.value }],
	}));

	// 3-6) Render
	return (
		<View style={[styles.container, { backgroundColor: theme.bg }]}>
			{/* Preview */}
			<View style={styles.previewWrap}>
				{busy ? (
					<ActivityIndicator size="large" />
				) : uri ? (
					<Image source={{ uri }} style={styles.preview} />
				) : (
					<Text style={{ color: "#909090" }}>이미지를 선택하거나 촬영해 주세요.</Text>
				)}
			</View>

			{/* Controls */}
			<View style={styles.row}>
				<TouchableOpacity style={[styles.btn, { backgroundColor: theme.primary }]} onPress={askCamera} activeOpacity={0.9}>
					<Text style={styles.btnText}>촬영</Text>
				</TouchableOpacity>
				<TouchableOpacity style={[styles.btn, { backgroundColor: "#5f6368" }]} onPress={askGallery} activeOpacity={0.9}>
					<Text style={styles.btnText}>갤러리</Text>
				</TouchableOpacity>
				{uri && (
					<TouchableOpacity style={[styles.btn, { backgroundColor: "#d32f2f" }]} onPress={clearImage} activeOpacity={0.9}>
						<Text style={styles.btnText}>↺ 초기화</Text>
					</TouchableOpacity>
				)}
			</View>

			{/* Result Modal (공통 컴포넌트) */}
			<ClassifierResultModal
				visible={resultVisible}
				theme={theme}
				result={result}
				onClose={() => setResultVisible(false)}
				onRetake={askCamera}
			/>
		</View>
	);
}

// ─────────────────────────────────────────────────────────────────────────────
// ④ Styles
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
	container: { flex: 1, paddingHorizontal: 24, paddingBottom: 72 },

	// Controls
	row: { flexDirection: "row", gap: 8, marginTop: 12 },
	btn: { flex: 1, height: 44, borderRadius: 12, alignItems: "center", justifyContent: "center" },
	btnText: { color: "#fff", fontSize: 15, fontWeight: "700" },

	// Preview
	previewWrap: {
		flex: 1,
		borderWidth: 1,
		borderColor: "#e0e0e0",
		borderRadius: 12,
		alignItems: "center",
		justifyContent: "center",
		overflow: "hidden",
	},
	preview: { width: "100%", height: "100%", resizeMode: "cover" },
});
