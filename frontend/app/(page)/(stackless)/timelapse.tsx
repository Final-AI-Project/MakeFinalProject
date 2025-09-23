// app/(page)/timelapse.tsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
	View,
	Text,
	StyleSheet,
	Pressable,
	useColorScheme,
	Animated,
	Image,
	Easing,
} from "react-native";
import { Video, ResizeMode } from "expo-av";
import Colors from "../../../constants/Colors";
import timelapseDeco from "../../../assets/images/timelapse_setting.png";
import timelapseDecoCircles from "../../../assets/images/timelapse_deco_setting.png";
import monsteraStable from "../../../assets/images/monstera_stable.mp4";
import { useRouter } from "expo-router";

type Plant = {
	id: string;
	name: string;        // 내 식물 별명
	species: string;     // 품종명 (예: 몬스테라)
	videoUri?: string;   // 타임랩스 비디오 URL(데모)
};

export default function HomeTimelapsePage() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];

	// 더미 “내 식물” 목록
	const myPlants: Plant[] = useMemo(
		() => [
			{
				id: "p1",
				name: "초코",
				species: "몬스테라",
				videoUri: "https://d23dyxeqlo5psv.cloudfront.net/big_buck_bunny.mp4",
			},
			{
				id: "p2",
				name: "토리",
				species: "올리브나무",
			},
			{
				id: "p3",
				name: "나나",
				species: "스투키",
			},
		],
		[]
	);

	const [openDrop, setOpenDrop] = useState(false);
	const [selected, setSelected] = useState<Plant | null>(null);
	const [generating, setGenerating] = useState(false);
	const [showVideo, setShowVideo] = useState(false);
	const router = useRouter();

	// 4초 타이머
	const timerRef = useRef<NodeJS.Timeout | null>(null);
	useEffect(() => {
		return () => {
			if (timerRef.current) clearTimeout(timerRef.current);
		};
	}, []);

	const handleSelect = (p: Plant) => {
		setSelected(p);
		setOpenDrop(false);
		// 초기화
		setShowVideo(false);
		if (timerRef.current) clearTimeout(timerRef.current);

		// 몬스테라면 4초 생성중 후 동영상 교체
		if (p.species === "몬스테라") {
			setGenerating(true);
			timerRef.current = setTimeout(() => {
				setGenerating(false);
				setShowVideo(true);
			}, 6000);
		} else {
			setGenerating(false);
			setShowVideo(false);
		}
	};

	// 무한 회전 애니메이션
	const spinAnim = React.useRef(new Animated.Value(0)).current;

	React.useEffect(() => {
		const loop = Animated.loop(
			Animated.timing(spinAnim, {
				toValue: -1,
				duration: 800,
				easing: Easing.linear,
				useNativeDriver: true,
			})
		);
		loop.start();
		return () => loop.stop();
	}, [spinAnim]);

	const spin = spinAnim.interpolate({
		inputRange: [0, 1],
		outputRange: ["0deg", "360deg"],
	});
	return (
		<View style={[styles.container, { backgroundColor: theme.bg }]}>
			{/* 상단: 내 식물 고르기 */}
			<Pressable
				style={[styles.selectBox, { borderColor: theme.border, backgroundColor: theme.card }]}
				onPress={() => setOpenDrop((v) => !v)}
			>
				<Text style={[styles.selectText, { color: theme.text }]}>
					{selected ? `${selected.name} (${selected.species})` : "내 식물 고르기"}
				</Text>
			</Pressable>

			{/* 드롭다운 (간단 구현) */}
			{openDrop && (
				<View style={[styles.dropdown, { borderColor: theme.border, backgroundColor: theme.card }]}>
					{myPlants.map((p) => (
						<Pressable key={p.id} style={styles.dropItem} onPress={() => handleSelect(p)}>
							<Text style={{ color: theme.text }}>{`${p.name} · ${p.species}`}</Text>
						</Pressable>
					))}
				</View>
			)}

			{/* 콘텐츠 박스 */}
			<View style={[styles.contentBox, { borderColor: theme.border, backgroundColor: theme.card }]}>
				{!selected && (
					<View style={styles.centerFill}>
						<Text style={{ color: theme.text }}>위에서 내 식물을 선택하세요</Text>
					</View>
				)}

				{selected && selected.species !== "몬스테라" && (
					<View style={[styles.centerFill, { borderColor: theme.border }]}>
						<Text style={[styles.msgText, { color: theme.text }]}>
							타임랩스의 조건이 모자랍니다{"\n"}하루하루 일기를 써봐요!
						</Text>
					</View>
				)}

				{selected && selected.species === "몬스테라" && generating && (
					<View style={styles.centerFill}>
						{/* timelapseDecoBox */}
						<View style={[styles.timelapseDecoBox, { borderColor: theme.border }]}>
							<Image
								source={timelapseDeco}
								style={styles.timelapseDeco}
								resizeMode="contain"
							/>
							<Animated.Image
								source={timelapseDecoCircles}
								style={[styles.timelapseDecoCircles, { transform: [{ rotate: spin }] }]}
								resizeMode="contain"
							/>
						</View>

						<Text style={[styles.loadingText, { color: theme.text }]}>타임랩스 생성중...</Text>
						<Text style={[styles.loadingSub, { color: theme.text }]}>생성된 타임랩스 보여주기</Text>
					</View>
				)}

				{selected && selected.species === "몬스테라" && showVideo && (
					<View style={styles.videoWrap}>
						<Video
							source={monsteraStable}
							style={StyleSheet.absoluteFillObject}
							resizeMode={ResizeMode.COVER}
							shouldPlay
							isLooping
							useNativeControls
						/>
					</View>
				)}
			</View>

			{/* 하단 버튼 바: 뒤로가기 / 타임 랩스 만들기 */}
			<View style={styles.bottomBar}>
				<Pressable
					onPress={() => router.replace("/(page)/diaryList")}
					style={({ pressed }) => [
						styles.backBtn,
						{ borderColor: theme.border, backgroundColor: theme.bg, opacity: pressed ? 0.85 : 1 },
					]}
					hitSlop={8}
				>
					<Text style={[styles.backText, { color: theme.text }]}>뒤로가기</Text>
				</Pressable>
			</View>
		</View>
	);
}

