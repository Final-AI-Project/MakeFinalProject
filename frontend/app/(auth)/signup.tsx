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

// 서버 주소를 환경에 맞게 바꿔주세요. (Expo 클라이언트에서 접근하려면 EXPO_PUBLIC_* prefix 권장)
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:3000";

type SignupForm = {
    user_id: string;
    user_pw: string;
    email: string;
    hp: string;       // 휴대폰
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
        () => !form.user_id || !form.user_pw || !form.email || !form.hp || !form.nickname || loading,
        [form, loading]
    );

    const onChange = (key: keyof SignupForm, val: string) => {
        setForm(prev => ({ ...prev, [key]: val }));
    };

    const validate = () => {
        const emailOk = /^\S+@\S+\.\S+$/.test(form.email);
        const hpOk = /^[0-9\-+ ]{9,20}$/.test(form.hp);
        if (!emailOk) { Alert.alert("회원가입", "이메일 형식이 올바르지 않습니다."); return false; }
        if (form.user_pw.length < 6) { Alert.alert("회원가입", "비밀번호는 6자 이상으로 입력해주세요."); return false; }
        if (!hpOk) { Alert.alert("회원가입", "휴대폰 번호 형식을 확인해주세요."); return false; }
        return true;
    };

    const handleSubmit = async () => {
        if (!validate()) return;
        try {
            Keyboard.dismiss(); // 모든 인풋 포커스 해제 + 키보드 닫기
            setLoading(true);
            const res = await fetch(`${API_BASE_URL}/auth/signup`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(form),
            });
            if (!res.ok) {
                const text = await res.text().catch(() => "");
                throw new Error(text || `Sign up failed (${res.status})`);
            }
            Alert.alert("회원가입", "회원가입이 완료되었습니다. 로그인 화면으로 이동합니다.", [
                { text: "확인", onPress: () => router.replace("/(auth)/login") },
            ]);
        } catch (err: any) {
            Alert.alert("회원가입 실패", err?.message ?? "잠시 후 다시 시도해주세요.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: theme.bg }}>
            <KeyboardAvoidingView
                behavior={Platform.select({ ios: "padding", android: undefined })}
                style={{ flex: 1 }}
            >
                <ScrollView keyboardShouldPersistTaps="handled">

                    <View style={styles.field}>
                        <Text style={[styles.label, { color: theme.text }]}>아이디 (user_id)</Text>
                        <TextInput
                            placeholder="아이디를 입력하세요"
                            placeholderTextColor={placeholderColor}
                            value={form.user_id}
                            onChangeText={v => onChange("user_id", v)}
                            autoCapitalize="none"
							style={[styles.input, { color: theme.text, borderColor: theme.border }]}
                        />
                    </View>

                    {/* ERD 매핑: user_pw */}
                    <View style={styles.field}>
                        <Text style={[styles.label, { color: theme.text }]}>비밀번호 (user_pw)</Text>
                        <TextInput
                            placeholder="비밀번호 (6자 이상)"
                            placeholderTextColor={placeholderColor}
                            value={form.user_pw}
                            onChangeText={v => onChange("user_pw", v)}
                            secureTextEntry
                            autoCapitalize="none"
							style={[styles.input, { color: theme.text, borderColor: theme.border }]}
                        />
                    </View>

                    {/* ERD 매핑: email */}
                    <View style={styles.field}>
                        <Text style={[styles.label, { color: theme.text }]}>이메일 (email)</Text>
                        <TextInput
                            placeholder="example@domain.com"
                            placeholderTextColor={placeholderColor}
                            keyboardType="email-address"
                            value={form.email}
                            onChangeText={v => onChange("email", v)}
                            autoCapitalize="none"
							style={[styles.input, { color: theme.text, borderColor: theme.border }]}
                        />
                    </View>

                    {/* ERD 매핑: hp */}
                    <View style={styles.field}>
                        <Text style={[styles.label, { color: theme.text }]}>휴대폰 (hp)</Text>
                        <TextInput
                            placeholder="010-1234-5678"
                            placeholderTextColor={placeholderColor}
                            keyboardType="phone-pad"
                            value={form.hp}
                            onChangeText={v => onChange("hp", v)}
							style={[styles.input, { color: theme.text, borderColor: theme.border }]}
                        />
                    </View>

                    {/* ERD 매핑: nickname */}
                    <View style={styles.field}>
                        <Text style={[styles.label, { color: theme.text }]}>닉네임 (nickname)</Text>
                        <TextInput
                            placeholder="별명을 입력하세요"
                            placeholderTextColor={placeholderColor}
                            value={form.nickname}
                            onChangeText={v => onChange("nickname", v)}
							style={[styles.input, { color: theme.text, borderColor: theme.border }]}
                        />
                    </View>

                    <TouchableOpacity
                        onPress={handleSubmit}
                        disabled={disabled}
                        style={[styles.btn, { backgroundColor: theme.primary }, disabled && { opacity: 0.6 }]}
                    >
                        {loading ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.btnText}>회원가입</Text>}
                    </TouchableOpacity>

                    <TouchableOpacity style={{ marginTop: 16, alignSelf: "center" }} onPress={() => router.replace("/(auth)/login")}>
                        <Text style={{ color: Colors.blue }}>이미 계정이 있으신가요? 로그인</Text>
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
