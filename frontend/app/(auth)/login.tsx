// app/(auth)/login.tsx
import React, { useMemo, useState } from "react";
import { View, Text, TextInput, TouchableOpacity, Alert, KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator } from "react-native";
import { useRouter, useLocalSearchParams } from "expo-router";
import { setToken } from "../../lib/auth";

// 서버 주소를 환경에 맞게 바꿔주세요.
const API_BASE_URL = "http://localhost:8080";

type LoginForm = {
    user_id: string;
    user_pw: string;
};

export default function LoginScreen() {
    const router = useRouter();
    const params = useLocalSearchParams<{ redirect?: string }>();
    const [form, setForm] = useState<LoginForm>({ user_id: "", user_pw: "" });
    const [loading, setLoading] = useState(false);

    const disabled = useMemo(() => !form.user_id || !form.user_pw, [form]);

    const onChange = (key: keyof LoginForm, val: string) => {
        setForm(prev => ({ ...prev, [key]: val }));
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

            Alert.alert("로그인", "로그인 성공했습니다!", [
                {
                    text: "확인",
                    onPress: () => {
                        const next = typeof params.redirect === "string" ? params.redirect : "/(main)/home";
                        router.replace(next);
                    },
                },
            ]);
        } catch (err: any) {
            Alert.alert("로그인 실패", err?.message ?? "아이디/비밀번호를 확인해주세요.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <KeyboardAvoidingView behavior={Platform.select({ ios: "padding", android: undefined })} style={{ flex: 1, backgroundColor: "#0B1020" }}>
            <ScrollView contentContainerStyle={{ padding: 20 }}>
                <Text style={{ fontSize: 28, fontWeight: "700", color: "#E5ECFF", marginBottom: 16 }}>로그인</Text>

                {/* ERD 매핑: user_id */}
                <View style={{ marginBottom: 12 }}>
                    <Text style={{ color: "#9FB0FF", marginBottom: 6 }}>아이디 (user_id)</Text>
                    <TextInput
                        placeholder="아이디"
                        placeholderTextColor="#8A8FA3"
                        value={form.user_id}
                        onChangeText={v => onChange("user_id", v)}
                        autoCapitalize="none"
                        style={styles.input}
                    />
                </View>

                {/* ERD 매핑: user_pw */}
                <View style={{ marginBottom: 20 }}>
                    <Text style={{ color: "#9FB0FF", marginBottom: 6 }}>비밀번호 (user_pw)</Text>
                    <TextInput
                        placeholder="비밀번호"
                        placeholderTextColor="#8A8FA3"
                        value={form.user_pw}
                        onChangeText={v => onChange("user_pw", v)}
                        autoCapitalize="none"
                        secureTextEntry
                        style={styles.input}
                    />
                </View>

                <TouchableOpacity
                    onPress={handleLogin}
                    disabled={disabled || loading}
                    style={[styles.btn, (disabled || loading) && { opacity: 0.6 }]}
                >
                    {loading ? <ActivityIndicator /> : <Text style={styles.btnText}>로그인</Text>}
                </TouchableOpacity>

                <TouchableOpacity style={{ marginTop: 16, alignSelf: "center" }} onPress={() => router.push("/(auth)/signup")}>
                    <Text style={{ color: "#B7C4FF" }}>아직 계정이 없으신가요? 회원가입</Text>
                </TouchableOpacity>
            </ScrollView>
        </KeyboardAvoidingView>
    );
}

const styles = {
    input: {
        borderWidth: 1,
        borderColor: "#2A3352",
        backgroundColor: "#141A2B",
        color: "#E5ECFF",
        borderRadius: 12,
        paddingHorizontal: 14,
        paddingVertical: 12,
        fontSize: 16,
    },
    btn: {
        backgroundColor: "#4C6FFF",
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

/* 백엔드 연결 포인트(참고)
{
    "user_id": "string",
    "user_pw": "string"
}
 */