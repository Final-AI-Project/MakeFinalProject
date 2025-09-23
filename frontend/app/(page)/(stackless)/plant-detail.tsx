// 파일: app/(page)/(stackless)/plant-detail.tsx
// ─────────────────────────────────────────────────────────────────────────────
// ① Imports
// ─────────────────────────────────────────────────────────────────────────────
import React, { useState } from "react";
import {
    View, Text, StyleSheet, ScrollView, Image, Pressable, TouchableOpacity,
    TextInput, ActivityIndicator
} from "react-native";
import { useLocalSearchParams } from "expo-router";
import { useRouter, type Href } from "expo-router";
import * as ImagePicker from "expo-image-picker";
import { useColorScheme } from "react-native";
import Colors from "../../../constants/Colors";
import { getApiUrl, API_ENDPOINTS } from "../../../config/api";
import { getToken } from "../../../libs/auth";
import { showAlert } from "../../../components/common/appAlert";

// ─────────────────────────────────────────────────────────────────────────────
// ② Types & Constants
// ─────────────────────────────────────────────────────────────────────────────
type PestLog = { id: string; note: string; createdAt: string };
type DiaryLog = { id: string; text: string; createdAt: string };
type WaterLog = { id: string; reason: string; createdAt: string };

const fmtDate = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

