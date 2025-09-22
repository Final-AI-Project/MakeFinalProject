// app/(page)/(stackless)/camera.tsx
// ─────────────────────────────────────────────────────────────────────────────
// ① Imports
// ─────────────────────────────────────────────────────────────────────────────
import React, { useState, useEffect, useRef, useMemo } from "react";
import {
	View,
	Text,
	StyleSheet,
	Image,
	Alert,
	useColorScheme,
	TouchableOpacity,
	ActivityIndicator,
	Platform,
	AccessibilityInfo,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useRouter, Href } from "expo-router";
import Animated, {
	useSharedValue,
	useAnimatedStyle,
	withRepeat,
	withTiming,
	withSequence,
	Easing,
} from "react-native-reanimated";

import Colors from "../../constants/Colors";
import { API_ENDPOINTS, getApiUrl } from "../../config/api";
import { getToken } from "../../libs/auth";
import { showAlert } from "../../components/common/appAlert";
import { startLoading } from "../../components/common/loading";
import ClassifierResultModal, {
	ClassifyResult,
} from "../../components/common/ClassifierResultModal";

// ─────────────────────────────────────────────────────────────────────────────
// ② Constants & Helpers
// ─────────────────────────────────────────────────────────────────────────────
const SPECIES = [
	"몬스테라",
	"스투키",
	"금전수",
	"선인장",
	"호접란",
	"테이블야자",
	"홍콩야자",
	"스파티필럼",
	"관음죽",
	"벵갈고무나무",
	"올리브나무",
	"디펜바키아",
	"보스턴고사리",
];

function mockClassify(_uri: string): ClassifyResult {
	const species = SPECIES[Math.floor(Math.random() * SPECIES.length)];
	const confidence = Math.round(70 + Math.random() * 29); // 70~99%
	return { species, confidence };
}

function fileNameFromUri(uri: string, fallback = "species.jpg") {
	const last = uri.split("/").pop() || fallback;
	return last.split("?")[0];
}

type ModalMode = "result" | null;

