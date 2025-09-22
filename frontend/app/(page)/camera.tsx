// app/(page)/(stackless)/camera.tsx
// ─────────────────────────────────────────────────────────────────────────────
// ① Imports
// ─────────────────────────────────────────────────────────────────────────────
import React, { useState, useEffect, useRef } from "react";
import { View, Text, StyleSheet, Image, Alert, useColorScheme, TouchableOpacity, ActivityIndicator } from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useRouter } from "expo-router";
import Colors from "../../constants/Colors";
import Animated, { useSharedValue, useAnimatedStyle, withRepeat, withTiming, withSequence, Easing } from "react-native-reanimated";
import { getApiUrl } from "../../config/api";
import { getToken } from "../../libs/auth";
import { showAlert } from "../../components/common/appAlert";

// 전역 로딩 오버레이 API
import { startLoading } from "../../components/common/loading";
import type { Href } from "expo-router";

// 결과 모달
import ClassifierResultModal, { ClassifyResult } from "../../components/common/ClassifierResultModal";

// ─────────────────────────────────────────────────────────────────────────────
// ② Constants & Helpers
// ─────────────────────────────────────────────────────────────────────────────
const SPECIES = [
	"몬스테라","스투키","금전수","선인장","호접란","테이블야자",
	"홍콩야자","스파티필럼","관음죽","벵갈고무나무","올리브나무","디펜바키아","보스턴고사리",
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

type ModalMode = "result" | null; // 로딩은 전역 오버레이로 대체

// ─────────────────────────────────────────────────────────────────────────────
// ③ Component
// ─────────────────────────────────────────────────────────────────────────────
export default function CameraScreen() {
	const router = useRouter();

	// 3-1) Theme & Animated shared values
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const handY = useSharedValue(0);

	// 3-2) Local States (UI & data)
	const [uri, setUri] = useState<string | null>(null);
	const [busy, setBusy] = useState(false);

	// 결과 + 모달 모드
	const [result, setResult] = useState<ClassifyResult | null>(null);
	const [modalMode, setModalMode] = useState<ModalMode>(null);

	// 3-3) Handlers
	const handlePicked = async (pickedUri: string) => {
		setUri(pickedUri);
		setResult(null);
		setBusy(true);

		// 전역 로딩 오버레이 시작: 네비게이션 목적 없음 → to를 빈 문자열로 전달
		startLoading(router, {
			to: "" as Href,
			// message를 비우면 loading.tsx가 랜덤 메시지를 순환해서 보여줌
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
					const response = await fetch(apiUrl, {
						method: "POST",
						headers: { Authorization: `Bearer ${token}` }, // ⚠ Content-Type X
						body: formData,
					});

					if (!response.ok) throw new Error(`분류 실패: ${response.status}`);

					const data = await response.json();
					if (data?.success && data?.species) {
						setResult({
							species: data.species,
							confidence: Math.round(data.confidence ?? 85),
						});
					} else {
						setResult(mockClassify(pickedUri));
					}
				} catch (err) {
					console.error("[infer] error:", err);
					showAlert({ title: "분류 실패", message: "식물 분류 중 문제가 발생했습니다. (임시 결과 표시)" });
					setResult(mockClassify(pickedUri));
				} finally {
					// 전역 로딩은 startLoading 내부 finally에서 자동으로 꺼짐
					setModalMode("result"); // 결과 모달 표시
					setBusy(false);
				}
			},
			// timeoutMs: 0  // 필요 시 강제 종료 및 네비게이션에 사용
		});
	};

	const askCamera = async () => {
		const { status } = await ImagePicker.requestCameraPermissionsAsync();
		if (status !== "granted") {
			return showAlert({ title: "권한 필요", message: "카메라 권한을 허용해주세요." });
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
			return showAlert({ title: "권한 필요", message: "갤러리 접근 권한을 허용해주세요." });
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
		setModalMode(null);
	};

	// 3-4) Effects: 최초 진입 시 카메라 자동 실행(1회)
	const didAutoOpen = useRef(false);
	useEffect(() => {
		if (didAutoOpen.current) return;
		didAutoOpen.current = true;
		setTimeout(() => { askCamera().catch(() => {}); }, 0);
	}, []);

	// 3-5) Small animation (optional)
	useEffect(() => {
		handY.value = withRepeat(
			withSequence(
				withTiming(-2, { duration: 250, easing: Easing.inOut(Easing.quad) }),
				withTiming(0,  { duration: 600, easing: Easing.inOut(Easing.quad) }),
				withTiming(0,  { duration: 250, easing: Easing.inOut(Easing.quad) }),
			),
			-1, false
		);
	}, []);
	const handAnimatedStyle = useAnimatedStyle(() => ({ transform: [{ translateY: handY.value }] }));

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

			{/* 결과 모달 */}
			<ClassifierResultModal
				visible={modalMode === "result"}
				theme={theme}
				result={result}
				onClose={() => setModalMode(null)}
				onRetake={askCamera}
			/>

			{/* (예시) 페이지 내 작은 데코 요소에 사용할 수 있음 */}
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
