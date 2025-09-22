// app/(auth)/signup.tsx
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
  Keyboard,
  StyleSheet,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import Colors from "../../constants/Colors";
import { useColorScheme } from "react-native";

import { API_BASE_URL } from "../../config/api";

type SignupForm = {
  user_id: string;
  user_pw: string;
  email: string;
  hp: string; // 휴대폰
  nickname: string;
};

export default function SignupScreen() {
  const router = useRouter();
  const [form, setForm] = useState<SignupForm>({
    user_id: "",
    user_pw: "",
    email: "",
    hp: "",
    nickname: "",
  });
  const [loading, setLoading] = useState(false);

  // ✅ 테마 연동 (로그인 화면과 동일)
  const scheme = useColorScheme();
  const theme = Colors[scheme === "dark" ? "dark" : "light"];
  const placeholderColor = scheme === "dark" ? "#8A8FA3" : "#909090";

  const disabled = useMemo(
    () =>
      !form.user_id ||
      !form.user_pw ||
      !form.email ||
      !form.hp ||
      !form.nickname ||
      loading,
    [form, loading]
  );

  const onChange = (key: keyof SignupForm, val: string) => {
    // 휴대폰 번호 하이픈 자동 입력
    if (key === "hp") {
      // 숫자만 추출
      const numbers = val.replace(/[^0-9]/g, "");
      // 3-4-4 형식으로 포맷팅
      let formatted = numbers;
      if (numbers.length > 3) {
        formatted = numbers.slice(0, 3) + "-" + numbers.slice(3);
      }
      if (numbers.length > 7) {
        formatted =
          numbers.slice(0, 3) +
          "-" +
          numbers.slice(3, 7) +
          "-" +
          numbers.slice(7, 11);
      }
      setForm((prev) => ({ ...prev, [key]: formatted }));
    } else {
      setForm((prev) => ({ ...prev, [key]: val }));
    }
  };

  const validate = () => {
    const emailOk = /^\S+@\S+\.\S+$/.test(form.email);
    const hpOk = /^010-\d{4}-\d{4}$/.test(form.hp);
    if (!emailOk) {
      Alert.alert("회원가입", "이메일 형식이 올바르지 않습니다.");
      return false;
    }
    if (form.user_pw.length < 8) {
      Alert.alert("회원가입", "비밀번호는 8자 이상으로 입력해주세요.");
      return false;
    }
    if (!hpOk) {
      Alert.alert("회원가입", "휴대폰 번호 형식을 확인해주세요.");
      return false;
    }
    return true;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    try {
      Keyboard.dismiss(); // 모든 인풋 포커스 해제 + 키보드 닫기
      setLoading(true);

      console.log("Sending signup request to:", `${API_BASE_URL}/auth/signup`);
      console.log("Request data:", form);

      const res = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(form),
      });

      console.log("Response status:", res.status);
      console.log("Response ok:", res.ok);

      if (!res.ok) {
        let errorMessage = "회원가입에 실패했습니다.";
        let errorTitle = "회원가입 실패";

        try {
          const errorData = await res.json();
          console.log("Error response data:", errorData);

          // 백엔드에서 보내는 구체적인 오류 메시지 처리
          if (errorData.detail) {
            errorMessage = errorData.detail;
          } else if (errorData.message) {
            errorMessage = errorData.message;
          }

          // HTTP 상태 코드에 따른 제목 설정
          if (res.status === 400) {
            errorTitle = "입력 오류";
            if (errorMessage.includes("이미 존재")) {
              errorMessage = "이미 사용 중인 아이디 또는 이메일입니다.";
            }
          } else if (res.status === 409) {
            errorTitle = "중복 오류";
            errorMessage = "이미 사용 중인 아이디 또는 이메일입니다.";
          } else if (res.status >= 500) {
            errorTitle = "서버 오류";
            errorMessage = "서버에 일시적인 문제가 발생했습니다.";
          }
        } catch (parseError) {
          // JSON 파싱 실패 시 HTTP 상태 코드로 판단
          if (res.status === 400) {
            errorTitle = "입력 오류";
            errorMessage = "입력한 정보를 다시 확인해주세요.";
          } else if (res.status === 409) {
            errorTitle = "중복 오류";
            errorMessage = "이미 사용 중인 아이디 또는 이메일입니다.";
          } else if (res.status >= 500) {
            errorTitle = "서버 오류";
            errorMessage = "서버에 일시적인 문제가 발생했습니다.";
          }
        }

        throw new Error(`${errorTitle}|${errorMessage}`);
      }

      // 회원가입 성공
      const data = await res.json();
      console.log("Signup success:", data);

      Alert.alert(
        "🎉 회원가입 완료",
        "회원가입이 성공적으로 완료되었습니다!\n로그인 화면으로 이동합니다.",
        [{ text: "확인", onPress: () => router.replace("/(auth)/login") }]
      );
    } catch (err: any) {
      console.error("Signup error:", err);

      // 오류 메시지 파싱 (제목|내용 형식)
      const errorParts = err?.message?.split("|") || [];
      const errorTitle = errorParts[0] || "회원가입 실패";
      const errorMessage =
        errorParts[1] || err?.message || "알 수 없는 오류가 발생했습니다.";

      // 서버 연결 실패인지 확인
      const isConnectionError =
        err?.message?.includes("fetch") ||
        err?.message?.includes("Network") ||
        err?.message?.includes("connection") ||
        err?.message?.includes("Failed to fetch") ||
        err?.message?.includes("TypeError") ||
        err?.name === "TypeError";

      if (isConnectionError) {
        Alert.alert(
          "🔌 서버 연결 실패",
          "백엔드 서버에 연결할 수 없습니다.\n\n• 백엔드 서버가 실행 중인지 확인해주세요\n• 네트워크 연결을 확인해주세요",
          [
            { text: "다시 시도", style: "default" },
            { text: "확인", style: "cancel" },
          ]
        );
      } else if (errorTitle === "중복 오류") {
        Alert.alert(
          "⚠️ 중복 오류",
          `${errorMessage}\n\n• 다른 아이디를 사용해주세요\n• 다른 이메일을 사용해주세요`,
          [
            { text: "다시 시도", style: "default" },
            { text: "확인", style: "cancel" },
          ]
        );
      } else if (errorTitle === "입력 오류") {
        Alert.alert(
          "📝 입력 오류",
          `${errorMessage}\n\n• 모든 필드를 올바르게 입력해주세요\n• 이메일 형식을 확인해주세요`,
          [
            { text: "다시 시도", style: "default" },
            { text: "확인", style: "cancel" },
          ]
        );
      } else if (errorTitle === "서버 오류") {
        Alert.alert(
          "⚠️ 서버 오류",
          `${errorMessage}\n\n잠시 후 다시 시도해주세요.`,
          [
            { text: "다시 시도", style: "default" },
            { text: "확인", style: "cancel" },
          ]
        );
      } else {
        Alert.alert(
          "❌ 회원가입 실패",
          `${errorMessage}\n\n문제가 지속되면 관리자에게 문의해주세요.`,
          [
            { text: "다시 시도", style: "default" },
            { text: "확인", style: "cancel" },
          ]
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView
      style={{ flex: 1, paddingHorizontal: 24, backgroundColor: theme.bg }}
    >
      <KeyboardAvoidingView
        behavior={Platform.select({ ios: "padding", android: undefined })}
        style={{ flex: 1 }}
      >
        <ScrollView keyboardShouldPersistTaps="handled">
          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.text }]}>
              아이디 (user_id)
            </Text>
            <TextInput
              placeholder="아이디를 입력하세요"
              placeholderTextColor={placeholderColor}
              value={form.user_id}
              onChangeText={(v) => onChange("user_id", v)}
              autoCapitalize="none"
              style={[
                styles.input,
                { color: theme.text, borderColor: theme.border },
              ]}
            />
          </View>

          {/* ERD 매핑: user_pw */}
          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.text }]}>
              비밀번호 (user_pw)
            </Text>
            <TextInput
              placeholder="비밀번호 (8자 이상)"
              placeholderTextColor={placeholderColor}
              value={form.user_pw}
              onChangeText={(v) => onChange("user_pw", v)}
              secureTextEntry
              autoCapitalize="none"
              style={[
                styles.input,
                { color: theme.text, borderColor: theme.border },
              ]}
            />
          </View>

          {/* ERD 매핑: email */}
          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.text }]}>
              이메일 (email)
            </Text>
            <TextInput
              placeholder="example@domain.com"
              placeholderTextColor={placeholderColor}
              keyboardType="email-address"
              value={form.email}
              onChangeText={(v) => onChange("email", v)}
              autoCapitalize="none"
              style={[
                styles.input,
                { color: theme.text, borderColor: theme.border },
              ]}
            />
          </View>

          {/* ERD 매핑: hp */}
          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.text }]}>
              휴대폰 (hp)
            </Text>
            <TextInput
              placeholder="010-1234-5678"
              placeholderTextColor={placeholderColor}
              keyboardType="phone-pad"
              value={form.hp}
              onChangeText={(v) => onChange("hp", v)}
              style={[
                styles.input,
                { color: theme.text, borderColor: theme.border },
              ]}
            />
          </View>

          {/* ERD 매핑: nickname */}
          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.text }]}>
              닉네임 (nickname)
            </Text>
            <TextInput
              placeholder="별명을 입력하세요"
              placeholderTextColor={placeholderColor}
              value={form.nickname}
              onChangeText={(v) => onChange("nickname", v)}
              style={[
                styles.input,
                { color: theme.text, borderColor: theme.border },
              ]}
            />
          </View>

          <TouchableOpacity
            onPress={handleSubmit}
            disabled={disabled}
            style={[
              styles.btn,
              { backgroundColor: theme.primary },
              disabled && { opacity: 0.6 },
            ]}
          >
            {loading ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.btnText}>회원가입</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={{ marginTop: 16, alignSelf: "center" }}
            onPress={() => router.replace("/(auth)/login")}
          >
            <Text style={{ color: Colors.blue }}>
              이미 계정이 있으신가요? 로그인
            </Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  field: {
    marginBottom: 12,
  },
  label: {
    marginBottom: 6,
    fontSize: 14,
    opacity: 0.9,
  },
  input: {
    height: 50,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
  },
  btn: {
    paddingVertical: 14,
    borderRadius: 14,
    alignItems: "center",
  },
  btnText: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "700",
  },
});