const styles = StyleSheet.create({
	container: { flex: 1, padding: 16 },
	selectBox: {
		borderWidth: 1,
		borderRadius: 10,
		paddingVertical: 14,
		paddingHorizontal: 12,
		marginBottom: 12,
	},
	selectText: { fontSize: 15, fontWeight: "600" },

	dropdown: {
		borderWidth: 1,
		borderRadius: 10,
		overflow: "hidden",
		marginBottom: 12,
	},
	dropItem: { paddingVertical: 12, paddingHorizontal: 12, borderBottomWidth: 1, borderBottomColor: "#00000010" },

	contentBox: {
		flex: 1,
		borderWidth: 1,
		borderRadius: 12,
		padding: 12,
	},
	centerFill: { flex: 1, alignItems: "center", justifyContent: "center" },

	msgText: { fontSize: 15, textAlign: "center", lineHeight: 22 },

	// timelapse 데코
	timelapseDecoBox: {
		width: 220,
		height: 200,
		borderWidth: 1,
		borderRadius: 12,
		alignItems: "center",
		justifyContent: "center",
		marginBottom: 14,
		overflow: "hidden",
	},
	timelapseDeco: { width: 200, height: 180, opacity: 0.9 },
	timelapseDecoCircles: { position: "absolute", right:47, top:8, width: 56, height: 56 },

	// 비디오
	videoWrap: { flex: 1, borderRadius: 10, overflow: "hidden" },
	video: { width: "100%", height: "100%" },

	loadingText: { fontSize: 16, fontWeight: "800", marginTop: 8 },
	loadingSub: { fontSize: 13, opacity: 0.8, marginTop: 6 },

	bottomBar: {
		flexDirection: "row",
	},
	backBtn: {
		flex: 1,
		borderWidth: 1,
		borderRadius: 12,
		alignItems: "center",
		justifyContent: "center",
		marginTop: 12,
		paddingVertical: 12,
	},
	primaryBtn: {
		flex: 1,
		borderWidth: 1,
		borderRadius: 14,
		alignItems: "center",
		justifyContent: "center",
		paddingVertical: 12,
	},
	backText: { fontSize: 15, fontWeight: "700" },
	fabText: { fontSize: 16, fontWeight: "800", textAlign: "center", lineHeight: 20 },
});
