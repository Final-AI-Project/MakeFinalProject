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
  Easing,
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
import { startLoading, stopLoading } from "../../components/common/loading";
import { getApiUrl, API_ENDPOINTS } from "../../config/api";

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
      targetX = boxWidth / 2 - 30 - 95;
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
    startLoading(router, { task, to: to as any, replace: true, message });
  };

  const handleLogin = async () => {
    Keyboard.dismiss();
    setLoading(true);
    try {
      // 백엔드가 기대하는 데이터 구조로 변환
      const requestData = {
        id_or_email: form.user_id,
        password: form.user_pw,
      };

      // 공용 API 설정을 사용하여 URL 생성
      const loginUrl = await getApiUrl(API_ENDPOINTS.AUTH.LOGIN);
      console.log("Sending login request to:", loginUrl);
      console.log("Request data:", requestData);

      const res = await fetch(loginUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        mode: "cors", // CORS 모드 명시적 설정
        body: JSON.stringify(requestData),
      });

      console.log("Response status:", res.status);
      console.log("Response ok:", res.ok);

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        console.log("Error response text:", text);
        throw new Error(text || `Login failed (${res.status})`);
      }

      // 백엔드 응답 구조에 맞게 토큰 처리
      const data = await res.json();
      console.log("Response data:", data);
      console.log("Response data keys:", Object.keys(data));
      console.log("Access token:", data.access_token);

      if (!data.access_token) {
        throw new Error("No access token received from server");
      }

      await setToken(data.access_token);

      // 로그인 성공 후 home으로 이동
      const next =
        typeof params.redirect === "string"
          ? (params.redirect as string)
          : "/(page)/home";
      router.replace(next as any);
    } catch (err: any) {
      console.error("Login error:", err);

      // 서버 연결 실패인지 확인
      const isConnectionError =
        err?.message?.includes("서버에 연결할 수 없습니다") ||
        err?.message?.includes("fetch") ||
        err?.message?.includes("Network") ||
        err?.message?.includes("connection");

      if (isConnectionError) {
        Alert.alert(
          "서버 연결 실패",
          "서버에 연결할 수 없습니다.\n백엔드 서버가 실행 중인지 확인해주세요.",
          [{ text: "확인" }]
        );
      } else {
        // 인증 실패 (아이디/비밀번호 오류)
        Alert.alert(
          "로그인 실패",
          "아이디 또는 비밀번호가 올바르지 않습니다.\n\n혹시 아직 회원가입을 하지 않으셨나요?",
          [
            { text: "다시 시도", style: "cancel" },
            {
              text: "회원가입",
              onPress: () => router.replace("/(auth)/signup" as any),
            },
          ]
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView
      edges={["top", "bottom"]}
      style={{ flex: 1, paddingHorizontal: 24, backgroundColor: theme.bg }}
    >
      <KeyboardAvoidingView
        behavior="padding"
        enabled
        style={{ flex: 1, justifyContent: "center" }} // 전체 채움 (필수)
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
            <Image
              style={styles.characterDefault}
              source={loginEffDef}
              resizeMode="contain"
            />

            {!showInputFace && (
              <Image
                style={styles.characterNormalface}
                source={normalface}
                resizeMode="contain"
              />
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
                style={[
                  styles.characterInputface,
                  { transform: [{ translateX: inputFaceX }] },
                ]}
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
              style={[
                styles.input,
                { color: theme.text, borderColor: theme.border },
              ]}
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
              style={[
                styles.input,
                { color: theme.text, borderColor: theme.border },
              ]}
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
            style={{ marginTop: 16, alignSelf: "center" }}
            onPress={() => router.replace("/(auth)/signup")}
          >
            <Text style={[styles.labelText, { color: Colors.blue }]}>
              아직 계정이 없으신가요? 회원가입
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={{ marginTop: 16, alignSelf: "center" }}
            onPress={() =>
              startLoading(router, {
                // 테스트용 (여기선 단순히 3초 대기)
                task: async () => {
                  await new Promise((r) => setTimeout(r, 3000));
                },
                to: "/(page)/home", // 완료 후 이동할 경로
                replace: true, // replace로 이동
              })
            }
          >
            <Text style={[styles.labelText, { color: Colors.blue }]}>
              메인 페이지로 강제 건너뛰기 (로딩 테스트)
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
		height:50,
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
