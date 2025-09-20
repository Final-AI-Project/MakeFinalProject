// 파일: app/(page)/(stackless)/plant-detail.tsx
// ─────────────────────────────────────────────────────────────────────────────
// ① Imports
// ─────────────────────────────────────────────────────────────────────────────
import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  Pressable,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
} from "react-native";
import { useLocalSearchParams } from "expo-router";
import { useRouter, type Href } from "expo-router";
import * as ImagePicker from "expo-image-picker";
import { useColorScheme } from "react-native";
import Colors from "../../../constants/Colors";
import { getApiUrl, API_ENDPOINTS } from "../../../config/api";
import { getToken, refreshToken } from "../../../libs/auth";

// ─────────────────────────────────────────────────────────────────────────────
// ② Types & Constants
// ─────────────────────────────────────────────────────────────────────────────
interface PlantDetail {
  idx: number;
  user_id: string;
  plant_id: number;
  plant_name: string;
  species?: string;
  meet_day?: string;
  current_humidity?: number;
  humidity_date?: string;
  user_plant_image?: string;
  feature?: string;
  temp?: string;
  watering?: string;
  flowering?: string;
  flower_color?: string;
  fertilizer?: string;
  pruning?: string;
  repot?: string;
  toxic?: string;
  diary_count: number;
  growing_location?: string;
}

interface DiaryRecord {
  idx: number;
  plant_idx: number;
  content: string;
  created_at: string;
  image_url?: string;
}

interface PestRecord {
  idx: number;
  plant_idx: number;
  pest_name: string;
  severity: string;
  notes?: string;
  created_at: string;
}

