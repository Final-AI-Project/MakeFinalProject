// app/(page)/menu.tsx
import React, { useMemo, useState, useCallback } from "react";
import {
	View,
	Text,
	StyleSheet,
	Pressable,
	Modal,
	Alert,
	useColorScheme,
	ActivityIndicator,
} from "react-native";
import { useRouter } from "expo-router";
import Colors from "../../constants/Colors";
import * as FileSystem from "expo-file-system";
import AsyncStorage from "@react-native-async-storage/async-storage";
import Constants from "expo-constants";

type ModalType = "version" | "cache" | "people" | "logout" | null;

export default function MenuScreen() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const router = useRouter();

	const [visible, setVisible] = useState<ModalType>(null);
	const [busy, setBusy] = useState(false);

	// ─────────────────────────────────────────────────────────────────────────
	// Helpers
	// ─────────────────────────────────────────────────────────────────────────
	const appVersion = useMemo(() => {
		// expo build version 정보
		const v =
			(Constants.expoConfig as any)?.version ??
			(Constants.manifest2 as any)?.extra?.version ??
			"0.0.0";
		const nativeV = (Constants as any).nativeAppVersion ?? "";
		return nativeV && nativeV !== v ? `${v} (native ${nativeV})` : v;
	}, []);

	const open = (t: ModalType) => setVisible(t);
	const close = () => setVisible(null);

	const clearAppCache = useCallback(async () => {
		try {
			setBusy(true);
			// 1) AsyncStorage 비우기 (토큰 제외하고 캐시만 비우고 싶다면 key 선별)
			//	여기서는 "캐시 삭제"는 전역 캐시 성격으로, 토큰은 유지.
			//	필요 시 화이트리스트 방식으로 보관할 키 추가하세요.
			const allKeys = await AsyncStorage.getAllKeys();
			const keepKeys = ["authorization"]; // 🔧 토큰 키 유지
			const removeKeys = allKeys.filter((k) => !keepKeys.includes(k));
			if (removeKeys.length) {
				await AsyncStorage.multiRemove(removeKeys);
			}

			// 2) FileSystem 캐시 삭제
			if (FileSystem.cacheDirectory) {
				await FileSystem.deleteAsync(FileSystem.cacheDirectory, {
					idempotent: true,
				});
			}
			// 3) 필요하면 앱 내부 임시폴더 등 추가 정리 로직 삽입

			close();
			Alert.alert("완료", "앱 캐시를 삭제했어요.");
		} catch (e) {
			console.warn(e);
			Alert.alert("오류", "캐시 삭제 중 문제가 발생했어요.");
		} finally {
			setBusy(false);
		}
	}, []);

	const doLogout = useCallback(async () => {
		try {
			setBusy(true);
			// 서버 세션이 있다면 API 호출 추가 가능
			// 1) 토큰/세션 정보 제거
			await AsyncStorage.removeItem("authorization");
			// 필요 시 사용자 정보 관련 키도 제거
			await AsyncStorage.multiRemove([
				"user_profile",
				"user_prefs",
			]);

			// 2) 라우팅: 로그인 화면으로 교체 이동
			router.replace("/(auth)/login");
		} catch (e) {
			console.warn(e);
			Alert.alert("오류", "로그아웃 중 문제가 발생했어요.");
		} finally {
			setBusy(false);
		}
	}, [router]);

	// ─────────────────────────────────────────────────────────────────────────
	// UI
	// ─────────────────────────────────────────────────────────────────────────
	return (
		<View style={[styles.container, { backgroundColor: theme.bg }]}>
			{/* 풀폭 리스트 (양옆 여백 0) */}
			<ListItem
				label="앱 버전"
				desc={appVersion}
				onPress={() => open("version")}
				borderColor={theme.border}
				textColor={theme.text}
				bg={theme.bg}
			/>
			<ListItem
				label="앱 캐시 삭제"
				onPress={() => open("cache")}
				borderColor={theme.border}
				textColor={theme.text}
				bg={theme.bg}
			/>
			<ListItem
				label="로그아웃"
				onPress={() => open("logout")}
				borderColor={theme.border}
				textColor={theme.text}
				bg={theme.bg}
				destructive
			/>
			<ListItem
				label="만든 사람들"
				onPress={() => open("people")}
				borderColor={theme.border}
				textColor={theme.text}
				bg={theme.bg}
			/>

			{/* 공용 모달: 가운데 카드 */}
			<CenterModal visible={!!visible} onRequestClose={close} themeBg={theme.bg}>
				{busy ? (
					<View style={styles.centerBox}>
						<ActivityIndicator />
						<Text style={[styles.modalTitle, { color: theme.text, marginTop: 12 }]}>
							처리 중…
						</Text>
					</View>
				) : visible === "version" ? (
					<View style={styles.centerBox}>
						<Text style={[styles.modalTitle, { color: theme.text }]}>앱 버전</Text>
						<Text style={[styles.modalBody, { color: theme.text }]}>
							현재 설치된 버전입니다.
						</Text>
						<Text style={[styles.versionText, { color: theme.text }]}>{appVersion}</Text>
						<ModalButtons
							onCancel={close}
							theme={theme}
							primaryLabel="닫기"
							primaryOnly
						/>
					</View>
				) : visible === "cache" ? (
					<View style={styles.centerBox}>
						<Text style={[styles.modalTitle, { color: theme.text }]}>캐시 삭제</Text>
						<Text style={[styles.modalBody, { color: theme.text }]}>
							임시파일 및 캐시를 정리합니다. 로그인 정보는 유지돼요.
						</Text>
						<ModalButtons
							onCancel={close}
							onConfirm={clearAppCache}
							theme={theme}
							confirmLabel="캐시 삭제"
						/>
					</View>
				) : visible === "logout" ? (
					<View style={styles.centerBox}>
						<Text style={[styles.modalTitle, { color: theme.text }]}>로그아웃</Text>
						<Text style={[styles.modalBody, { color: theme.text }]}>
							정말 로그아웃 하시겠습니까?
						</Text>
						<ModalButtons
							onCancel={close}
							onConfirm={doLogout}
							theme={theme}
							confirmLabel="확인"
							destructive
						/>
					</View>
				) : visible === "people" ? (
					<View style={styles.centerBox}>
						<Text style={[styles.modalTitle, { color: theme.text }]}>만든 사람들</Text>
						{/* 🔧 이 영역을 프로젝트 팀원 정보로 자유롭게 수정 */}
						<Text style={[styles.modalBody, { color: theme.text }]}>김신명 – DB</Text>
						<Text style={[styles.modalBody, { color: theme.text }]}>김우주 – AI</Text>
						<Text style={[styles.modalBody, { color: theme.text }]}>오지환 – UI</Text>
						<Text style={[styles.modalBody, { color: theme.text }]}>이광주 – Product</Text>
						<Text style={[styles.modalBody, { color: theme.text }]}>정은혜 – Dev</Text>
						<ModalButtons onCancel={close} theme={theme} primaryLabel="닫기" primaryOnly />
					</View>
				) : null}
			</CenterModal>
		</View>
	);
}

