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
import { useLocalSearchParams, useFocusEffect } from "expo-router";
import { useRouter, type Href } from "expo-router";
import * as ImagePicker from "expo-image-picker";
import { useColorScheme } from "react-native";
import Colors from "../../../constants/Colors";
import { getApiUrl } from "../../../config/api";
import { getToken } from "../../../libs/auth";
import { API_ENDPOINTS } from "../../../config/api";

// ─────────────────────────────────────────────────────────────────────────────
// ② Types & Constants
// ─────────────────────────────────────────────────────────────────────────────
type PestLog = { id: string; note: string; createdAt: string };
type DiaryLog = { id: string; text: string; createdAt: string };
type WaterLog = { id: string; reason: string; createdAt: string };

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
    id?: string;
    imageUri?: string;
    nickname?: string;
    species?: string;
    startedAt?: string;
    plantId?: string;
  }>();

  // 3-2) Local States
  const [imageUri, setImageUri] = useState<string | null>(
    params.imageUri ?? null
  );
  const [nickname, setNickname] = useState<string>(params.nickname ?? "");
  const [species, setSpecies] = useState<string>(params.species ?? "");
  const [startedAt, setStartedAt] = useState<string>(params.startedAt ?? "");
  const [health, setHealth] = useState<string>("좋음"); // 기본값
  const [pestLogs] = useState<PestLog[]>([]); // ✨ 작성은 별도 페이지에서
  const [diaryLogs] = useState<DiaryLog[]>([]); // ✨ 작성은 별도 페이지에서
  const [waterLogs, setWaterLogs] = useState<WaterLog[]>([]);
  const [busy, setBusy] = useState(false);
  const [wikiInfo, setWikiInfo] = useState<any>(null);
  const [loadingWiki, setLoadingWiki] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // 컴포넌트 마운트 시 위키 정보 가져오기
  useEffect(() => {
    fetchWikiInfo();
  }, [params.id]); // params.id가 변경될 때마다 실행

  // 페이지가 포커스될 때마다 상태 초기화 (React Navigation 캐싱 문제 해결)
  useFocusEffect(
    React.useCallback(() => {
      // 편집 모드 해제
      setIsEditing(false);
      setIsSaving(false);
      setLoadingWiki(false);

      // params에서 받은 값으로 상태 초기화
      setImageUri(params.imageUri ?? null);
      setNickname(params.nickname ?? "");
      setSpecies(params.species ?? "");
      setStartedAt(params.startedAt ?? "");

      // 위키 정보 새로고침
      fetchWikiInfo();
    }, [
      params.id,
      params.imageUri,
      params.nickname,
      params.species,
      params.startedAt,
    ])
  );

  // 위키 정보 가져오기
  async function fetchWikiInfo() {
    const plantId = params.id || params.plantId;
    if (!plantId) return;

    try {
      setLoadingWiki(true);
      const token = await getToken();
      const apiUrl = getApiUrl(`/plants/${plantId}/wiki-info`);

      const response = await fetch(apiUrl, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setWikiInfo(data.wiki_info);
      }
    } catch (error) {
      console.error("위키 정보 조회 오류:", error);
    } finally {
      setLoadingWiki(false);
    }
  }

  // 3-3) Photo handlers (사진 변경 + 품종 재분류)
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

        // 품종 재분류 실행
        await classifySpecies(res.assets[0].uri);
      }
    } finally {
      setBusy(false);
    }
  }

  // 품종 분류 함수
  async function classifySpecies(imageUri: string) {
    try {
      setBusy(true);

      const token = await getToken();
      if (!token) {
        Alert.alert("오류", "로그인이 필요합니다.");
        return;
      }

      // FormData 생성 (React Native 방식)
      const formData = new FormData();
      formData.append("image", {
        uri: imageUri,
        type: "image/jpeg",
        name: "plant_image.jpg",
      } as any);

      // 품종 분류 API 호출 (Content-Type 헤더 제거 - 브라우저가 자동 설정)
      const apiUrl = getApiUrl("/plants/classify-species");
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          // Content-Type 헤더 제거 - FormData 사용 시 브라우저가 자동으로 multipart/form-data 설정
        },
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success && result.species) {
          // 한글 품종명이 있으면 사용, 없으면 영어 품종명 사용
          const displaySpecies = result.species_korean || result.species;
          setSpecies(displaySpecies);
          Alert.alert(
            "품종 재분류 완료",
            `새로운 품종: ${displaySpecies}\n신뢰도: ${Math.round(
              (result.confidence || 0) * 100
            )}%`
          );
        } else {
          Alert.alert("품종 분류 실패", "품종을 분류할 수 없습니다.");
        }
      } else {
        throw new Error(`품종 분류 실패: ${response.status}`);
      }
    } catch (error) {
      console.error("품종 분류 오류:", error);
      // 품종 분류 실패해도 계속 진행 (사용자에게 알림만 표시)
      Alert.alert(
        "품종 분류 실패",
        "품종 분류 중 문제가 발생했습니다.\n기존 품종 정보를 유지합니다.",
        [{ text: "확인" }]
      );
    } finally {
      setBusy(false);
    }
  }

  // 3-4) “습도계 지수 n% 증가 시 물준날로 기록?”
  const [humidityRise, setHumidityRise] = useState<string>("10");
  function markWateringByHumidity() {
    const n = Number(humidityRise);
    if (Number.isNaN(n) || n <= 0) {
      Alert.alert("값 확인", "증가 퍼센트를 숫자로 입력해주세요.");
      return;
    }
    setWaterLogs((prev) => [
      {
        id: String(Date.now()),
        reason: `습도 +${n}%`,
        createdAt: fmtDate(new Date()),
      },
      ...prev,
    ]);
    Alert.alert("기록 완료", `습도 ${n}% 증가로 물 준 날을 기록했어요.`);
  }

  // 3-5) Delete / Edit / Back
  async function onDelete() {
    Alert.alert(
      "식물 삭제",
      `${nickname || "이 식물"}과의 모든 추억을 삭제하시겠습니까?`,
      [
        { text: "취소", style: "cancel" },
        {
          text: "삭제하기",
          style: "destructive",
          onPress: () => {
            // 2단계 확인
            Alert.alert(
              "정말 삭제하시겠습니까?",
              "삭제 시 다음 데이터가 모두 사라집니다:\n• 식물 기본 정보\n• 관련 일기\n• 관련 이미지\n• 진단 기록\n\n삭제된 데이터는 복구할 수 없습니다.",
              [
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
                        Alert.alert("오류", "로그인이 필요합니다.");
                        return;
                      }

                      // API URL 생성 (plantId 사용)
                      const plantId = params.id || params.plantId;
                      const apiUrl = getApiUrl(
                        API_ENDPOINTS.PLANTS.DELETE(Number(plantId))
                      );

                      // 삭제 요청
                      const response = await fetch(apiUrl, {
                        method: "DELETE",
                        headers: {
                          Authorization: `Bearer ${token}`,
                          "Content-Type": "application/json",
                        },
                      });

                      if (!response.ok) {
                        const errorData = await response
                          .json()
                          .catch(() => ({}));
                        throw new Error(
                          errorData.detail ||
                            `HTTP error! status: ${response.status}`
                        );
                      }

                      const result = await response.json();
                      Alert.alert(
                        "삭제 완료",
                        "식물과 관련된 모든 데이터가 성공적으로 삭제되었습니다.",
                        [
                          {
                            text: "확인",
                            onPress: () => router.push("/(page)/home"),
                          },
                        ]
                      );
                    } catch (error) {
                      console.error("식물 삭제 실패:", error);
                      Alert.alert(
                        "삭제 실패",
                        error instanceof Error
                          ? error.message
                          : "식물 삭제 중 오류가 발생했습니다."
                      );
                    } finally {
                      setBusy(false);
                    }
                  },
                },
              ]
            );
          },
        },
      ]
    );
  }

  // 수정 모드 토글
  function toggleEdit() {
    setIsEditing(!isEditing);
  }

  // 저장 기능
  async function saveChanges() {
    const plantId = params.id || params.plantId;
    if (!plantId) {
      Alert.alert("오류", "식물 ID가 없습니다.");
      return;
    }

    setIsSaving(true);
    try {
      const token = await getToken();
      if (!token) {
        Alert.alert("오류", "로그인이 필요합니다.");
        return;
      }

      // FormData 생성
      const formData = new FormData();
      formData.append("plant_name", nickname);
      formData.append("species", species);

      // 이미지가 변경되었으면 추가
      if (imageUri && imageUri.startsWith("file://")) {
        formData.append("image", {
          uri: imageUri,
          type: "image/jpeg",
          name: "plant_image.jpg",
        } as any);
      }

      // API 호출
      const apiUrl = getApiUrl(API_ENDPOINTS.PLANTS.UPDATE(Number(plantId)));
      const response = await fetch(apiUrl, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        Alert.alert("저장 완료", "식물 정보가 성공적으로 업데이트되었습니다.");
        setIsEditing(false);
        // 홈페이지로 돌아가기
        router.push("/(page)/home");
      } else {
        throw new Error(`저장 실패: ${response.status}`);
      }
    } catch (error) {
      console.error("식물 정보 저장 오류:", error);
      Alert.alert("저장 실패", "식물 정보 저장 중 문제가 발생했습니다.");
    } finally {
      setIsSaving(false);
    }
  }

  // 3-6) ✨ 기록/일기 페이지로 이동
  function goPestNew() {
    const plantId = params.id || params.plantId;
    const href: Href = {
      pathname: "/(page)/medical" as const,
      params: { plantId: String(plantId ?? ""), nickname, species },
    };
    router.push(href);
  }

  function goDiaryNew() {
    const plantId = params.id || params.plantId;
    const href: Href = {
      pathname: "/(page)/diary" as const,
      params: { plantId: String(plantId ?? ""), nickname, species },
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
            style={[
              styles.photoPlaceholder,
              { borderColor: theme.border, backgroundColor: theme.graybg },
            ]}
          >
            {imageUri ? (
              <>
                <Image
                  source={{ uri: imageUri }}
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
            {isEditing ? (
              <TextInput
                value={nickname}
                onChangeText={setNickname}
                style={[
                  styles.input,
                  {
                    color: theme.text,
                    borderColor: theme.border,
                    backgroundColor: theme.bg,
                  },
                ]}
                placeholder={nickname || "식물 별명을 입력하세요"}
                placeholderTextColor="#888"
              />
            ) : (
              <Text style={[styles.kvVal, { color: theme.text }]}>
                {nickname || "-"}
              </Text>
            )}
          </View>
          <View style={styles.rowBetween}>
            <Text style={[styles.kvKey, { color: theme.text }]}>품종</Text>
            <Text style={[styles.kvVal, { color: theme.text }]}>
              {species || "-"}
            </Text>
          </View>
          <View style={styles.rowBetween}>
            <Text style={[styles.kvKey, { color: theme.text }]}>
              키우기 시작한 날
            </Text>
            <Text style={[styles.kvVal, { color: theme.text }]}>
              {startedAt || "-"}
            </Text>
          </View>
        </View>

        {/* 건강 상태 */}
        <View style={styles.card}>
          <Text style={[styles.cardTitle, { color: theme.text }]}>
            건강 상태
          </Text>
          <TextInput
            placeholder="예: 좋음 / 잎끝 마름 / 새잎 돋음 등"
            placeholderTextColor="#909090"
            readOnly={true}
            value={health}
            onChangeText={setHealth}
            style={[
              styles.input,
              { color: theme.text, borderColor: theme.border },
            ]}
          />
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
          {pestLogs.length === 0 ? (
            <Text style={{ color: "#888" }}>기록이 없어요.</Text>
          ) : (
            pestLogs.map((log) => (
              <View key={log.id} style={styles.listRow}>
                <Text style={[styles.listDate, { color: theme.text }]}>
                  {log.createdAt}
                </Text>
                <Text style={[styles.listText, { color: theme.text }]}>
                  {log.note}
                </Text>
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
          {diaryLogs.length === 0 ? (
            <Text style={{ color: "#888" }}>작성한 일기가 없어요.</Text>
          ) : (
            diaryLogs.map((log) => (
              <View key={log.id} style={styles.listRow}>
                <Text style={[styles.listDate, { color: theme.text }]}>
                  {log.createdAt}
                </Text>
                <Text style={[styles.listText, { color: theme.text }]}>
                  {log.text}
                </Text>
              </View>
            ))
          )}
        </View>

        {/* 내 식물 품종 정보 */}
        <View style={styles.card}>
          <Text style={[styles.cardTitle, { color: theme.text }]}>
            내 식물 품종 정보
          </Text>
          {loadingWiki ? (
            <Text style={{ color: "#888" }}>위키 정보를 불러오는 중...</Text>
          ) : wikiInfo ? (
            <View>
              <Text style={[styles.infoText, { color: theme.text }]}>
                <Text style={styles.infoLabel}>품종명: </Text>
                {wikiInfo.plant_name || wikiInfo.species || species}
              </Text>
              {wikiInfo.description && (
                <Text style={[styles.infoText, { color: theme.text }]}>
                  <Text style={styles.infoLabel}>설명: </Text>
                  {wikiInfo.description}
                </Text>
              )}
              {wikiInfo.care_tips && (
                <Text style={[styles.infoText, { color: theme.text }]}>
                  <Text style={styles.infoLabel}>관리 팁: </Text>
                  {wikiInfo.care_tips}
                </Text>
              )}
              {wikiInfo.watering_frequency && (
                <Text style={[styles.infoText, { color: theme.text }]}>
                  <Text style={styles.infoLabel}>물주기: </Text>
                  {wikiInfo.watering_frequency}
                </Text>
              )}
              {wikiInfo.light_requirement && (
                <Text style={[styles.infoText, { color: theme.text }]}>
                  <Text style={styles.infoLabel}>광량: </Text>
                  {wikiInfo.light_requirement}
                </Text>
              )}
            </View>
          ) : (
            <Text style={{ color: "#888" }}>
              해당 품종의 위키 정보를 찾을 수 없습니다.
            </Text>
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
          onPress={() => router.push("/(page)/home")}
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
        {isEditing ? (
          <TouchableOpacity
            style={[styles.bottomBtn, { backgroundColor: theme.primary }]}
            onPress={saveChanges}
            disabled={isSaving}
          >
            <Text style={styles.bottomBtnText}>
              {isSaving ? "저장 중..." : "저장하기"}
            </Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={[styles.bottomBtn, { backgroundColor: theme.primary }]}
            onPress={toggleEdit}
          >
            <Text style={styles.bottomBtnText}>수정하기</Text>
          </TouchableOpacity>
        )}
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
  listText: { flex: 1, fontSize: 14 },

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

  // 위키 정보 스타일
  infoText: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 8,
  },
  infoLabel: {
    fontWeight: "600",
    color: "#666",
  },
});
