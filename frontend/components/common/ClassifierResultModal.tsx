// components/common/ClassifierResultModal.tsx
import React, { useEffect } from "react";
import { View, Text, StyleSheet, Image, Modal, ActivityIndicator, TouchableOpacity, Pressable } from "react-native";
import Animated, {
	useSharedValue,
	useAnimatedStyle,
	withRepeat,
	withSequence,
	withTiming,
	withDelay,
	Easing,
	cancelAnimation,
} from "react-native-reanimated";

// 데코 이미지 (프로젝트 경로에 맞춰 유지)
import classifiercharacter from "../../assets/images/classifier_setting.png";
import classifiercharacterWeapon from "../../assets/images/classifier_weapon.png";
import classifiercharacterHand from "../../assets/images/classifier_hand.png";

export type ClassifyResult = { species: string; confidence: number };

type ThemeLike = {
	bg: string;
	text: string;
	primary?: string;
};

type Props = {
	visible: boolean;
	theme: ThemeLike;
	result: ClassifyResult | null;	 // 결과 없으면 로더 노출
	onClose: () => void;						 // "확인" 클릭
	onRetake: () => void;						// "다시 촬영" 클릭
};

export default function ClassifierResultModal({
	visible,
	theme,
	result,
	onClose,
	onRetake,
}: Props) {
	// 애니메이션 공유값
	const weaponAngle = useSharedValue(0);
	const handY = useSharedValue(0);
	const W = 75, H = 70;

	// 애니 루프
	function startWeaponLoop({
		startDelay = 300,
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
		weaponAngle.value = withDelay(startDelay, withRepeat(seq, -1, false));
	}

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

	// 모달 열릴 때 시작 / 닫힐 때 정지
	useEffect(() => {
		if (visible) {
			startWeaponLoop();
			startHandLoop();
		} else {
			cancelAnimation(weaponAngle);
			cancelAnimation(handY);
			weaponAngle.value = 0;
			handY.value = 0;
		}
	}, [visible]);

	const weaponAnimatedStyle = useAnimatedStyle(() => ({
		transform: [
			{ translateX:	(W / 2) + 10 },
			{ translateY:	(H / 2) + 10 },
			{ rotate: `${weaponAngle.value}deg` },
			{ translateX: -(W / 2) + 10 },
			{ translateY: -(H / 2) + 10 },
		],
	}));

	const handAnimatedStyle = useAnimatedStyle(() => ({
		transform: [{ translateY: handY.value }],
	}));

	return (
		<Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
			<View style={styles.modalBackdrop}>
				<View style={[styles.modalCard, { backgroundColor: theme.bg }]}>
					<Text style={[styles.modalTitle, { color: theme.text }]}>분류 결과</Text>

					{result ? (
						<>
							<Text style={[styles.modalSpecies, { color: theme.text }]}>{result.species}</Text>
							<Text style={styles.modalSub}>신뢰도 {result.confidence}%</Text>
						</>
					) : (
						<ActivityIndicator />
					)}

					{/* 캐릭터 데코 + 애니메이션 (카메라와 동일 스타일) */}
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

					{/* actions */}
					<View style={styles.modalRow}>
						<TouchableOpacity
							style={[styles.btn, { backgroundColor: "#5f6368" }]}
							onPress={onRetake}
							activeOpacity={0.9}
						>
							<Text style={styles.btnText}>다시 촬영</Text>
						</TouchableOpacity>
						<Pressable
							style={[styles.btn, { backgroundColor: theme.primary || "#6a9eff", flex: 1 }]}
							onPress={onClose}
						>
							<Text style={styles.btnText}>확인</Text>
						</Pressable>
					</View>
				</View>
			</View>
		</Modal>
	);
}

const styles = StyleSheet.create({
	// Modal: layout & text (카메라와 동일)
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
		paddingBottom: 20,
		borderWidth: 1,
		borderColor: "#e0e0e0",
	},
	modalTitle: { fontSize: 16, fontWeight: "700", marginBottom: 8 },
	modalSpecies: { fontSize: 22, fontWeight: "800", marginTop: 4 },
	modalSub: { color: "#6b6b6b", marginTop: 6 },
	modalRow: { flexDirection: "row", gap: 8 },

	// Modal: character decoration (카메라 파일 기준)
	imageDecoBox: {
		display: "flex",
		flexDirection: "row",
		justifyContent: "flex-end",
		position: "relative",
	},
	imageDeco: { width: 200, height: 170 },
	imageWeapon: { position: "absolute", right: 148, bottom: 99, width: 75, height: 70 },
	imageHand: { position: "absolute", right: 20, bottom: 73, width: 28 },

	// shared button
	btn: { flex: 1, height: 44, borderRadius: 12, alignItems: "center", justifyContent: "center" },
	btnText: { color: "#fff", fontSize: 15, fontWeight: "700" },
});
