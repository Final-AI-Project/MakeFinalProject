// app/(auth)/login.tsx
import React, { useMemo, useState, useRef, useEffect } from "react";
import {
	View,
	Text,
	TextInput,
	TouchableOpacity,
	Alert,
	Keyboard,
	KeyboardAvoidingView,
	Platform,
	ScrollView,
	ActivityIndicator,
	Animated,
	StyleSheet,
	Easing
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter, useLocalSearchParams } from "expo-router";
import { setToken } from "../../libs/auth";
import { useColorScheme, Image } from "react-native";
import Colors from "../../constants/Colors";
import loginEffDef from "../../assets/images/login_eff_def.png";
import normalface from "../../assets/images/login_eff_normalface.png";
import inputface from "../../assets/images/login_eff_inputface.png";
import pwface from "../../assets/images/login_eff_pwface.png";
import { startLoading } from "../common/loading";

// 🔧 환경별 안전한 API_BASE_URL (실기기는 EXPO_PUBLIC_API_BASE_URL 사용 권장)
const FALLBACK_PORT = 8080;
const ENV_BASE =
	typeof process.env.EXPO_PUBLIC_API_BASE_URL === "string" &&
	process.env.EXPO_PUBLIC_API_BASE_URL.trim().length > 0
		? process.env.EXPO_PUBLIC_API_BASE_URL.trim()
		: "";

const DEFAULT_BASE =
	Platform.OS === "android"
		? `http://10.0.2.2:${FALLBACK_PORT}` // Android 에뮬레이터
		: `http://localhost:${FALLBACK_PORT}`; // iOS 시뮬레이터/웹

export const API_BASE_URL = ENV_BASE || DEFAULT_BASE;

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
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const [boxWidth, setBoxWidth] = useState(0);

	const disabled = useMemo(
		() => !form.user_id || !form.user_pw || loading,
		[form, loading]
	);

	// 로그인 포커스 이펙트
	const [showInputFace, setShowInputFace] = useState(false);
	const [showPwFace, setShowPwFace] = useState(false);
	const inputFaceX = useRef(new Animated.Value(0)).current;
	const pwFaceY = useRef(new Animated.Value(180)).current;

	// 아이디 포커스
	const onIdFocus = () => {
		setShowPwFace(false);
		setShowInputFace(true);
	};
	const onIdBlur = () => {
		setShowInputFace(false);
	};

	// 비밀번호 포커스
	const onPwFocus = () => {
		setShowInputFace(false);
		setShowPwFace(true);
		pwFaceY.setValue(180);
		Animated.timing(pwFaceY, {
			toValue: 0,
			duration: 220,
			easing: Easing.out(Easing.quad),
			useNativeDriver: true,
		}).start();
	};
	const onPwBlur = () => {
		setShowPwFace(false);
	};

	useEffect(() => {
		const length = form.user_id.length;
		const maxChars = 50;

		let targetX;

		if (length === 0) {
			targetX = (boxWidth / 2 - 30) - 95;
		} else {
			const percent = Math.min(length / maxChars, 1);
			targetX = percent * boxWidth * 0.175;
		}

		Animated.timing(inputFaceX, {
			toValue: targetX,
			duration: 100,
			easing: Easing.out(Easing.quad),
			useNativeDriver: true,
		}).start();
	}, [form.user_id, boxWidth, inputFaceX]);

	const onChange = (key: keyof LoginForm, val: string) => {
		setForm((prev) => ({ ...prev, [key]: val }));
	};

	// ✅ 파일 내 로컬 runWithLoading (새 파일 만들지 않음)
	const runWithLoading = (
		router: ReturnType<typeof useRouter>,
		task: () => Promise<any>,
		to: string,
		message?: string
	) => {
		startLoading(router, { task, to, replace: true, message });
	};

	const handleLogin = async () => {
		Keyboard.dismiss();
		try {
			// 디버깅에 도움되는 로그 (원인 파악용)
			console.log("API_BASE_URL:", API_BASE_URL);

			await runWithLoading(
				router,
				async () => {
					const res = await fetch(`${API_BASE_URL}/auth/login`, {
						method: "POST",
						headers: { "Content-Type": "application/json" },
						body: JSON.stringify(form),
					});

					if (!res.ok) {
						const text = await res.text().catch(() => "");
						throw new Error(text || `Login failed (${res.status})`);
					}

					// 토큰/세션 처리
					const data = await res.json();
					await setToken(data.token);
				},
				// 성공 후 이동 경로
				typeof params.redirect === "string"
					? (params.redirect as string)
					: "/(main)/home",
				"로그인 중입니다..." // 선택 메시지
			);
		} catch (err: any) {
			console.log("LOGIN ERROR:", err);
			Alert.alert(
				"로그인 실패",
				err?.message ?? "아이디/비밀번호를 확인해주세요."
			);
		}
	};

	return (
		<SafeAreaView
			edges={["top", "bottom"]}
			style={{ flex: 1, backgroundColor: theme.bg }}
		>
			<KeyboardAvoidingView
				behavior="padding" enabled
				style={{ flex:1, justifyContent:'center' }} // 전체 채움 (필수)
			>
				<ScrollView keyboardShouldPersistTaps="handled">
					<View
						style={styles.characterImage}
						onLayout={(e) => {
							const { width } = e.nativeEvent.layout;
							setBoxWidth(width);
						}}
					>
						{/* 캐릭터 이미지 */}
						<Image  style={styles.characterDefault}  source={loginEffDef} resizeMode="contain"/>

						{!showInputFace && (
							<Image style={styles.characterNormalface} source={normalface} resizeMode="contain" />
						)}

						{showPwFace && (
							<Animated.Image
								style={[
									styles.characterPwface,
									{ transform: [{ translateY: pwFaceY }] }, // 아래→위로 상승
								]}
								source={pwface}
								resizeMode="contain"
							/>
						)}

						{!showPwFace && showInputFace && (
							<Animated.Image
								style={[ styles.characterInputface, { transform: [{ translateX: inputFaceX }] } ]}
								source={inputface}
								resizeMode="contain"
							/>
						)}
					</View>
					<View style={styles.inputBox}>
						<TextInput
							placeholder="아이디"
							placeholderTextColor="#909090"
							value={form.user_id}
							onChangeText={(v) => onChange("user_id", v)}
							onFocus={onIdFocus}
							onBlur={onIdBlur}
							autoCapitalize="none"
							returnKeyType="next"
							style={[ styles.input, { color: theme.text, borderColor: theme.border} ]}
						/>
					</View>

					{/* ERD 매핑: user_pw */}
					<View style={styles.inputBox}>
						<TextInput
							placeholder="비밀번호"
							placeholderTextColor="#909090"
							value={form.user_pw}
							onChangeText={(v) => onChange("user_pw", v)}
							onFocus={onPwFocus}
							onBlur={onPwBlur}
							autoCapitalize="none"
							secureTextEntry
							returnKeyType="done"
							style={[ styles.input, { color: theme.text, borderColor: theme.border} ]}
						/>
					</View>

					<TouchableOpacity
						onPress={handleLogin}
						disabled={disabled}
						style={[
							styles.btn,
							disabled && { opacity: 0.6 },
							{ backgroundColor: theme.primary },
						]}
					>
						{loading ? (
							<ActivityIndicator color="#FFFFFF" />
						) : (
							<Text style={styles.btnText}>로그인</Text>
						)}
					</TouchableOpacity>

					<TouchableOpacity
						style={{ marginTop:16, alignSelf: "center" }}
						onPress={() => router.replace("/(auth)/signup")}
					>
						<Text style={[styles.labelText, { color: Colors.blue }]}>
							아직 계정이 없으신가요? 회원가입
						</Text>
					</TouchableOpacity>

					<TouchableOpacity
						style={{ marginTop:16, alignSelf: "center" }}
						onPress={() =>
							startLoading(router, {
								// 테스트용 (여기선 단순히 3초 대기)
								task: async () => {
									await new Promise(r => setTimeout(r, 3000));
								},
								to: "/(main)/home",          // 완료 후 이동할 경로
								replace: true,               // replace로 이동
							})
						}
					>
						<Text style={[styles.labelText, { color: Colors.blue }]}>
							메인 페이지로 강제 건너뛰기 (로딩 테스트)
						</Text>
					</TouchableOpacity>

					<TouchableOpacity
						style={{ marginTop:16, alignSelf: "center" }}
						onPress={() => router.replace("/common/loading")}
					>
						<Text style={[styles.labelText, { color: Colors.blue }]}>
							로딩 페이지 강제 띄우기
						</Text>
					</TouchableOpacity>
				</ScrollView>
			</KeyboardAvoidingView>
		</SafeAreaView>
	);
}