// ─────────────────────────────────────────────────────────────────────────────
// Sub Components
// ─────────────────────────────────────────────────────────────────────────────
function ListItem({
	label,
	desc,
	onPress,
	borderColor,
	textColor,
	bg,
	destructive,
}: {
	label: string;
	desc?: string;
	onPress?: () => void;
	borderColor: string;
	textColor: string;
	bg: string;
	destructive?: boolean;
}) {
	return (
		<Pressable onPress={onPress} style={({ pressed }) => [
			styles.row,
			{ borderBottomColor: borderColor, backgroundColor: bg, opacity: pressed ? 0.8 : 1 },
		]}>
			<Text style={[styles.rowLabel, { color: destructive ? "#e65b5b" : textColor }]}>
				{label}
			</Text>
			{desc ? <Text style={[styles.rowDesc, { color: textColor }]}>{desc}</Text> : null}
		</Pressable>
	);
}

function CenterModal({
	visible,
	onRequestClose,
	children,
	themeBg,
}: {
	visible: boolean;
	onRequestClose: () => void;
	children: React.ReactNode;
	themeBg: string;
}) {
	return (
		<Modal
			visible={visible}
			transparent
			animationType="fade"
			onRequestClose={onRequestClose}
		>
			<View style={styles.backdrop} />
			<View style={styles.centerWrap}>
				<View style={[styles.card, { backgroundColor: themeBg }]}>
					{children}
				</View>
			</View>
		</Modal>
	);
}

