import React, { useEffect, useMemo, useRef, useState } from "react";
import { View, Text, StyleSheet, Modal, Animated, Easing, useColorScheme } from "react-native";
import type { Router, Href } from "expo-router";
import Colors from "../../constants/Colors";

/* =========================
   Types (원본 시그니처 유지)
========================= */
export type LoadingJob = {
	task?: () => Promise<any>;
	to: Href;
	replace?: boolean;
	delay?: number;
	message?: string;
	timeoutMs?: number;
};

type RouterLike = Pick<Router, "push" | "replace" | "back">;

/* =========================
   Lightweight event bus
========================= */
type InternalState = {
	visible: boolean;
	message?: string;
	error?: string | null;
};

type Listener = (s: InternalState) => void;

const listeners = new Set<Listener>();
let _state: InternalState = { visible: false, message: undefined, error: null };

function emit(next: Partial<InternalState>) {
	_state = { ..._state, ...next };
	listeners.forEach(l => l(_state));
}

/* =========================
   Public APIs (원본 함수명/시그니처 유지)
========================= */
let _cancelled = false;

export function startLoading(
	router: RouterLike,
	job: LoadingJob
) {
	_cancelled = false;
	const { task, delay, to, replace, message, timeoutMs = 0 } = job;
	const wait = (ms: number) => new Promise(r => setTimeout(r, ms));

	// 딤 모달 즉시 표시
	emit({ visible: true, error: null, message });

	let done = false;
	let timeoutId: ReturnType<typeof setTimeout> | null = null;

	const run = async () => {
		try {
			if (timeoutMs > 0) {
				timeoutId = setTimeout(() => {
					if (done) return;
					done = true;

					if (_cancelled) {
						emit({ visible: false, message: undefined, error: null });
						return;
					}

					if (to) {
						if (replace && router.replace) router.replace(to);
						else router.push?.(to);   // ✅ 여기!
					}
				}, timeoutMs);
			}

			if (task) {
				await Promise.all([task(), wait(500)]);
			} else if (delay) {
				await wait(delay);
			}

			if (done) return;
			done = true;
			if (timeoutId) clearTimeout(timeoutId);
			if (_cancelled) {
				emit({ visible: false, message: undefined, error: null });
				return;
			}

			if (to) {
				if (replace && router.replace) router.replace(to);
				else router.push?.(to);
			}
		} catch (e: any) {
			if (timeoutId) clearTimeout(timeoutId);
			emit({ visible: true, error: e?.message || "알 수 없는 오류가 발생했어요." });
			setTimeout(() => emit({ visible: false, message: undefined, error: null }), 1200);
		} finally {
			setTimeout(() => emit({ visible: false, message: undefined, error: null }), 100);
		}
	};
	run();
}

export function stopLoading(
	router: RouterLike,
	opts?: { to?: Href; replace?: boolean }
) {
	_cancelled = true;
	emit({ visible: false, message: undefined, error: null });
	const to = opts?.to;
	if (to) {
		if (opts?.replace && router.replace) router.replace(to);
		else router.push?.(to);
	}
}

// common/loading.tsx 상단
const loadingMessages = [
	"로딩 중에도 식물은 자라요!",
	"식물은 밤에도 호흡을 해요.",
	"대부분의 뿌리는 산소도 함께 흡수해요.",
	"잎의 기공은 낮에 열리고 밤에 닫혀요.",
	"식물도 스트레스를 받으면 성장에 영향을 받아요.",
	"꽃은 번식을 위한 식물의 전략이에요.",
	"숲은 지구 산소의 약 28%를 공급해요.",
];

/* =========================
   Host Component (루트에 1회 마운트)
========================= */
export function GlobalLoadingHost() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const [state, setState] = useState<InternalState>(_state);

	const [randomMsg, setRandomMsg] = useState(loadingMessages[0]);

	useEffect(() => {
		const l: Listener = (s) => setState(s);
		listeners.add(l);
		return () => { listeners.delete(l); };
	}, []);

	// ✅ 주기적으로 랜덤 변경 (state.message가 없을 때만)
	useEffect(() => {
		if (!state.visible) return; // 모달이 보일 때만
		if (state.message) return;   // 고정 메시지 있으면 셔플 안 함
		const pick = () =>
			loadingMessages[Math.floor(Math.random() * loadingMessages.length)];
		setRandomMsg(pick());	   // 즉시 1회 시드
		const itv = setInterval(() => setRandomMsg(pick()), 3000);
		return () => clearInterval(itv);
	}, [state.visible, state.message]);


	const styles = useMemo(() => makeStyles(theme), [theme]);

	return (
		<Modal
			visible={state.visible}
			transparent
			animationType="fade"
			statusBarTranslucent
		>
			<View style={styles.overlay}>
				<View style={styles.box}>
					<CornersLoader size={100} color={theme.primary} />
					<Text style={styles.msg}>
						{state.error ? `⚠️ ${state.error}` : (state.message || randomMsg)}
					</Text>
				</View>
			</View>
		</Modal>
	);
}

/* =========================
   Styles
========================= */
const makeStyles = (theme: any) => StyleSheet.create({
	overlay: {
		flex: 1,
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
		color: theme.text,
		textAlign: "center",
	},
});

/* =========================
   Spinner
========================= */
function CornersLoader({ size = 100, color = "#6B74E6" }) {
	const t = useRef(new Animated.Value(0)).current;

	useEffect(() => {
		const loop = Animated.loop(
			Animated.timing(t, {
				toValue: 1,
				duration: 3000,
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

	const spin = t.interpolate({
		inputRange: [0, 1],
		outputRange: ["0deg", "360deg"],
	});

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
		left: 0,
		top: 0,
		right: 0,
		bottom: 0,
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