const styles = StyleSheet.create({
	characterImage: {
		display:'flex',
		justifyContent:'center',
		alignItems: 'center',
		alignSelf:'center',
		overflow:'hidden',
		borderRadius:'50%',
		width:312,
		height:312,
		marginBottom:30,
		borderWidth:5,
		borderStyle:'solid',
		borderColor:'#666',
	},
	characterDefault:{
		position:'absolute',
		top:'50%',
		left:'50%',
		transform:[{translateX:-200},{translateY:-200}],
		width:400,
		height:400,
		marginTop:60,
	},
	characterNormalface:{
		position:'absolute',
		top:160,
		left:'50%',
		transform:[{translateX:-90}],
		width:180,
		zIndex:2,
	},
	characterInputface:{
		position:'absolute',
		top:180,
		left:30,
		transform:[{translateX:-95}],
		width:180,
		zIndex:2,
	},
	characterPwface:{ 
		position:'absolute', 
		top:100, 
		width:230, 
		height:180,
		zIndex:2,
	},
	inputBox: {
		marginBottom:16,
	},
	labelText: {
		marginBottom:6,
		fontSize:14
	},
	input: {
		borderWidth: 1,
		borderRadius: 12,
		paddingHorizontal: 14,
		paddingVertical: 12,
		fontSize: 16,
	},
	inputLight: {
		borderColor: Colors.light.border,
		backgroundColor: Colors.light.secondary,
		color: Colors.light.text,
	},
	inputDark: {
		borderColor: Colors.dark.border,
		backgroundColor: Colors.dark.secondary,
		color: Colors.dark.text,
	},
	btn: {
		paddingVertical: 14,
		borderRadius: 14,
		alignItems: "center",
	},
	btnText: {
		color: Colors.dark.text,
		fontSize: 18,
		fontWeight: "700",
	},
});
