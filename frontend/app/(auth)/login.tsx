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
import { setToken } from "../../lib/auth";
import { useColorScheme, Dimensions, Image } from "react-native";
import Colors from "../../constants/Colors";
import loginEffDef from "../../assets/images/login_eff_def.png";
import normalface from "../../assets/images/login_eff_normalface.png";
import inputface from "../../assets/images/login_eff_inputface.png";
import pwface from "../../assets/images/login_eff_pwface.png";

// 서버 주소를 환경에 맞게 바꿔주세요. (Expo 클라이언트에서 접근하려면 EXPO_PUBLIC_* prefix 필수)
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8080";
const { width: SCREEN_WIDTH } = Dimensions.get("window");

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
		setShowPwFace(false); // 스냅 숨김 (나갈 때는 애니메이션 없이 즉시)
	};

	useEffect(() => {
		const length = form.user_id.length;
		const maxChars = 32;

		let targetX;

		if (length === 0) {
			targetX = SCREEN_WIDTH * 0.09; 
		} else {
			const percent = Math.min(length / maxChars, 1);
			targetX = percent * SCREEN_WIDTH * 0.175;
		}

		Animated.timing(inputFaceX, {
			toValue: targetX,
			duration: 100,
			easing: Easing.out(Easing.quad),
			useNativeDriver: true,
		}).start();
	}, [form.user_id]);

	const onChange = (key: keyof LoginForm, val: string) => {
		setForm((prev) => ({ ...prev, [key]: val }));
	};

	const handleLogin = async () => {
		try {
			Keyboard.dismiss();
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

			const next = typeof params.redirect === "string" ? (params.redirect as string) : "/(main)/home";
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
			style={{ flex: 1, backgroundColor: theme.bg }}
		>
			<KeyboardAvoidingView
				behavior="padding" enabled
				style={{ flex:1, justifyContent:'center' }} // 전체 채움 (필수)
			>
				<ScrollView keyboardShouldPersistTaps="handled">
					<View style={styles.characterImage}>
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
							style={[ styles.input, { color: theme.text } ]}
						/>
					</View>

					{/* ERD 매핑: user_pw */}
					<View style={styles.inputBox}>
						<TextInput
							placeholder="비밀번호"
							placeholderTextColor="#909090"
							value={form.user_pw}
							onChangeText={(v) => onChange("user_pw", v)}
							onFocus={onPwFocus}   // ✅ 추가
							onBlur={onPwBlur}     // ✅ 추가
							autoCapitalize="none"
							secureTextEntry
							returnKeyType="done"
							style={[ styles.input, { color: theme.text } ]}
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
						onPress={() => router.push("/(auth)/signup")}
					>
						<Text style={[styles.labelText, { color: Colors.blue }]}>
							아직 계정이 없으신가요? 회원가입
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
		borderColor: "#666",
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