import React, { useEffect, useMemo, useRef, useState } from "react";
import { View, Text, StyleSheet, Modal, Animated, Easing, useColorScheme } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import Colors from "../../constants/Colors";

type LoadingJob = {
	task?: () => Promise<any>;
	to: string;
	replace?: boolean;
	delay?: number;
	message?: string;
};

let _job: LoadingJob | null = null;

export function startLoading(
	router: ReturnType<typeof useRouter> | { push: (p: string) => void },
	job: LoadingJob
) {
	_job = job;
	router.push("/common/loading");
}

// 준비된 워딩 리스트
const loadingMessages = [
	"로딩 중에도 식물은 자라요!",
	"식물은 밤에도 호흡을 해요.",
	"대부분의 뿌리는 산소도 함께 흡수해요.",
	"잎의 기공은 낮에 열리고 밤에 닫혀요.",
	"식물도 스트레스를 받으면 성장에 영향을 받아요.",
	"꽃은 번식을 위한 식물의 전략이에요.",
	"숲은 지구 산소의 약 28%를 공급해요.",
];
// ...

export default function Loading() {
	const router = useRouter();
	const params = useLocalSearchParams<{ message?: string }>();
	const [error, setError] = useState<string | null>(null);
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	
	const styles = React.useMemo(() => makeStyles(theme), [theme]);

	const [randomMsg, setRandomMsg] = useState(loadingMessages[0]);
	useEffect(() => {
		if (params.message) return; // 백엔드 메시지가 있으면 랜덤 변경 안 함
		const interval = setInterval(() => {
		const idx = Math.floor(Math.random() * loadingMessages.length);
		setRandomMsg(loadingMessages[idx]);
		}, 3000);
		return () => clearInterval(interval);
	}, [params.message]);
	const fallbackMessage = params.message || randomMsg;

	useEffect(() => {
		let mounted = true;
		(async () => {
			const job = _job;
			_job = null;

			try {
				const wait = (ms:number)=>new Promise(r=>setTimeout(r,ms));

				if (job?.task) {
					await Promise.all([job.task(), wait(500)]);
				} else if (job?.delay) {
					await new Promise((r) => setTimeout(r, job.delay));
				}
				if (!mounted || !job?.to) return;

				if (job.replace) router.replace(job.to);
				else router.push(job.to);
			} catch (e: any) {
				console.error(e);
				setError(e?.message || "알 수 없는 오류가 발생했어요.");
				setTimeout(() => {
					if (!mounted) return;
					router.back();
				}, 1200);
			}
		})();
		return () => {
			mounted = false;
		};
	}, [router]);

	return (
		<Modal visible transparent statusBarTranslucent>
			<View style={styles.overlay}>
				<View style={styles.box}>
					<CornersLoader size={100} color="#6B74E6" />
					<Text style={styles.msg}>
						{error ? `⚠️ ${error}` : fallbackMessage}
					</Text>
				</View>
			</View>
		</Modal>
	);
}

const makeStyles = (theme: any) => StyleSheet.create({
	overlay: {
		...StyleSheet.absoluteFillObject,
		backgroundColor: "rgba(0,0,0,0.5)",
		justifyContent: "center",
		alignItems: "center",
	},
	box: {
		width: 240,
		minHeight: 240,
		padding: 32,
		borderRadius: 24,
		backgroundColor: theme.bg,
		alignItems: "center",
	},
	msg: {
		marginTop: 40,
		fontSize: 14,
		color: theme.text, // ← 텍스트 컬러도 테마 적용
		textAlign: "center",
	},
});

/* ─────────────────────────────
	4개의 코너가 무한 회전하는 로더
────────────────────────────── */
function CornersLoader({ size = 100, color = "#6B74E6" }) {
	const t = useRef(new Animated.Value(0)).current;

	useEffect(() => {
		const loop = Animated.loop(
			Animated.timing(t, {
				toValue: 1,
				duration: 3000, // 3s
				easing: Easing.linear,
				useNativeDriver: true,
			})
		);
		loop.start();
		return () => {
			loop.stop();
			t.setValue(0);
		};
	}, [t]);

	// 공통 회전 (부모 .corners spin)
	const spin = t.interpolate({
		inputRange: [0, 1],
		outputRange: ["0deg", "360deg"],
	});

	// 각 corner별 타이밍 (spin1~4 근사)
	const spin1 = t.interpolate({
		inputRange: [0, 0.3, 0.7, 1],
		outputRange: ["0deg", "0deg", "0deg", "360deg"],
	});
	const spin2 = t.interpolate({
		inputRange: [0, 0.3, 0.7, 1],
		outputRange: ["0deg", "270deg", "270deg", "360deg"],
	});
	const spin3 = t.interpolate({
		inputRange: [0, 0.3, 0.7, 1],
		outputRange: ["0deg", "180deg", "180deg", "360deg"],
	});
	const spin4 = t.interpolate({
		inputRange: [0, 0.3, 0.7, 1],
		outputRange: ["0deg", "90deg", "90deg", "360deg"],
	});

	return (
		<Animated.View style={{ width: size, height: size, transform: [{ rotate: spin }] }}>
			<Animated.View style={[loaderStyles.cornerWrap, { transform: [{ rotate: spin1 }] }]}>
				<View style={[loaderStyles.cornerBlock, { backgroundColor: color }]} />
			</Animated.View>
			<Animated.View style={[loaderStyles.cornerWrap, { transform: [{ rotate: spin2 }] }]}>
				<View style={[loaderStyles.cornerBlock, { backgroundColor: color }]} />
			</Animated.View>
			<Animated.View style={[loaderStyles.cornerWrap, { transform: [{ rotate: spin3 }] }]}>
				<View style={[loaderStyles.cornerBlock, { backgroundColor: color }]} />
			</Animated.View>
			<Animated.View style={[loaderStyles.cornerWrap, { transform: [{ rotate: spin4 }] }]}>
				<View style={[loaderStyles.cornerBlock, { backgroundColor: color }]} />
			</Animated.View>
		</Animated.View>
	);
}

const loaderStyles = StyleSheet.create({
	cornerWrap: {
		position: "absolute",
		left: 0, top: 0, right: 0, bottom: 0,
		alignItems: "flex-start",
		justifyContent: "flex-start",
	},
	cornerBlock: {
		width: "48%",
		height: "48%",
		borderTopRightRadius: 30,
		borderBottomLeftRadius: 30,
	},
});

/*	
StyleSheet.create 랑 return 이 분리 되어 있는데 합치지 않은 이유는?

1. 퍼포먼스
StyleSheet.create는 호출될 때 JS 객체를 만들고, 네이티브로 넘겨주는 비용이 있어요.
만약 return 안쪽에서 매번 StyleSheet.create를 호출하면, 렌더링 때마다 스타일 객체가 새로 생성돼요.
→ 불필요한 리렌더 / 성능 저하 가능성.

2. 가독성 / 재사용
스타일은 한 번 정의하고 여러 컴포넌트에서 재사용하는 경우도 있어서, 보통 함수 바깥에 둡니다.
*/