// ─────────────────────────────────────────────────────────────────────────────
// ③ Component
// ─────────────────────────────────────────────────────────────────────────────
export default function PlantDetail() {
    // 3-1) Theme & Router & Params
    const router = useRouter();
    const scheme = useColorScheme();
    const theme = Colors[scheme === "dark" ? "dark" : "light"];

    // 리스트/등록 화면에서 전달받은 초기 값
    const params = useLocalSearchParams<{
        imageUri?: string;
        nickname?: string;
        species?: string;
        startedAt?: string;
        plantId?: string;
        id?: string; // 삭제 시 사용되는 듯하여 유지
    }>();

    // 3-2) Local States
    const [imageUri, setImageUri] = useState<string | null>(params.imageUri ?? null);
    const [nickname] = useState<string>(params.nickname ?? "");
    const [species] = useState<string>(params.species ?? "");
    const [startedAt] = useState<string>(params.startedAt ?? "");
    const [health, setHealth] = useState<string>("좋음"); // 기본값
    const [watering, setWatering] = useState('');
    const [pestLogs] = useState<PestLog[]>([]);
    const [diaryLogs] = useState<DiaryLog[]>([]);
    const [waterLogs, setWaterLogs] = useState<WaterLog[]>([]);
    const [busy, setBusy] = useState(false);

    // 3-3) Photo handlers (사진 변경)
    async function changePhoto() {
        const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (status !== "granted") {
            showAlert({
                title: "권한 필요",
                message: "앨범 접근 권한을 허용해주세요.",
                buttons: [{ text: "확인" }],
            });
            return;
        }
        setBusy(true);
        try {
            const res = await ImagePicker.launchImageLibraryAsync({
                allowsEditing: true,
                quality: 0.9,
                mediaTypes: ["images"] as any, // ✅ 최신 enum 대체
                aspect: [1, 1],
            });
            if (!res.canceled && res.assets?.[0]?.uri) {
                setImageUri(res.assets[0].uri);
            }
        } finally {
            setBusy(false);
        }
    }

    // 3-4) “습도계 지수 n% 증가 시 물준날로 기록?”
    const [humidityRise, setHumidityRise] = useState<string>("10");
    function markWateringByHumidity() {
        const n = Number(humidityRise);
        if (Number.isNaN(n) || n <= 0) {
            showAlert({
                title: "값 확인",
                message: "증가 퍼센트를 숫자로 입력해주세요.",
                buttons: [{ text: "확인" }],
            });
            return;
        }
        setWaterLogs(prev => [
            { id: String(Date.now()), reason: `습도 +${n}%`, createdAt: fmtDate(new Date()) },
            ...prev,
        ]);
        showAlert({
            title: "기록 완료",
            message: `습도 ${n}% 증가로 물 준 날을 기록했어요.`,
            buttons: [{ text: "확인" }],
        });
    }

    // 3-5) Delete / Edit / Back
    async function onDelete() {
        showAlert({
            title: "삭제 확인",
            message: "정말 이 식물을 삭제할까요?",
            buttons: [
                { text: "취소", style: "cancel" },
                {
                    text: "삭제",
                    style: "destructive",
                    onPress: async () => {
                        try {
                            setBusy(true);

                            // 토큰 가져오기
                            const token = await getToken();
                            if (!token) {
                                showAlert({
                                    title: "오류",
                                    message: "로그인이 필요합니다.",
                                    buttons: [{ text: "확인" }],
                                });
                                return;
                            }

                            // API URL 생성
                            const apiUrl = getApiUrl(API_ENDPOINTS.PLANTS.DELETE(Number(params.id)));

                            // 삭제 요청
                            const response = await fetch(apiUrl, {
                                method: "DELETE",
                                headers: {
                                    Authorization: `Bearer ${token}`,
                                    "Content-Type": "application/json",
                                },
                            });

                            if (!response.ok) {
                                const errorData = await response.json().catch(() => ({}));
                                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                            }

                            const result = await response.json();
                            showAlert({
                                title: "삭제 완료",
                                message: result.message || "식물이 성공적으로 삭제되었습니다.",
                                buttons: [{ text: "확인", onPress: () => router.back() }],
                            });
                        } catch (error: any) {
                            console.error("식물 삭제 실패:", error);
                            showAlert({
                                title: "삭제 실패",
                                message: error?.message || "식물 삭제 중 오류가 발생했습니다.",
                                buttons: [{ text: "확인" }],
                            });
                        } finally {
                            setBusy(false);
                        }
                    },
                },
            ],
            dismissible: false,
        });
    }

    function goEdit() {
        router.push("/(page)/(stackless)/plant-new");
    }

    // 3-6) ✨ 기록/일기 페이지로 이동
    function goPestNew() {
        const href: Href = {
            pathname: "/(page)/medical" as const,
            params: { plantId: String(params.plantId ?? ""), nickname, species },
        };
        router.push(href);
    }

    function goDiaryNew() {
        const href: Href = {
            pathname: "/(page)/diary" as const,
            params: { plantId: String(params.plantId ?? ""), nickname, species },
        };
        router.push(href);
    }

    // 3-7) Render
    return (
        <View style={[styles.container, { backgroundColor: theme.bg }]}>
            <ScrollView contentContainerStyle={{ paddingBottom: 140 }}>
                {/* 사진 섹션 */}
                <View style={styles.photoBox}>
                    <Pressable
                        onPress={changePhoto}
                        disabled={busy}
                        style={[styles.photoPlaceholder, { borderColor: theme.border, backgroundColor: theme.graybg }]}
                    >
                        {imageUri ? (
                            <>
                                <Image source={{ uri: imageUri }} style={styles.photo} resizeMode="cover" />
                                <View style={[styles.changeBadge, { borderColor: theme.border, backgroundColor: theme.bg + "cc" }]}>
                                    <Text style={[styles.changeBadgeText, { color: theme.text }]}>사진 변경</Text>
                                </View>
                            </>
                        ) : (
                            <>
                                <Text style={{ color: theme.text, fontSize: 40 }}>+</Text>
                                <Text style={{ color: theme.text, marginTop: 4 }}>사진을 등록하세요</Text>
                            </>
                        )}
                    </Pressable>
                    {busy && (
                        <View style={styles.busyOverlay}>
                            <ActivityIndicator size="large" />
                        </View>
                    )}
                </View>

                {/* 기본 정보 */}
                <View style={styles.card}>
                    <Text style={[styles.cardTitle, { color: theme.text }]}>기본 정보</Text>
                    <View style={styles.rowBetween}>
                        <Text style={[styles.kvKey, { color: theme.text }]}>별명</Text>
                        <Text style={[styles.kvVal, { color: theme.text }]}>{nickname || "-"}</Text>
                    </View>
                    <View style={styles.rowBetween}>
                        <Text style={[styles.kvKey, { color: theme.text }]}>품종</Text>
                        <Text style={[styles.kvVal, { color: theme.text }]}>{species || "-"}</Text>
                    </View>
                    <View style={styles.rowBetween}>
                        <Text style={[styles.kvKey, { color: theme.text }]}>키우기 시작한 날</Text>
                        <Text style={[styles.kvVal, { color: theme.text }]}>{startedAt || "-"}</Text>
                    </View>
                </View>

                {/* 건강 상태 */}
                <View style={styles.card}>
                    <Text style={[styles.cardTitle, { color: theme.text }]}>건강 상태</Text>
                    <TextInput
                        placeholder="예: 좋음 / 잎끝 마름 / 새잎 돋음 등"
                        placeholderTextColor="#909090"
                        readOnly={true}
                        value={health}
                        onChangeText={setHealth}
                        style={[styles.input, { color: theme.text, borderColor: theme.border }]}
                    />
                </View>

                {/* 병충해 기록 (보기 전용 / 작성은 페이지 이동) */}
                <View style={styles.card}>
                    <View style={styles.cardHeader}>
                        <Text style={[styles.cardTitle, { color: theme.text }]}>병충해 기록</Text>
                        <TouchableOpacity style={[styles.smallBtn, { backgroundColor: theme.primary }]} onPress={goPestNew}>
                            <Text style={styles.smallBtnText}>기록 추가</Text>
                        </TouchableOpacity>
                    </View>
                    {pestLogs.length === 0 ? (
                        <Text style={{ color: "#888" }}>기록이 없어요.</Text>
                    ) : (
                        pestLogs.map(log => (
                            <View key={log.id} style={styles.listRow}>
                                <Text style={[styles.listDate, { color: theme.text }]}>{log.createdAt}</Text>
                                <Text style={[styles.listText, { color: theme.text }]}>{log.note}</Text>
                            </View>
                        ))
                    )}
                </View>

                {/* 일기 목록 (보기 전용 / 작성은 페이지 이동) */}
                <View style={styles.card}>
                    <View style={styles.cardHeader}>
                        <Text style={[styles.cardTitle, { color: theme.text }]}>일기 목록</Text>
                        <TouchableOpacity style={[styles.smallBtn, { backgroundColor: theme.primary }]} onPress={goDiaryNew}>
                            <Text style={styles.smallBtnText}>일기 작성</Text>
                        </TouchableOpacity>
                    </View>
                    {diaryLogs.length === 0 ? (
                        <Text style={{ color: "#888" }}>작성한 일기가 없어요.</Text>
                    ) : (
                        diaryLogs.map(log => (
                            <View key={log.id} style={styles.listRow}>
                                <Text style={[styles.listDate, { color: theme.text }]}>{log.createdAt}</Text>
                                <Text style={[styles.listText, { color: theme.text }]}>{log.text}</Text>
                            </View>
                        ))
                    )}
                </View>

                {/* 다음 물 주기 */}
                <View style={styles.card}>
                    <Text style={[styles.cardTitle, { color: theme.text }]}>다음 물주기</Text>
                    <TextInput
                        placeholder="2025-09-23"
                        placeholderTextColor="#909090"
                        readOnly={true}
                        value={watering}
                        onChangeText={setWatering}
                        style={[styles.input, { color: theme.text, borderColor: theme.border }]}
                    />
                </View>

                {/* 일기 목록 (보기 전용 / 작성은 페이지 이동) */}
                <View style={styles.card}>
                    <View style={styles.cardHeader}>
                        <Text style={[styles.cardTitle, { color: theme.text }]}>일기 목록</Text>
                        <TouchableOpacity style={[styles.smallBtn, { backgroundColor: theme.primary }]} onPress={goDiaryNew}>
                            <Text style={styles.smallBtnText}>일기 작성</Text>
                        </TouchableOpacity>
                    </View>
                    {diaryLogs.length === 0 ? (
                        <Text style={{ color: "#888" }}>작성한 일기가 없어요.</Text>
                    ) : (
                        diaryLogs.map(log => (
                            <View key={log.id} style={styles.listRow}>
                                <Text style={[styles.listDate, { color: theme.text }]}>{log.createdAt}</Text>
                                <Text style={[styles.listText, { color: theme.text }]}>{log.text}</Text>
                            </View>
                        ))
                    )}
                </View>

                {/* 내 식물 품종 정보 (BD 연동 전 비움) */}
                <View style={styles.card}>
                    <Text style={[styles.cardTitle, { color: theme.text }]}>내 식물 품종 정보</Text>
                    <Text style={{ color: "#888" }}>DB 연동 예정입니다.</Text>
                </View>
            </ScrollView>

            {/* 하단 고정 버튼들 */}
            <View style={[styles.bottomBar, { backgroundColor: theme.bg }]}>
                <TouchableOpacity style={[styles.bottomBtn, styles.outlineBtn, { borderColor: theme.border }]} onPress={() => router.back()}>
                    <Text style={[styles.bottomBtnText, { color: theme.text }]}>뒤로가기</Text>
                </TouchableOpacity>
                <TouchableOpacity style={[styles.bottomBtn, { backgroundColor: "#d32f2f" }]} onPress={onDelete}>
                    <Text style={styles.bottomBtnText}>식물 삭제</Text>
                </TouchableOpacity>
                <TouchableOpacity style={[styles.bottomBtn, { backgroundColor: theme.primary }]} onPress={goEdit}>
                    <Text style={styles.bottomBtnText}>수정하기</Text>
                </TouchableOpacity>
            </View>
        </View>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// ④ Styles
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
    container: { flex: 1 },

    // Photo
    photoBox: { alignItems: "center", position: "relative", height: 260 },
    photo: { position: "absolute", left: 0, top: 0, width: "100%", height: 260, resizeMode: "cover" },
    photoPlaceholder: { width: "100%", height: 260, alignItems: "center", justifyContent: "center" },
    changeBadge: { position: "absolute", right: 24, bottom: 10, borderWidth: 1, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6 },
    changeBadgeText: { fontSize: 12, fontWeight: "700" },

    busyOverlay: {
        position: "absolute", left: 24, right: 24, top: 0, bottom: 0,
        alignItems: "center", justifyContent: "center", backgroundColor: "rgba(0,0,0,0.08)", borderRadius: 12,
    },

    // Cards
    card: { marginTop: 16, marginHorizontal: 24, borderWidth: 1, borderColor: "#e0e0e0", borderRadius: 12, padding: 14 },
    cardHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 6 },
    cardTitle: { fontSize: 16, fontWeight: "800", marginBottom: 8 },

    // Rows & K/V
    row: { flexDirection: "row", alignItems: "center", gap: 8 },
    rowBetween: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: 8 },
    kvKey: { fontSize: 14, fontWeight: "600" },
    kvVal: { fontSize: 14, fontWeight: "500" },

    // Inputs & small controls
    input: { height: 50, borderWidth: 1, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10 },
    inputSmall: { width: 80 },
    unit: { fontSize: 14 },

    smallBtn: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8 },
    smallBtnText: { color: "#fff", fontWeight: "700" },

    // Lists
    listRow: { flexDirection: "row", gap: 10, paddingVertical: 6 },
    listDate: { fontSize: 12, opacity: 0.8, width: 84 },
    listText: { flex: 1, fontSize: 14 },

    // Bottom bar
    bottomBar: {
        position: "absolute", left: 0, right: 0, bottom: 0,
        flexDirection: "row", gap: 8, padding: 12,
    },
    bottomBtn: { flex: 1, height: 48, borderRadius: 12, alignItems: "center", justifyContent: "center" },
    outlineBtn: { borderWidth: 1 },
    bottomBtnText: { color: "#fff", fontSize: 15, fontWeight: "700" },
});
