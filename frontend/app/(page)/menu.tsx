// app/(page)/menu.tsx
import React, { useMemo, useState, useCallback } from "react";
import {
	View,
	Text,
	StyleSheet,
	Pressable,
	useColorScheme,
} from "react-native";
import { useRouter } from "expo-router";
import Colors from "../../constants/Colors";
import * as FileSystem from "expo-file-system";
import AsyncStorage from "@react-native-async-storage/async-storage";
import Constants from "expo-constants";
import { showAlert, confirm } from "../../components/common/appAlert";

export default function MenuScreen() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const router = useRouter();

	const [busy, setBusy] = useState(false);

	// ─────────────────────────────────────────────────────────────────────────
	// Helpers
	// ─────────────────────────────────────────────────────────────────────────
	const appVersion = useMemo(() => {
		// expo build version 정보
		const v =
			(Constants.expoConfig as any)?.version ??
			(Constants as any)?.manifest2?.extra?.version ??
			"0.0.0";
		const nativeV = (Constants as any).nativeAppVersion ?? "";
		return nativeV && nativeV !== v ? `${v} (native ${nativeV})` : v;
	}, []);

	const clearAppCache = useCallback(async () => {
		try {
			setBusy(true);

			// 1) AsyncStorage 비우기 (토큰은 보존)
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

			showAlert({
				title: "완료",
				message: "앱 캐시를 삭제했어요.",
				buttons: [{ text: "확인" }],
			});
		} catch (e) {
			console.warn(e);
			showAlert({
				title: "오류",
				message: "캐시 삭제 중 문제가 발생했어요.",
				buttons: [{ text: "확인" }],
			});
		} finally {
			setBusy(false);
		}
	}, []);

	const doLogout = useCallback(async () => {
		try {
			setBusy(true);
			// 1) 토큰/세션 정보 제거
			await AsyncStorage.removeItem("authorization");
			await AsyncStorage.multiRemove(["user_profile", "user_prefs"]);
			// 2) 로그인 화면으로 교체 이동
			router.replace("/(auth)/login");
		} catch (e) {
			console.warn(e);
			showAlert({
				title: "오류",
				message: "로그아웃 중 문제가 발생했어요.",
				buttons: [{ text: "확인" }],
			});
		} finally {
			setBusy(false);
		}
	}, [router]);

	// 핸들러들 (모달 제거 → 공통 알럿/컨펌 사용)
	const handleShowVersion = () =>
		showAlert({
			title: "앱 버전",
			message: `현재 설치된 버전입니다.\n${appVersion}`,
			buttons: [{ text: "닫기" }],
		});

	const handleAskClearCache = async () => {
		if (busy) return;
		const ok = await confirm({
			title: "캐시 삭제",
			message: "임시파일 및 캐시를 정리합니다. 로그인 정보는 유지돼요.",
			okText: "캐시 삭제",
			cancelText: "취소",
		});
		if (ok) await clearAppCache();
	};

	const handleAskLogout = async () => {
		if (busy) return;
		const ok = await confirm({
			title: "로그아웃",
			message: "정말 로그아웃 하시겠습니까?",
			okText: "확인",
			cancelText: "취소",
		});
		if (ok) await doLogout();
	};

	const handleShowPeople = () =>
		showAlert({
			title: "만든 사람들",
			message: ["김신명 – DB", "김우주 – AI", "오지환 – UI", "이광주 – Product", "정은혜 – Dev"].join("\n"),
			buttons: [{ text: "닫기" }],
		});

	// ─────────────────────────────────────────────────────────────────────────
	// UI
	// ─────────────────────────────────────────────────────────────────────────
	return (
		<View style={[styles.container, { backgroundColor: theme.bg }]}>
			{/* 풀폭 리스트 (양옆 여백 0) */}
			<ListItem
				label="앱 버전"
				desc={appVersion}
				onPress={handleShowVersion}
				borderColor={theme.border}
				textColor={theme.text}
				bg={theme.bg}
			/>
			<ListItem
				label="앱 캐시 삭제"
				onPress={handleAskClearCache}
				borderColor={theme.border}
				textColor={theme.text}
				bg={theme.bg}
			/>
			<ListItem
				label="로그아웃"
				onPress={handleAskLogout}
				borderColor={theme.border}
				textColor={theme.text}
				bg={theme.bg}
				destructive
			/>
			<ListItem
				label="만든 사람들"
				onPress={handleShowPeople}
				borderColor={theme.border}
				textColor={theme.text}
				bg={theme.bg}
			/>
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
		<Pressable
			onPress={onPress}
			style={({ pressed }) => [
				styles.row,
				{
					borderBottomColor: borderColor,
					backgroundColor: bg,
					opacity: pressed ? 0.8 : 1,
				},
			]}
		>
			<Text
				style={[
					styles.rowLabel,
					{ color: destructive ? "#e65b5b" : textColor },
				]}
			>
				{label}
			</Text>
			{desc ? (
				<Text style={[styles.rowDesc, { color: textColor }]}>{desc}</Text>
			) : null}
		</Pressable>
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
		alignItems: "center",
		borderBottomWidth: StyleSheet.hairlineWidth,
		flexDirection: "row",
		justifyContent: "space-between",
		minHeight: 56,
		paddingHorizontal: 16,
	},
	rowLabel: {
		fontSize: 16,
	},
	rowDesc: {
		fontSize: 14,
		marginLeft: 12,
		opacity: 0.7,
	},
});
