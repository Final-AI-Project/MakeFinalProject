import React, { useMemo, useRef, useState } from "react";
import {
	View,
	Text,
	StyleSheet,
	Image,
	Pressable,
	Animated,
	Easing,
	useColorScheme,
	LayoutChangeEvent,
} from "react-native";
import Colors from "../../constants/Colors";

type Props = {
	photoUri?: string | null;
	nickname: string;                 // 내 식물 별명
	diagnosedAt: string;              // 진단 날짜 문자열 (예: 2025-09-18)
	diseaseName: string;              // 병충해 이름
	children?: React.ReactNode;       // 펼쳤을 때 표시할 상세 내용
	imageSize?: number;               // 왼쪽 사진 가로/세로 (기본 72)
	border?: boolean;                 // 외곽선 on/off (기본 true)
	rounded?: number;                 // 라운드 (기본 12)
};

export default function DiseaseAccordionCard({
	photoUri,
	nickname,
	diagnosedAt,
	diseaseName,
	children,
	imageSize = 72,
	border = true,
	rounded = 12,
}: Props) {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];

	const [open, setOpen] = useState(false);
	const rotate = useRef(new Animated.Value(0)).current;
	const height = useRef(new Animated.Value(0)).current;
	const contentH = useRef(0);

	const arrowRotate = rotate.interpolate({
		inputRange: [0, 1],
		outputRange: ["0deg", "180deg"],
	});

	function toggle() {
		const toVal = open ? 0 : 1;
		setOpen(!open);
		Animated.parallel([
			Animated.timing(rotate, {
				toValue: toVal,
				duration: 200,
				useNativeDriver: true,
				easing: Easing.out(Easing.quad),
			}),
			Animated.timing(height, {
				toValue: open ? 0 : contentH.current,
				duration: 220,
				useNativeDriver: false,
				easing: Easing.out(Easing.quad),
			}),
		]).start();
	}

	function onContentLayout(e: LayoutChangeEvent) {
		// 펼침 영역의 실제 높이를 최초 1회 저장
		if (contentH.current === 0) {
			contentH.current = e.nativeEvent.layout.height;
			// 처음엔 접힌 상태이므로 height=0으로 시작 (이미 설정되어 있음)
		}
	}

	const boxStyle = useMemo(
		() => [
			styles.card,
			{
				borderColor: border ? theme.border : "transparent",
				backgroundColor: theme.bg,
				borderRadius: rounded,
			},
		],
		[theme, border, rounded]
	);

	return (
		<View style={boxStyle}>
			{/* 상단 본문 (사진 + 텍스트 2줄) */}
			<View style={styles.row}>
				{/* 왼쪽 사진 */}
				<View style={styles.leftCol}>
					<View
						style={[
							styles.photoWrap,
							{
								width: imageSize,
								height: imageSize,
								borderRadius: 8,
								borderColor: theme.border,
							},
						]}
					>
						{photoUri ? (
							<Image
								source={{ uri: photoUri }}
								style={{ width: "100%", height: "100%", borderRadius: 8 }}
								resizeMode="cover"
							/>
						) : (
							<View style={[styles.photoPlaceholder]}>
								<Text style={{ color: theme.text }}>사진</Text>
							</View>
						)}
					</View>
				</View>

				{/* 오른쪽 상/하 텍스트 박스 */}
				<View style={styles.rightCol}>
					<View
						style={[
							styles.topBox,
							{ borderColor: theme.border, backgroundColor: theme.bg, borderTopRightRadius: 8 },
						]}
					>
						<Text numberOfLines={1} style={[styles.titleText, { color: theme.text }]}>
							{nickname} / {diagnosedAt}
						</Text>
					</View>

					<View
						style={[
							styles.bottomBox,
							{ borderColor: theme.border, backgroundColor: theme.bg, borderBottomRightRadius: 8 },
						]}
					>
						<Text numberOfLines={1} style={[styles.diseaseText, { color: theme.text }]}>
							{diseaseName}
						</Text>
					</View>
				</View>
			</View>

			{/* 중앙 하단 화살표 */}
			<Pressable onPress={toggle} style={styles.arrowBtn} hitSlop={8}>
				<Animated.View style={{ transform: [{ rotate: arrowRotate }] }}>
					<Text style={[styles.arrowIcon, { color: theme.text }]}>▼</Text>
				</Animated.View>
			</Pressable>

			{/* 아코디언 펼침 영역 */}
			<Animated.View style={{ overflow: "hidden", height }}>
				{/* 실제 콘텐츠는 자연 높이를 측정하기 위해 한 번 렌더링해두고 감춥니다 */}
				<View onLayout={onContentLayout} style={{ paddingTop: 8, paddingBottom: 12 }}>
					{children ? (
						children
					) : (
						<Text style={{ color: theme.text, lineHeight: 20 }}>
							여기에 처방, 원인, 주의사항 등 상세 내용을 넣어주세요.
						</Text>
					)}
				</View>
			</Animated.View>
		</View>
	);
}

const styles = StyleSheet.create({
	card: {
		padding: 12,
		borderWidth: 1,
	},
	row: {
		flexDirection: "row",
		alignItems: "stretch",
	},
	leftCol: {
		marginRight: 10,
		justifyContent: "center",
	},
	photoWrap: {
		borderWidth: 1,
		overflow: "hidden",
		backgroundColor: "#ddd",
		alignItems: "center",
		justifyContent: "center",
	},
	photoPlaceholder: {
		flex: 1,
		alignItems: "center",
		justifyContent: "center",
	},
	rightCol: {
		flex: 1,
	},
	topBox: {
		borderWidth: 1,
		paddingHorizontal: 10,
		paddingVertical: 8,
	},
	bottomBox: {
		borderWidth: 1,
		paddingHorizontal: 10,
		paddingVertical: 8,
		marginTop: 6,
	},
	titleText: {
		fontSize: 15,
		fontWeight: "600",
	},
	diseaseText: {
		fontSize: 15,
		fontWeight: "500",
	},
	arrowBtn: {
		alignSelf: "center",
		marginTop: 8,
		padding: 6,
		borderRadius: 8,
	},
	arrowIcon: {
		fontSize: 18,
	},
});