// ─────────────────────────────────────────────────────────────────────────────
// ③ Component
// ─────────────────────────────────────────────────────────────────────────────
export default function CameraScreen() {
	const router = useRouter();

	// 3-1) Theme & Animated shared values
	const scheme = useColorScheme();
	const theme = useMemo(
		() => Colors[scheme === "dark" ? "dark" : "light"],
		[scheme]
	);

	const handY = useSharedValue(0);

	// 3-2) Local States (UI & data)
	const [uri, setUri] = useState<string | null>(null);
	const [busy, setBusy] = useState(false);
	const [result, setResult] = useState<ClassifyResult | null>(null);
	const [modalMode, setModalMode] = useState<ModalMode>(null);

	// 안전한 setState를 위한 마운트 플래그
	const mountedRef = useRef(true);
	useEffect(() => {
		mountedRef.current = true;
		return () => {
			mountedRef.current = false;
		};
	}, []);

	// 3-3) Handlers
	const handlePicked = async (pickedUri: string) => {
		if (!pickedUri) return;
		setUri(pickedUri);
		setResult(null);
		setBusy(true);
		
		const apiUrl = getApiUrl(API_ENDPOINTS.AI.CLASSIFY);

		// 전역 로딩 오버레이 시작: 네비게이션 목적 없음 → to를 빈 문자열로 전달
		startLoading(router, {
			to: "" as Href,
			task: async () => {
				try {
					const token = await getToken();
					if (!token) {
						showAlert({ title: "오류", message: "로그인이 필요합니다." });
						setResult(mockClassify(pickedUri));
						return;
					}

					const formData = new FormData();
					formData.append("image", {
						uri: pickedUri,
						type: "image/jpeg",
						name: fileNameFromUri(pickedUri),
					} as any);

					const apiUrl = getApiUrl("/plants/classify-species");
					console.log("[infer] apiUrl =", apiUrl);

					const response = await fetch(apiUrl, {
						method: "POST",
						headers: { Authorization: `Bearer ${token}` }, // RN: Content-Type 자동(boundary)
						body: formData,
					});

					if (!response.ok) {
						throw new Error(`분류 실패: ${response.status}`);
					}

					const data = await response.json();
					console.log("[infer] api raw =", data);

					if (data?.success && data?.species) {
						setResult({
							species: String(data.species),
							confidence: Math.round(Number(data.confidence ?? 85)),
						});
					} else {
						setResult(mockClassify(pickedUri));
					}
				} catch (err) {
					console.error("[infer] error -> mock fallback:", err);
					showAlert({
						title: "분류 실패",
						message: "식물 분류 중 문제가 발생했습니다. (임시 결과 표시)",
					});
					setResult(mockClassify(pickedUri));
				} finally {
					if (!mountedRef.current) return;
					setModalMode("result");
					setBusy(false);
				}
			},
		});
	};

	const askCamera = async () => {
		if (busy) return;
		const { status } = await ImagePicker.requestCameraPermissionsAsync();
		if (status !== "granted") {
			return showAlert({
				title: "권한 필요",
				message: "카메라 권한을 허용해주세요.",
			});
		}
		setBusy(true);
		try {
			const res = await ImagePicker.launchCameraAsync({
				quality: 0.85,
				exif: false,
				base64: false,
				allowsEditing: false,
			});
			if (!res.canceled) handlePicked(res.assets[0].uri);
		} finally {
			setBusy(false);
		}
	};

	const askGallery = async () => {
		if (busy) return;
		const { status } =
			await ImagePicker.requestMediaLibraryPermissionsAsync();
		if (status !== "granted") {
			return showAlert({
				title: "권한 필요",
				message: "갤러리 접근 권한을 허용해주세요.",
			});
		}
		setBusy(true);
		try {
			const res = await ImagePicker.launchImageLibraryAsync({
				quality: 0.85,
				exif: false,
				base64: false,
				allowsEditing: false,
			});
			if (!res.canceled) handlePicked(res.assets[0].uri);
		} finally {
			setBusy(false);
		}
	};

	const clearImage = () => {
		if (busy) return;
		setUri(null);
		setResult(null);
		setModalMode(null);
	};

	// 3-4) Effects: 최초 진입 시 카메라 자동 실행(1회)
	const didAutoOpen = useRef(false);
	useEffect(() => {
		if (didAutoOpen.current) return;
		didAutoOpen.current = true;
		// 접근성 모드에선 자동 실행을 피함(사용자 통제 우선)
		AccessibilityInfo.isScreenReaderEnabled().then((enabled) => {
			if (enabled) return;
			setTimeout(() => {
				askCamera().catch(() => {});
			}, 0);
		});
	}, []);

	// 3-5) Small animation (optional)
	useEffect(() => {
		handY.value = withRepeat(
			withSequence(
				withTiming(-2, { duration: 250, easing: Easing.inOut(Easing.quad) }),
				withTiming(0, { duration: 600, easing: Easing.inOut(Easing.quad) }),
				withTiming(0, { duration: 250, easing: Easing.inOut(Easing.quad) })
			),
			-1,
			false
		);
	}, []);
	const handAnimatedStyle = useAnimatedStyle(() => ({
		transform: [{ translateY: handY.value }],
	}));

	// 3-6) Render
	return (
		<View style={[styles.container, { backgroundColor: theme.bg }]}>
			{/* Preview */}
			<View style={styles.previewWrap} accessibilityLabel="사진 미리보기 영역">
				{busy ? (
					<ActivityIndicator size="large" />
				) : uri ? (
					<Image source={{ uri }} style={styles.preview} />
				) : (
					<Text style={{ color: "#909090" }}>
						이미지를 선택하거나 촬영해 주세요.
					</Text>
				)}
			</View>

			{/* Controls */}
			<View style={styles.row}>
				<TouchableOpacity
					style={[
						styles.btn,
						{ backgroundColor: theme.primary, opacity: busy ? 0.6 : 1 },
					]}
					onPress={askCamera}
					activeOpacity={0.9}
					disabled={busy}
					accessibilityRole="button"
					accessibilityLabel="카메라 촬영"
				>
					<Text style={styles.btnText}>촬영</Text>
				</TouchableOpacity>

				<TouchableOpacity
					style={[
						styles.btn,
						{ backgroundColor: "#5f6368", opacity: busy ? 0.6 : 1 },
					]}
					onPress={askGallery}
					activeOpacity={0.9}
					disabled={busy}
					accessibilityRole="button"
					accessibilityLabel="갤러리에서 선택"
				>
					<Text style={styles.btnText}>갤러리</Text>
				</TouchableOpacity>

				{uri && (
					<TouchableOpacity
						style={[
							styles.btn,
							{ backgroundColor: "#d32f2f", opacity: busy ? 0.6 : 1 },
						]}
						onPress={clearImage}
						activeOpacity={0.9}
						disabled={busy}
						accessibilityRole="button"
						accessibilityLabel="초기화"
					>
						<Text style={styles.btnText}>↺ 초기화</Text>
					</TouchableOpacity>
				)}
			</View>

			{/* Result Modal */}
			<ClassifierResultModal
				visible={modalMode === "result"}
				theme={theme}
				result={result}
				onClose={() => setModalMode(null)}
				onRetake={askCamera}
			/>

			{/* Decorative tiny bar (kept) */}
			<Animated.View style={[{ height: 2 }, handAnimatedStyle]} />
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
	btn: {
		flex: 1,
		height: 44,
		borderRadius: 12,
		alignItems: "center",
		justifyContent: "center",
	},
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