const fmtDate = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate()
  ).padStart(2, "0")}`;

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
    plantIdx?: string;
    imageUri?: string;
    nickname?: string;
    species?: string;
    startedAt?: string;
    plantId?: string;
  }>();

  // 3-2) Local States
  const [plantDetail, setPlantDetail] = useState<PlantDetail | null>(null);
  const [diaryRecords, setDiaryRecords] = useState<DiaryRecord[]>([]);
  const [pestRecords, setPestRecords] = useState<PestRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  // 3-3) API 호출 함수들
  const fetchPlantDetail = async (plantIdx: number) => {
    try {
      const token = await getToken();
      if (!token) {
        Alert.alert("오류", "로그인이 필요합니다.");
        router.push("/(auth)/login");
        return;
      }

      const url = await getApiUrl(API_ENDPOINTS.PLANT_DETAIL.GET(plantIdx));
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.status === 401) {
        const refreshed = await refreshToken();
        if (refreshed) {
          return fetchPlantDetail(plantIdx);
        } else {
          Alert.alert("오류", "로그인이 만료되었습니다.");
          router.push("/(auth)/login");
          return;
        }
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setPlantDetail(data);
    } catch (error) {
      console.error("식물 상세 정보 조회 실패:", error);
      Alert.alert("오류", "식물 정보를 불러오는데 실패했습니다.");
    }
  };

  const fetchDiaryRecords = async (plantIdx: number) => {
    try {
      const token = await getToken();
      if (!token) return;

      const url = await getApiUrl(
        `${API_ENDPOINTS.DIARY.LIST}?plant_idx=${plantIdx}`
      );
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.status === 401) {
        const refreshed = await refreshToken();
        if (refreshed) {
          return fetchDiaryRecords(plantIdx);
        }
        return;
      }

      if (response.ok) {
        const data = await response.json();
        setDiaryRecords(data.diaries || []);
      }
    } catch (error) {
      console.error("일기 목록 조회 실패:", error);
    }
  };

  const fetchPestRecords = async (plantIdx: number) => {
    try {
      const token = await getToken();
      if (!token) return;

      const url = await getApiUrl(
        API_ENDPOINTS.PLANT_DETAIL.PEST_RECORDS(plantIdx)
      );
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.status === 401) {
        const refreshed = await refreshToken();
        if (refreshed) {
          return fetchPestRecords(plantIdx);
        }
        return;
      }

      if (response.ok) {
        const data = await response.json();
        setPestRecords(data || []);
      }
    } catch (error) {
      console.error("병충해 기록 조회 실패:", error);
    }
  };

  // 3-4) useEffect로 데이터 로드
  useEffect(() => {
    const plantIdx = params.plantIdx;
    if (plantIdx) {
      const loadData = async () => {
        setLoading(true);
        await Promise.all([
          fetchPlantDetail(parseInt(plantIdx)),
          fetchDiaryRecords(parseInt(plantIdx)),
          fetchPestRecords(parseInt(plantIdx)),
        ]);
        setLoading(false);
      };
      loadData();
    } else {
      setLoading(false);
    }
  }, [params.plantIdx]);

  // 3-5) Photo handlers (사진 변경)
  async function changePhoto() {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") {
      Alert.alert("권한 필요", "앨범 접근 권한을 허용해주세요.");
      return;
    }
    setBusy(true);
    try {
      const res = await ImagePicker.launchImageLibraryAsync({
        allowsEditing: true,
        quality: 0.9,
        mediaTypes: ["images"], // ✅ 최신 enum
        aspect: [1, 1],
      });
      if (!res.canceled && res.assets?.[0]?.uri) {
        setImageUri(res.assets[0].uri);
      }
    } finally {
      setBusy(false);
    }
  }

  // 3-6) Delete / Edit / Back
  const deletePlant = async (plantIdx: number) => {
    try {
      const token = await getToken();
      if (!token) {
        Alert.alert("오류", "로그인이 필요합니다.");
        return;
      }

      const url = await getApiUrl(API_ENDPOINTS.PLANTS.DELETE(plantIdx));
      const response = await fetch(url, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.status === 401) {
        const refreshed = await refreshToken();
        if (refreshed) {
          return deletePlant(plantIdx);
        } else {
          Alert.alert("오류", "로그인이 만료되었습니다.");
          return;
        }
      }

      if (response.ok) {
        Alert.alert("삭제 완료", "식물이 삭제되었습니다.");
        router.back();
      } else {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error("식물 삭제 실패:", error);
      Alert.alert("오류", "식물 삭제에 실패했습니다.");
    }
  };

  function onDelete() {
    if (!plantDetail) return;

    Alert.alert("삭제 확인", "정말 이 식물을 삭제할까요?", [
      { text: "취소", style: "cancel" },
      {
        text: "삭제",
        style: "destructive",
        onPress: () => deletePlant(plantDetail.idx),
      },
    ]);
  }

  function goEdit() {
    if (!plantDetail) return;

    const href: Href = {
      pathname: "/(page)/(stackless)/plant-new" as const,
      params: {
        plantIdx: String(plantDetail.idx),
        plantName: plantDetail.plant_name,
        species: plantDetail.species || "",
        meetDay: plantDetail.meet_day || "",
      },
    };
    router.push(href);
  }

  // 3-7) ✨ 기록/일기 페이지로 이동
  function goPestNew() {
    if (!plantDetail) return;

    const href: Href = {
      pathname: "/(page)/medical" as const,
      params: {
        plantIdx: String(plantDetail.idx),
        plantName: plantDetail.plant_name,
        species: plantDetail.species || "",
      },
    };
    router.push(href);
  }

  function goDiaryNew() {
    if (!plantDetail) return;

    const href: Href = {
      pathname: "/(page)/diary" as const,
      params: {
        plantIdx: String(plantDetail.idx),
        plantName: plantDetail.plant_name,
        species: plantDetail.species || "",
      },
    };
    router.push(href);
  }

  // 3-8) Render
  if (loading) {
    return (
      <View
        style={[
          styles.container,
          styles.centerContent,
          { backgroundColor: theme.bg },
        ]}
      >
        <ActivityIndicator size="large" color={theme.primary} />
        <Text style={[styles.loadingText, { color: theme.text }]}>
          식물 정보를 불러오는 중...
        </Text>
      </View>
    );
  }

  if (!plantDetail) {
    return (
      <View
        style={[
          styles.container,
          styles.centerContent,
          { backgroundColor: theme.bg },
        ]}
      >
        <Text style={[styles.errorText, { color: theme.text }]}>
          식물 정보를 찾을 수 없습니다.
        </Text>
        <TouchableOpacity
          style={[styles.backBtn, { backgroundColor: theme.primary }]}
          onPress={() => router.back()}
        >
          <Text style={styles.backBtnText}>뒤로가기</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      <ScrollView contentContainerStyle={{ paddingBottom: 140 }}>
        {/* 사진 섹션 */}
        <View style={styles.photoBox}>
          <Pressable
            onPress={changePhoto}
            disabled={busy}
            style={[
              styles.photoPlaceholder,
              { borderColor: theme.border, backgroundColor: theme.graybg },
            ]}
          >
            {plantDetail.user_plant_image ? (
              <>
                <Image
                  source={{ uri: plantDetail.user_plant_image }}
                  style={styles.photo}
                  resizeMode="cover"
                />
                <View
                  style={[
                    styles.changeBadge,
                    {
                      borderColor: theme.border,
                      backgroundColor: theme.bg + "cc",
                    },
                  ]}
                >
                  <Text style={[styles.changeBadgeText, { color: theme.text }]}>
                    사진 변경
                  </Text>
                </View>
              </>
            ) : (
              <>
                <Text style={{ color: theme.text, fontSize: 40 }}>+</Text>
                <Text style={{ color: theme.text, marginTop: 4 }}>
                  사진을 등록하세요
                </Text>
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
          <Text style={[styles.cardTitle, { color: theme.text }]}>
            기본 정보
          </Text>
          <View style={styles.rowBetween}>
            <Text style={[styles.kvKey, { color: theme.text }]}>별명</Text>
            <Text style={[styles.kvVal, { color: theme.text }]}>
              {plantDetail.plant_name || "-"}
            </Text>
          </View>
          <View style={styles.rowBetween}>
            <Text style={[styles.kvKey, { color: theme.text }]}>품종</Text>
            <Text style={[styles.kvVal, { color: theme.text }]}>
              {plantDetail.species || "-"}
            </Text>
          </View>
          <View style={styles.rowBetween}>
            <Text style={[styles.kvKey, { color: theme.text }]}>
              키우기 시작한 날
            </Text>
            <Text style={[styles.kvVal, { color: theme.text }]}>
              {plantDetail.meet_day
                ? new Date(plantDetail.meet_day).toLocaleDateString()
                : "-"}
            </Text>
          </View>
          {plantDetail.current_humidity && (
            <View style={styles.rowBetween}>
              <Text style={[styles.kvKey, { color: theme.text }]}>
                현재 습도
              </Text>
              <Text style={[styles.kvVal, { color: theme.text }]}>
                {plantDetail.current_humidity}%
              </Text>
            </View>
          )}
          {plantDetail.growing_location && (
            <View style={styles.rowBetween}>
              <Text style={[styles.kvKey, { color: theme.text }]}>
                키우는 장소
              </Text>
              <Text style={[styles.kvVal, { color: theme.text }]}>
                {plantDetail.growing_location}
              </Text>
            </View>
          )}
        </View>

        {/* 병충해 기록 (보기 전용 / 작성은 페이지 이동) */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={[styles.cardTitle, { color: theme.text }]}>
              병충해 기록
            </Text>
            <TouchableOpacity
              style={[styles.smallBtn, { backgroundColor: theme.primary }]}
              onPress={goPestNew}
            >
              <Text style={styles.smallBtnText}>기록 추가</Text>
            </TouchableOpacity>
          </View>
          {pestRecords.length === 0 ? (
            <Text style={{ color: "#888" }}>기록이 없어요.</Text>
          ) : (
            pestRecords.map((record) => (
              <View key={record.idx} style={styles.listRow}>
                <Text style={[styles.listDate, { color: theme.text }]}>
                  {new Date(record.created_at).toLocaleDateString()}
                </Text>
                <View style={styles.listContent}>
                  <Text style={[styles.listText, { color: theme.text }]}>
                    {record.pest_name}
                  </Text>
                  <Text style={[styles.listSubText, { color: theme.text }]}>
                    심각도: {record.severity}
                  </Text>
                  {record.notes && (
                    <Text style={[styles.listSubText, { color: theme.text }]}>
                      {record.notes}
                    </Text>
                  )}
                </View>
              </View>
            ))
          )}
        </View>

        {/* 일기 목록 (보기 전용 / 작성은 페이지 이동) */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={[styles.cardTitle, { color: theme.text }]}>
              일기 목록
            </Text>
            <TouchableOpacity
              style={[styles.smallBtn, { backgroundColor: theme.primary }]}
              onPress={goDiaryNew}
            >
              <Text style={styles.smallBtnText}>일기 작성</Text>
            </TouchableOpacity>
          </View>
          {diaryRecords.length === 0 ? (
            <Text style={{ color: "#888" }}>작성한 일기가 없어요.</Text>
          ) : (
            diaryRecords.map((record) => (
              <View key={record.idx} style={styles.listRow}>
                <Text style={[styles.listDate, { color: theme.text }]}>
                  {new Date(record.created_at).toLocaleDateString()}
                </Text>
                <View style={styles.listContent}>
                  <Text style={[styles.listText, { color: theme.text }]}>
                    {record.content}
                  </Text>
                  {record.image_url && (
                    <Image
                      source={{ uri: record.image_url }}
                      style={styles.diaryImage}
                    />
                  )}
                </View>
              </View>
            ))
          )}
        </View>

        {/* 내 식물 품종 정보 */}
        <View style={styles.card}>
          <Text style={[styles.cardTitle, { color: theme.text }]}>
            내 식물 품종 정보
          </Text>
          {plantDetail.feature && (
            <View style={styles.rowBetween}>
              <Text style={[styles.kvKey, { color: theme.text }]}>특징</Text>
              <Text style={[styles.kvVal, { color: theme.text }]}>
                {plantDetail.feature}
              </Text>
            </View>
          )}
          {plantDetail.temp && (
            <View style={styles.rowBetween}>
              <Text style={[styles.kvKey, { color: theme.text }]}>
                적정 온도
              </Text>
              <Text style={[styles.kvVal, { color: theme.text }]}>
                {plantDetail.temp}
              </Text>
            </View>
          )}
          {plantDetail.watering && (
            <View style={styles.rowBetween}>
              <Text style={[styles.kvKey, { color: theme.text }]}>물주기</Text>
              <Text style={[styles.kvVal, { color: theme.text }]}>
                {plantDetail.watering}
              </Text>
            </View>
          )}
          {plantDetail.fertilizer && (
            <View style={styles.rowBetween}>
              <Text style={[styles.kvKey, { color: theme.text }]}>비료</Text>
              <Text style={[styles.kvVal, { color: theme.text }]}>
                {plantDetail.fertilizer}
              </Text>
            </View>
          )}
          {plantDetail.toxic && (
            <View style={styles.rowBetween}>
              <Text style={[styles.kvKey, { color: theme.text }]}>독성</Text>
              <Text style={[styles.kvVal, { color: theme.text }]}>
                {plantDetail.toxic}
              </Text>
            </View>
          )}
        </View>
      </ScrollView>

      {/* 하단 고정 버튼들 */}
      <View style={[styles.bottomBar, { backgroundColor: theme.bg }]}>
        <TouchableOpacity
          style={[
            styles.bottomBtn,
            styles.outlineBtn,
            { borderColor: theme.border },
          ]}
          onPress={() => router.back()}
        >
          <Text style={[styles.bottomBtnText, { color: theme.text }]}>
            뒤로가기
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.bottomBtn, { backgroundColor: "#d32f2f" }]}
          onPress={onDelete}
        >
          <Text style={styles.bottomBtnText}>식물 삭제</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.bottomBtn, { backgroundColor: theme.primary }]}
          onPress={goEdit}
        >
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
  centerContent: { alignItems: "center", justifyContent: "center" },
  loadingText: { marginTop: 16, fontSize: 16 },
  errorText: { fontSize: 16, marginBottom: 16 },
  backBtn: { paddingHorizontal: 24, paddingVertical: 12, borderRadius: 8 },
  backBtnText: { color: "#fff", fontWeight: "700" },

  // Photo
  photoBox: { alignItems: "center", position: "relative", height: 260 },
  photo: {
    position: "absolute",
    left: 0,
    top: 0,
    width: "100%",
    height: 260,
    resizeMode: "cover",
  },
  photoPlaceholder: {
    width: "100%",
    height: 260,
    alignItems: "center",
    justifyContent: "center",
  },
  changeBadge: {
    position: "absolute",
    right: 24,
    bottom: 10,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  changeBadgeText: { fontSize: 12, fontWeight: "700" },

  busyOverlay: {
    position: "absolute",
    left: 24,
    right: 24,
    top: 0,
    bottom: 0,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(0,0,0,0.08)",
    borderRadius: 12,
  },

  // Cards
  card: {
    marginTop: 16,
    marginHorizontal: 24,
    borderWidth: 1,
    borderColor: "#e0e0e0",
    borderRadius: 12,
    padding: 14,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 6,
  },
  cardTitle: { fontSize: 16, fontWeight: "800", marginBottom: 8 },

  // Rows & K/V
  row: { flexDirection: "row", alignItems: "center", gap: 8 },
  rowBetween: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: 8,
  },
  kvKey: { fontSize: 14, fontWeight: "600" },
  kvVal: { fontSize: 14, fontWeight: "500" },

  // Inputs & small controls
  input: {
    height: 50,
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  inputSmall: { width: 80 },
  unit: { fontSize: 14 },

  smallBtn: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8 },
  smallBtnText: { color: "#fff", fontWeight: "700" },

  // Lists
  listRow: { flexDirection: "row", gap: 10, paddingVertical: 6 },
  listDate: { fontSize: 12, opacity: 0.8, width: 84 },
  listContent: { flex: 1 },
  listText: { fontSize: 14, marginBottom: 2 },
  listSubText: { fontSize: 12, opacity: 0.7 },
  diaryImage: { width: 60, height: 60, borderRadius: 8, marginTop: 4 },

  // Bottom bar
  bottomBar: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    flexDirection: "row",
    gap: 8,
    padding: 12,
  },
  bottomBtn: {
    flex: 1,
    height: 48,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  outlineBtn: { borderWidth: 1 },
  bottomBtnText: { color: "#fff", fontSize: 15, fontWeight: "700" },
});
