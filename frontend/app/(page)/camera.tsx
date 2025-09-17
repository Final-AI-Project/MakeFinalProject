// 파일: app/(page)/(stackless)/camera.tsx
import React, { useState, useEffect, useRef } from "react";
import { View, Text, StyleSheet, Image, Alert, useColorScheme, TouchableOpacity, ActivityIndicator, Modal } from "react-native";
import * as ImagePicker from "expo-image-picker";
import Colors from "../../constants/Colors";
import classifiercharacter from "../../assets/images/classifier_setting.png";
import classifiercharacterWeapon from "../../assets/images/classifier_weapon.png";
import classifiercharacterHand from "../../assets/images/classifier_hand.png";
import Animated, {
	useSharedValue,
	useAnimatedStyle,
	withRepeat,
	withTiming,
	withSequence,
	withDelay,
	Easing,
} from "react-native-reanimated";

const SPECIES = [
	"몬스테라","스투키","금전수","선인장","호접란","테이블야자",
	"홍콩야자","스파티필럼","관음죽","벵갈고무나무","올리브나무","디펜바키아","보스턴고사리",
];

// 🔹 (모델 미연동) 가짜 분류기
function mockClassify(_uri: string) {
	const species = SPECIES[Math.floor(Math.random() * SPECIES.length)];
	const confidence = Math.round(70 + Math.random() * 29); // 70~99%
	return { species, confidence };
}

export default function CameraScreen() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const weaponAngle = useSharedValue(0);
	const handY = useSharedValue(0);
	const W = 75, H = 70;

	const [weaponSize, setWeaponSize] = useState({ w: 0, h: 0 });
	const [uri, setUri] = useState<string | null>(null);
	const [busy, setBusy] = useState(false);

	// 🔹 결과 모달 상태
	const [resultVisible, setResultVisible] = useState(false);
	const [result, setResult] = useState<{ species: string; confidence: number } | null>(null);

	const handlePicked = (pickedUri: string) => {
		setUri(pickedUri);
		// 1단계 로딩(busy)이 끝난 뒤, 2단계 모달을 띄우기 위해 살짝 지연
		setTimeout(() => {
			const r = mockClassify(pickedUri);
			setResult(r);
			setResultVisible(true);
		}, 80);
	};

	const askCamera = async () => {
		const { status } = await ImagePicker.requestCameraPermissionsAsync();
		if (status !== "granted") {
			return Alert.alert("권한 필요", "카메라 권한을 허용해주세요.");
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
		const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
		if (status !== "granted") {
			return Alert.alert("권한 필요", "갤러리 접근 권한을 허용해주세요.");
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
		setUri(null);
		setResult(null);
		setResultVisible(false);
	};

	// 🔹 페이지 진입 즉시 카메라 실행(1회)
	const didAutoOpen = useRef(false);
	useEffect(() => {
		if (didAutoOpen.current) return;
		didAutoOpen.current = true;
		setTimeout(() => { askCamera().catch(() => {}); }, 0);
	}, []);

	function startWeaponLoop({
		startDelay = 0,
		hold = 200,
		up = 220,
		down = 220,
	} = {}) {
		weaponAngle.value = 0;

		const seq = withSequence(
			withTiming(45, { duration: up, easing: Easing.out(Easing.cubic) }),
			withDelay(hold, withTiming(0, { duration: down, easing: Easing.in(Easing.cubic) })),
			withDelay(hold, withTiming(0, { duration: 0 }))
		);

		weaponAngle.value = startDelay
		? withDelay(startDelay, withRepeat(seq, -1, false))
		: withRepeat(seq, -1, false);
	}

	useEffect(() => {
		startWeaponLoop({ startDelay: 300, hold: 200, up: 220, down: 220 });
	}, []);

	useEffect(() => {
		// 위로 3px → 원위치 반복
		handY.value = withRepeat(
			withSequence(
				withTiming(-2, { duration: 250, easing: Easing.inOut(Easing.quad) }),
				withTiming(0,  { duration: 600, easing: Easing.inOut(Easing.quad) }),
				withTiming(0,  { duration: 250, easing: Easing.inOut(Easing.quad) })
			),
			-1,
			false
		);
	}, []);

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

	return (
		<View style={[styles.container, { backgroundColor: theme.bg }]}>
			<View style={styles.previewWrap}>
				{busy ? (
					<ActivityIndicator size="large" />
				) : uri ? (
					<Image source={{ uri }} style={styles.preview} />
				) : (
					<Text style={{ color: "#909090" }}>이미지를 선택하거나 촬영해 주세요.</Text>
				)}
			</View>

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

			{/* 🔹 2단계: 분류 결과 모달 */}
			<Modal visible={resultVisible} transparent animationType="fade" onRequestClose={() => setResultVisible(false)}>
				<View style={styles.modalBackdrop}>
					<View style={[styles.modalCard, { backgroundColor: theme.bg }]}>
						<Text style={[styles.modalTitle, { color: theme.text }]}>분류 결과</Text>
						{result ? (
							<>
								<Text style={[styles.modalSpecies, { color: theme.text }]}>{result.species}</Text>
								<Text style={styles.modalSub}>신뢰도 {result.confidence}%</Text>
								<View style={styles.imageDecoBox}>
									<Image source={ classifiercharacter } style={styles.imageDeco} resizeMode="contain" />
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
							</>
						) : (
							<ActivityIndicator />
						)}

						<View style={styles.modalRow}>
							<TouchableOpacity
								style={[styles.btn, { backgroundColor: theme.primary }]}
								onPress={() => setResultVisible(false)}
								activeOpacity={0.9}
							>
								<Text style={styles.btnText}>확인</Text>
							</TouchableOpacity>
							<TouchableOpacity
								style={[styles.btn, { backgroundColor: "#5f6368" }]}
								onPress={askCamera}
								activeOpacity={0.9}
							>
								<Text style={styles.btnText}>다시 촬영</Text>
							</TouchableOpacity>
						</View>
					</View>
				</View>
			</Modal>
		</View>
	);
}

const styles = StyleSheet.create({
	container: { flex: 1, paddingHorizontal: 24, paddingBottom: 72 },
	row: { flexDirection: "row", gap: 8, marginTop: 12 },
	btn: { flex: 1, height: 44, borderRadius: 12, alignItems: "center", justifyContent: "center" },
	btnText: { color: "#fff", fontSize: 15, fontWeight: "700" },
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

	/* modal */
	modalBackdrop: {
		flex: 1,
		backgroundColor: "rgba(0,0,0,0.4)",
		alignItems: "center",
		justifyContent: "center",
		padding: 24,
	},
	modalCard: {
		width: "100%",
		borderRadius: 16,
		paddingTop: 20,
		paddingHorizontal: 20,
		paddingBottom:20,
		borderWidth: 1,
		borderColor: "#e0e0e0",
	},
	modalTitle: { fontSize: 16, fontWeight: "700", marginBottom: 8 },
	modalSpecies: { fontSize: 22, fontWeight: "800", marginTop: 4 },
	modalSub: { color: "#6b6b6b", marginTop: 6 },
	modalRow: { flexDirection: "row", gap: 8, },
	imageDecoBox: {
		display:'flex',
		flexDirection:'row',
		justifyContent:'flex-end',
		position:'relative',
	},
	imageDeco: {
		width:200,
		height:170,
	},
	imageWeapon: {
		position:'absolute',
		right:148,
		bottom:99,
		width:75,
		height:70,
	},
	imageHand: {
		position:'absolute',
		right:20,
		bottom:73,
		width:28,
	},
});