function ModalButtons({
	onCancel,
	onConfirm,
	theme,
	confirmLabel = "확인",
	primaryLabel = "확인",
	primaryOnly = false,
	destructive = false,
}: {
	onCancel?: () => void;
	onConfirm?: () => void;
	theme: any;
	confirmLabel?: string;
	primaryLabel?: string;
	primaryOnly?: boolean;
	destructive?: boolean;
}) {
	if (primaryOnly) {
		return (
			<View style={styles.btnRow}>
				<Pressable onPress={onCancel} style={[styles.btn, { borderColor: theme.border }]}>
					<Text style={[styles.btnText, { color: theme.text }]}>{primaryLabel}</Text>
				</Pressable>
			</View>
		);
	}
	return (
		<View style={styles.btnRow}>
			<Pressable onPress={onCancel} style={[styles.btn, { borderColor: theme.border }]}>
				<Text style={[styles.btnText, { color: theme.text }]}>취소</Text>
			</Pressable>
			<Pressable
				onPress={onConfirm}
				style={[styles.btn, { borderColor: destructive ? "#e65b5b" : theme.border }]}
			>
				<Text
					style={[
						styles.btnText,
						{ color: destructive ? "#e65b5b" : theme.text, fontWeight: "700" },
					]}
				>
					{confirmLabel}
				</Text>
			</Pressable>
		</View>
	);
}

// ─────────────────────────────────────────────────────────────────────────────
// Styles (Tab size 4, 풀폭 목록)
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
	container: {
		flex: 1,
	},
	row: {
		minHeight: 56,
		paddingHorizontal: 16, // 글자는 여백 있어도, 행 자체는 풀폭 (컨테이너 패딩 없음)
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "space-between",
		borderBottomWidth: StyleSheet.hairlineWidth,
	},
	rowLabel: {
		fontSize: 16,
	},
	rowDesc: {
		fontSize: 14,
		opacity: 0.7,
		marginLeft: 12,
	},
	backdrop: {
		...StyleSheet.absoluteFillObject,
		backgroundColor: "rgba(0,0,0,0.45)",
	},
	centerWrap: {
		flex: 1,
		alignItems: "center",
		justifyContent: "center",
		padding: 24,
	},
	card: {
		width: "100%",
		maxWidth: 420,
		borderRadius: 16,
		padding: 20,
		elevation: 3,
	},
	centerBox: {
		alignItems: "center",
	},
	versionText: {
		fontSize: 18,
		marginTop: 6,
	},
	modalTitle: {
		fontSize: 18,
		marginBottom: 12,
		fontWeight: "700",
		textAlign: "center",
	},
	modalBody: {
		fontSize: 14,
		opacity: 0.8,
		marginBottom: 16,
		textAlign: "center",
	},
	btnRow: {
		width: "100%",
		marginTop: 8,
		flexDirection: "row",
		justifyContent: "space-between",
		gap: 10,
	},
	btnRowSingle: {
		width: "100%",
		marginTop: 8,
	},
	btn: {
		flex: 1,
		borderWidth: StyleSheet.hairlineWidth,
		borderRadius: 12,
		paddingVertical: 12,
		alignItems: "center",
	},
	btnText: {
		fontSize: 15,
	},
});
