// app/(auth)/signup.tsx
import React, { useMemo, useState } from "react";
import { View, Text, TextInput, TouchableOpacity, Alert, KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator } from "react-native";
import { useRouter } from "expo-router";

// 서버 주소를 환경에 맞게 바꿔주세요.
const API_BASE_URL = "http://localhost:8080";

type SignupForm = {
    user_id: string;
    user_pw: string;
    email: string;
    hp: string;         // 휴대폰
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
    const disabled = useMemo(() => {
        return !form.user_id || !form.user_pw || !form.email || !form.hp || !form.nickname;
    }, [form]);

    const onChange = (key: keyof SignupForm, val: string) => {
        setForm(prev => ({ ...prev, [key]: val }));
    };

    const validate = () => {
        const emailOk = /^\S+@\S+\.\S+$/.test(form.email);
        const hpOk = /^[0-9\-+ ]{9,20}$/.test(form.hp);
        if (!emailOk) return Alert.alert("회원가입", "이메일 형식이 올바르지 않습니다.");
        if (form.user_pw.length < 6) return Alert.alert("회원가입", "비밀번호는 6자 이상으로 입력해주세요.");
        if (!hpOk) return Alert.alert("회원가입", "휴대폰 번호 형식을 확인해주세요.");
        return true;
    };

    const handleSubmit = async () => {
        if (!validate()) return;
        try {
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
        <KeyboardAvoidingView behavior={Platform.select({ ios: "padding", android: undefined })} style={{ flex: 1, backgroundColor: "#0B1020" }}>
            <ScrollView contentContainerStyle={{ padding: 20 }}>
                <Text style={{ fontSize: 28, fontWeight: "700", color: "#E5ECFF", marginBottom: 16 }}>회원가입</Text>

                {/* ERD 매핑: user_id */}
                <View style={{ marginBottom: 12 }}>
                    <Text style={{ color: "#9FB0FF", marginBottom: 6 }}>아이디 (user_id)</Text>
                    <TextInput
                        placeholder="아이디를 입력하세요"
                        placeholderTextColor="#8A8FA3"
                        value={form.user_id}
                        onChangeText={v => onChange("user_id", v)}
                        autoCapitalize="none"
                        style={styles.input}
                    />
                </View>

                {/* ERD 매핑: user_pw */}
                <View style={{ marginBottom: 12 }}>
                    <Text style={{ color: "#9FB0FF", marginBottom: 6 }}>비밀번호 (user_pw)</Text>
                    <TextInput
                        placeholder="비밀번호 (6자 이상)"
                        placeholderTextColor="#8A8FA3"
                        value={form.user_pw}
                        onChangeText={v => onChange("user_pw", v)}
                        secureTextEntry
                        autoCapitalize="none"
                        style={styles.input}
                    />
                </View>

                {/* ERD 매핑: email */}
                <View style={{ marginBottom: 12 }}>
                    <Text style={{ color: "#9FB0FF", marginBottom: 6 }}>이메일 (email)</Text>
                    <TextInput
                        placeholder="example@domain.com"
                        placeholderTextColor="#8A8FA3"
                        keyboardType="email-address"
                        value={form.email}
                        onChangeText={v => onChange("email", v)}
                        autoCapitalize="none"
                        style={styles.input}
                    />
                </View>

                {/* ERD 매핑: hp */}
                <View style={{ marginBottom: 12 }}>
                    <Text style={{ color: "#9FB0FF", marginBottom: 6 }}>휴대폰 (hp)</Text>
                    <TextInput
                        placeholder="010-1234-5678"
                        placeholderTextColor="#8A8FA3"
                        keyboardType="phone-pad"
                        value={form.hp}
                        onChangeText={v => onChange("hp", v)}
                        style={styles.input}
                    />
                </View>

                {/* ERD 매핑: nickname */}
                <View style={{ marginBottom: 20 }}>
                    <Text style={{ color: "#9FB0FF", marginBottom: 6 }}>닉네임 (nickname)</Text>
                    <TextInput
                        placeholder="별명을 입력하세요"
                        placeholderTextColor="#8A8FA3"
                        value={form.nickname}
                        onChangeText={v => onChange("nickname", v)}
                        style={styles.input}
                    />
                </View>

                <TouchableOpacity
                    onPress={handleSubmit}
                    disabled={disabled || loading}
                    style={[styles.btn, (disabled || loading) && { opacity: 0.6 }]}
                >
                    {loading ? <ActivityIndicator /> : <Text style={styles.btnText}>회원가입</Text>}
                </TouchableOpacity>

                <TouchableOpacity style={{ marginTop: 16, alignSelf: "center" }} onPress={() => router.push("/(auth)/login")}>
                    <Text style={{ color: "#B7C4FF" }}>이미 계정이 있으신가요? 로그인</Text>
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
    "user_pw": "string",
    "email": "string",
    "hp": "string",
    "nickname": "string"
}
 */