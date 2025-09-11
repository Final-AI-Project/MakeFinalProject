// app/(auth)/login.tsx
import React, { useMemo, useState } from "react";
import {
	View,
	Text,
	TextInput,
	TouchableOpacity,
	Alert,
	KeyboardAvoidingView,
	Platform,
	ScrollView,
	ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { useRouter, useLocalSearchParams } from "expo-router";
import { setToken } from "../../lib/auth";
import { useColorScheme } from "react-native";

// 서버 주소를 환경에 맞게 바꿔주세요. (Expo 클라이언트에서 접근하려면 EXPO_PUBLIC_* prefix 필수)
const API_BASE_URL =
	process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8080";

type LoginForm = {
	user_id: string;
	user_pw: string;
};

export default function LoginScreen() {
	const router = useRouter();
	const params = useLocalSearchParams<{ redirect?: string }>();
	const [form, setForm] = useState<LoginForm>({ user_id: "", user_pw: "" });
	const [loading, setLoading] = useState(false);
	const scheme = useColorScheme();
	const dark = scheme === "dark";

	const disabled = useMemo(
		() => !form.user_id || !form.user_pw || loading,
		[form, loading]
	);

	const onChange = (key: keyof LoginForm, val: string) => {
		setForm((prev) => ({ ...prev, [key]: val }));
	};

	const handleLogin = async () => {
		try {
			setLoading(true);
			const res = await fetch(`${API_BASE_URL}/auth/login`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(form),
			});

			if (!res.ok) {
				const text = await res.text().catch(() => "");
				throw new Error(text || `Login failed (${res.status})`);
			}

			// 토큰/세션 처리 예시 (백엔드 응답 구조에 맞게 수정)
			const data = await res.json();
			await setToken(data.token);

			const next =
				typeof params.redirect === "string" ? params.redirect : "/(tab)/index";
			Alert.alert("로그인", "로그인 성공했습니다!", [
				{ text: "확인", onPress: () => router.replace(next) },
			]);
		} catch (err: any) {
			Alert.alert(
				"로그인 실패",
				err?.message ?? "아이디/비밀번호를 확인해주세요."
			);
		} finally {
			setLoading(false);
		}
	};

	return (
		<SafeAreaView
			edges={["top", "bottom"]}
			style={{ flex: 1, backgroundColor: dark ? "#0a1b26" : "#fafafa" }}
		>
			{/* Edge-to-Edge에서는 StatusBar 배경색이 무시되므로, SafeAreaView 배경으로 처리 */}
			<StatusBar style={dark ? "light" : "dark"} />

			<KeyboardAvoidingView
				behavior={Platform.select({ ios: "padding", android: undefined })}
				style={{ flex: 1 }} // 전체 채움 (필수)
			>
				<ScrollView
					contentContainerStyle={{ padding: 20 }}
					keyboardShouldPersistTaps="handled"
				>
					<Text
						style={{
							fontSize: 28,
							fontWeight: "700",
							color: dark ? "#E5ECFF" : "#0B1020",
							marginBottom: 16,
						}}
					>
						로그인
					</Text>

					{/* ERD 매핑: user_id */}
					<View style={{ marginBottom: 12 }}>
						<Text
							style={{
								color: dark ? "#9FB0FF" : "#3B4B8E",
								marginBottom: 6,
							}}
						>
							아이디 (user_id)
						</Text>
						<TextInput
							placeholder="아이디"
							placeholderTextColor={dark ? "#8A8FA3" : "#9AA0B4"}
							value={form.user_id}
							onChangeText={(v) => onChange("user_id", v)}
							autoCapitalize="none"
							returnKeyType="next"
							style={[
								styles.input,
								dark ? styles.inputDark : styles.inputLight,
							]}
						/>
					</View>

					{/* ERD 매핑: user_pw */}
					<View style={{ marginBottom: 20 }}>
						<Text
							style={{
								color: dark ? "#9FB0FF" : "#3B4B8E",
								marginBottom: 6,
							}}
						>
							비밀번호 (user_pw)
						</Text>
						<TextInput
							placeholder="비밀번호"
							placeholderTextColor={dark ? "#8A8FA3" : "#9AA0B4"}
							value={form.user_pw}
							onChangeText={(v) => onChange("user_pw", v)}
							autoCapitalize="none"
							secureTextEntry
							returnKeyType="done"
							style={[
								styles.input,
								dark ? styles.inputDark : styles.inputLight,
							]}
						/>
					</View>

					<TouchableOpacity
						onPress={handleLogin}
						disabled={disabled}
						style={[
							styles.btn,
							disabled && { opacity: 0.6 },
							{ backgroundColor: dark ? "#4C6FFF" : "#3B63FF" },
						]}
					>
						{loading ? (
							<ActivityIndicator color="#FFFFFF" />
						) : (
							<Text style={styles.btnText}>로그인</Text>
						)}
					</TouchableOpacity>

					<TouchableOpacity
						style={{ marginTop: 16, alignSelf: "center" }}
						onPress={() => router.push("/(auth)/signup")}
					>
						<Text style={{ color: dark ? "#B7C4FF" : "#425BD9" }}>
							아직 계정이 없으신가요? 회원가입
						</Text>
					</TouchableOpacity>
				</ScrollView>
			</KeyboardAvoidingView>
		</SafeAreaView>
	);
}

const styles = {
	input: {
		borderWidth: 1,
		borderRadius: 12,
		paddingHorizontal: 14,
		paddingVertical: 12,
		fontSize: 16,
	},
	inputDark: {
		borderColor: "#2A3352",
		backgroundColor: "#141A2B",
		color: "#E5ECFF",
	},
	inputLight: {
		borderColor: "#D7DAE3",
		backgroundColor: "#FFFFFF",
		color: "#0B1020",
	},
	btn: {
		paddingVertical: 14,
		borderRadius: 14,
		alignItems: "center",
	},
	btnText: {
		color: "#FFFFFF",
		fontSize: 18,
		fontWeight: "700",
	},
} as const;
