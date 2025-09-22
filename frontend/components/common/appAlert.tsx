// components/common/appAlert.tsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
	Modal,
	View,
	Text,
	Pressable,
	StyleSheet,
	Animated,
	Easing,
	useColorScheme,
} from "react-native";
import Colors from "../../constants/Colors";

/* ========= Types ========= */
export type AlertButton = {
	text: string;
	onPress?: () => void | Promise<void>;
	style?: "default" | "cancel" | "destructive";
};
export type AlertOptions = {
	title?: string;
	message: string;
	buttons?: AlertButton[];
	dismissible?: boolean; // 딤 클릭으로 닫기 허용
};

/* ========= Lightweight event bus ========= */
type InternalState = {
	visible: boolean;
	title?: string;
	message?: string;
	buttons: AlertButton[];
	dismissible: boolean;
};
const listeners = new Set<(s: InternalState) => void>();
let _state: InternalState = {
	visible: false,
	title: undefined,
	message: undefined,
	buttons: [],
	dismissible: false,
};
function emit(next: Partial<InternalState>) {
	_state = { ..._state, ...next };
	listeners.forEach((l) => l(_state));
}

/* ========= Public APIs ========= */
// 간단 호출: showAlert({ title, message, buttons })
export function showAlert(opts: AlertOptions) {
	const buttons = opts.buttons?.length ? opts.buttons : [{ text: "확인" }];
	emit({
		visible: true,
		title: opts.title,
		message: opts.message,
		buttons,
		dismissible: !!opts.dismissible,
	});
}

// confirm: Promise<boolean> 반환 (확인 true / 취소 false)
export function confirm(opts: { title?: string; message: string; okText?: string; cancelText?: string; dismissible?: boolean; }) {
	return new Promise<boolean>((resolve) => {
		const ok: AlertButton = {
			text: opts.okText ?? "확인",
			style: "default",
			onPress: () => resolve(true),
		};
		const cancel: AlertButton = {
			text: opts.cancelText ?? "취소",
			style: "cancel",
			onPress: () => resolve(false),
		};
		showAlert({
			title: opts.title,
			message: opts.message,
			buttons: [cancel, ok],
			dismissible: !!opts.dismissible,
		});
	});
}

/* ========= Host ========= */
export function GlobalAlertHost() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const [state, setState] = useState<InternalState>(_state);

	useEffect(() => {
		const l = (s: InternalState) => setState(s);
		listeners.add(l);
		return () => { listeners.delete(l); };
	}, []);

	const scale = useRef(new Animated.Value(0.9)).current;
	const opacity = useRef(new Animated.Value(0)).current;

	useEffect(() => {
		if (state.visible) {
			Animated.parallel([
				Animated.timing(opacity, { toValue: 1, duration: 160, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
				Animated.spring(scale, { toValue: 1, useNativeDriver: true, bounciness: 4 }),
			]).start();
		} else {
			opacity.setValue(0);
			scale.setValue(0.9);
		}
	}, [state.visible, opacity, scale]);

	const styles = useMemo(() => makeStyles(theme), [theme]);

	const handleClose = () => emit({ visible: false, title: undefined, message: undefined, buttons: [], dismissible: false });

	return (
		<Modal visible={state.visible} transparent animationType="fade" statusBarTranslucent>
			<View style={styles.overlay}>
				{/* 딤 클릭으로 닫기 */}
				<Pressable style={StyleSheet.absoluteFill} onPress={() => state.dismissible && handleClose()} />
				<Animated.View style={[styles.box, { transform: [{ scale }], opacity }]}>
					{state.title ? <Text style={styles.title}>{state.title}</Text> : null}
					{state.message ? <Text style={styles.message}>{state.message}</Text> : null}
					<View style={styles.actions}>
						{(state.buttons || []).map((b, idx) => (
							<Pressable
								key={`${b.text}-${idx}`}
								onPress={async () => { handleClose(); try { await b.onPress?.(); } catch {} }}
								style={[
									styles.btn,
									b.style === "cancel" && styles.btnGhost,
									b.style === "destructive" && styles.btnDanger,
								]}
							>
								<Text style={[
									styles.btnText,
									b.style === "cancel" && styles.btnTextGhost,
								]}>
									{b.text}
								</Text>
							</Pressable>
						))}
					</View>
				</Animated.View>
			</View>
		</Modal>
	);
}

/* ========= Styles ========= */
const makeStyles = (theme: any) => StyleSheet.create({
	overlay: {
		flex: 1,
		backgroundColor: "rgba(0,0,0,0.5)",
		alignItems: "center",
		justifyContent: "center",
		padding: 24,
	},
	box: {
		width: "100%",
		maxWidth: 420,
		borderRadius: 20,
		paddingHorizontal: 20,
		paddingVertical: 18,
		backgroundColor: theme.bg,
	},
	title: {
		fontSize: 16,
		fontWeight: "800",
		color: theme.text,
		marginBottom: 8,
	},
	message: {
		fontSize: 14,
		color: theme.text,
		opacity: 0.9,
	},
	actions: {
		flexDirection: "row",
		justifyContent: "flex-end",
		gap: 8,
		marginTop: 18,
	},
	btn: {
		minWidth: 76,
		paddingHorizontal: 14,
		paddingVertical: 10,
		borderRadius: 12,
		backgroundColor: theme.primary,
		alignItems: "center",
		justifyContent: "center",
	},
	btnText: { color: "#fff", fontWeight: "700" },
	btnGhost: {
		backgroundColor: "transparent",
		borderWidth: 1,
		borderColor: theme.border,
	},
	btnTextGhost: { color: theme.text },
	btnDanger: {
		backgroundColor: "#ef4444",
	},
});