// app/(page)/(stackless)/plant-new.tsx
// ─────────────────────────────────────────────────────────────────────────────
// ① Imports
// ─────────────────────────────────────────────────────────────────────────────
import React, { useMemo, useState, useRef, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  Pressable,
  Image,
  Alert,
  ActivityIndicator,
  Platform,
  Dimensions,
  KeyboardAvoidingView,
  Keyboard,
  StatusBar,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useRouter } from "expo-router";
import { useColorScheme } from "react-native";
import Colors from "../../../constants/Colors";
import { getApiUrl } from "../../../config/api";
import { getToken, refreshToken } from "../../../libs/auth";

// 공통 모달
import ClassifierResultModal, {
  ClassifyResult,
} from "../../../components/common/ClassifierResultModal";

type IndoorOutdoor = "indoor" | "outdoor" | null;

const SPECIES = [
  "몬스테라",
  "스투키",
  "금전수",
  "선인장",
  "호접란",
  "테이블야자",
  "홍콩야자",
  "스파티필럼",
  "관음죽",
  "벵갈고무나무",
  "올리브나무",
  "디펜바키아",
  "보스턴고사리",
] as const;

// 백엔드를 통한 품종 분류 API 호출
async function classifySpecies(imageUri: string): Promise<ClassifyResult> {
  try {
    const token = await getToken();
    console.log("🔑 토큰 상태:", token ? "존재함" : "없음");
    console.log("🔑 토큰 길이:", token ? token.length : 0);

    if (!token) {
      throw new Error("로그인이 필요합니다.");
    }

    // FormData 생성
    const formData = new FormData();
    formData.append("image", {
      uri: imageUri,
      type: "image/jpeg",
      name: "plant.jpg",
    } as any);

    // 백엔드 API 호출 (백엔드가 모델서버로 전달)
    const apiUrl = await getApiUrl("/plants/classify-species");
    console.log("🌐 API URL:", apiUrl);

    const response = await fetch(apiUrl, {
      method: "POST",
      body: formData,
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "multipart/form-data",
      },
    });

    console.log("📡 응답 상태:", response.status);

    if (!response.ok) {
      // 401 에러인 경우 토큰 갱신 시도
      if (response.status === 401) {
        console.log("🔄 401 에러 - 토큰 갱신 시도");
        const newToken = await refreshToken();
        if (newToken) {
          console.log("🔄 토큰 갱신 성공 - 재시도");
          // 갱신된 토큰으로 재시도
          const retryResponse = await fetch(apiUrl, {
            method: "POST",
            body: formData,
            headers: {
              Authorization: `Bearer ${newToken}`,
              "Content-Type": "multipart/form-data",
            },
          });

          if (retryResponse.ok) {
            const result = await retryResponse.json();
            if (result.success && result.species) {
              return {
                species: result.species_korean || result.species, // 한글명 우선 사용
                confidence: Math.round(result.confidence * 100),
              };
            } else {
              throw new Error(result.message || "분류에 실패했습니다.");
            }
          }
        }
      }

      const errorData = await response.json().catch(() => ({}));
      console.log("❌ 에러 응답:", errorData);
      throw new Error(errorData.detail || `분류 실패: ${response.status}`);
    }

    const result = await response.json();

    if (result.success && result.species) {
      return {
        species: result.species_korean || result.species, // 한글명 우선 사용
        confidence: Math.round(result.confidence * 100),
      };
    } else {
      throw new Error(result.message || "분류에 실패했습니다.");
    }
  } catch (error) {
    console.error("품종 분류 오류:", error);
    // 오류 시 기본값 반환
    return {
      species: "알 수 없음",
      confidence: 0,
    };
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// ③ Component
// ─────────────────────────────────────────────────────────────────────────────
export default function PlantNew() {
  // Theme & Router
  const router = useRouter();
  const scheme = useColorScheme();
  const theme = Colors[scheme === "dark" ? "dark" : "light"];

  // 상단 오프셋 (SafeAreaProvider 없이)
  const topOffset =
    Platform.OS === "android" ? StatusBar.currentHeight ?? 0 : 0;

  // Form states
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [species, setSpecies] = useState<string>("");
  const [nickname, setNickname] = useState<string>("");
  const [startedAt, setStartedAt] = useState<string>("");

  // UI states
  const [busy, setBusy] = useState(false);
  const [resultVisible, setResultVisible] = useState(false);
  const [result, setResult] = useState<ClassifyResult | null>(null);

  // Scroll helpers
  const scrollRef = useRef<ScrollView>(null);
  const fieldY = useRef<Record<string, number>>({});
  function onFieldLayout(key: string, y: number) {
    fieldY.current[key] = y;
  }
  function scrollToField(key: string, inputHeight = 56) {
    const y = fieldY.current[key] ?? 0;
    const screenH = Dimensions.get("window").height;
    const targetY = Math.max(0, y - screenH / 3 + inputHeight / 2);
    scrollRef.current?.scrollTo({ y: targetY, animated: true });
  }

  // Validation
  const isKnownSpecies = useMemo(
    () => (species ? (SPECIES as readonly string[]).includes(species) : true),
    [species]
  );
  const isAllFilled = Boolean(
    imageUri && species.trim() && nickname.trim() && startedAt.trim()
  );
  const isDateLike = useMemo(
    () => !startedAt || /^\d{4}-\d{2}-\d{2}$/.test(startedAt),
    [startedAt]
  );

  // Utils
  function formatDateInput(text: string): string {
    const digits = text.replace(/\D/g, "").slice(0, 8);
    if (digits.length <= 4) return digits;
    if (digits.length <= 6) return `${digits.slice(0, 4)}-${digits.slice(4)}`;
    return `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6, 8)}`;
  }

  // Image pick
  function handlePickImage() {
    if (Platform.OS === "web") return void pickFromLibrary();
    Alert.alert("사진 등록", "사진을 불러올 방법을 선택하세요.", [
      { text: "사진 찍기", onPress: takePhoto },
      { text: "앨범 선택", onPress: pickFromLibrary },
      { text: "취소", style: "cancel" },
    ]);
  }
  async function pickFromLibrary() {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted")
      return Alert.alert("권한 필요", "앨범 접근 권한을 허용해주세요.");
    setBusy(true);
    try {
      const res = await ImagePicker.launchImageLibraryAsync({
        allowsEditing: true,
        quality: 0.9,
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        aspect: [1, 1],
      });
      if (!res.canceled && res.assets?.[0]?.uri) {
        setImageUri(res.assets[0].uri);
        // 실제 모델 서버 API 호출
        const r = await classifySpecies(res.assets[0].uri);
        setResult(r);
        // 분류 결과를 품종 입력 필드에 자동으로 채우기
        if (r.species && r.species !== "알 수 없음") {
          setSpecies(r.species);
        }
        setTimeout(() => setResultVisible(true), 80);
      }
    } finally {
      setBusy(false);
    }
  }
  async function takePhoto() {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== "granted")
      return Alert.alert("권한 필요", "카메라 권한을 허용해주세요.");
    setBusy(true);
    try {
      const res = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        quality: 0.9,
        aspect: [1, 1],
      });
      if (!res.canceled && res.assets?.[0]?.uri) {
        setImageUri(res.assets[0].uri);
        // 실제 모델 서버 API 호출
        const r = await classifySpecies(res.assets[0].uri);
        setResult(r);
        // 분류 결과를 품종 입력 필드에 자동으로 채우기
        if (r.species && r.species !== "알 수 없음") {
          setSpecies(r.species);
        }
        setTimeout(() => setResultVisible(true), 80);
      }
    } finally {
      setBusy(false);
    }
  }

  // Submit
  async function handleSubmit() {
    if (!isAllFilled) return;
    if (!isDateLike)
      return Alert.alert(
        "날짜 형식 확인",
        "날짜는 YYYY-MM-DD 형식으로 입력해주세요."
      );

    Keyboard.dismiss();
    setBusy(true);

    try {
      const token = await getToken();
      if (!token) {
        Alert.alert("오류", "로그인이 필요합니다.");
        return;
      }

      // FormData 생성
      const formData = new FormData();
      formData.append("plant_name", nickname);
      formData.append("meet_day", startedAt);

      // 품종이 있으면 추가 (이미지가 없거나 수동 입력한 경우)
      if (species.trim()) {
        formData.append("species", species);
      }

      // 이미지가 있으면 추가 (백엔드에서 자동으로 품종 분류 수행)
      if (imageUri) {
        formData.append("image", {
          uri: imageUri,
          type: "image/jpeg",
          name: "plant.jpg",
        } as any);
      }

      // 백엔드 API 호출
      const apiUrl = await getApiUrl("/plants");
      const response = await fetch(apiUrl, {
        method: "POST",
        body: formData,
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data",
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `등록 실패: ${response.status}`);
      }

      const result = await response.json();

      Alert.alert("등록 완료", "새 식물이 성공적으로 등록되었습니다!", [
        { text: "확인", onPress: () => router.replace("/(page)/home") },
      ]);
    } catch (error) {
      console.error("식물 등록 오류:", error);
      Alert.alert(
        "등록 실패",
        error instanceof Error
          ? error.message
          : "식물 등록 중 오류가 발생했습니다."
      );
    } finally {
      setBusy(false);
    }
  }

  // Render
  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: theme.bg }}
      behavior={Platform.select({ ios: "padding", android: "height" })} // ← 동일화
      keyboardVerticalOffset={topOffset}
    >
      <ScrollView
        ref={scrollRef}
        keyboardDismissMode={Platform.select({
          ios: "interactive",
          android: "none",
        })} // ← 스치면 내려가지 않게
        keyboardShouldPersistTaps="handled" // ← 인풋 터치 유지
      >
        {/* 사진 */}
        <View style={styles.photoBox}>
          <Pressable
            onPress={handlePickImage}
            disabled={busy}
            onStartShouldSetResponder={() => false}
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
                  키우는 식물을 자랑해주세요!
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

        {/* 입력들 */}
        <View style={styles.inputArea}>
          {/* 품종 분류 */}
          <View
            style={styles.field}
            onLayout={(e) => onFieldLayout("species", e.nativeEvent.layout.y)}
          >
            <Text style={[styles.sectionLabel, { color: theme.text }]}>
              품종 분류
            </Text>
            <TextInput
              placeholder="직접입력 (예: 몬스테라)"
              placeholderTextColor="#909090"
              value={species}
              onChangeText={setSpecies}
              onFocus={() => scrollToField("species")}
              style={[
                styles.input,
                { color: theme.text, borderColor: theme.border },
              ]}
            />
            <Text style={[styles.notice, { color: theme.text }]}>
              * 직접입력 시 올바른 품종정보나 생육정보의 제공이 어려울 수
              있습니다.
            </Text>
            {species.trim().length > 0 && !isKnownSpecies && (
              <Text style={styles.warn}>
                * 데이터 베이스에 없는 식물입니다. 식물주님의 품종을 학습하여
                조만간 업데이트 하겠습니다.
              </Text>
            )}
          </View>

          {/* 별명 */}
          <View
            style={styles.field}
            onLayout={(e) => onFieldLayout("nickname", e.nativeEvent.layout.y)}
          >
            <Text style={[styles.sectionLabel, { color: theme.text }]}>
              내 식물 별명
            </Text>
            <TextInput
              placeholder="예: 몬몬이"
              placeholderTextColor="#909090"
              value={nickname}
              onChangeText={setNickname}
              onFocus={() => scrollToField("nickname")}
              style={[
                styles.input,
                { color: theme.text, borderColor: theme.border },
              ]}
            />
          </View>

          {/* 키우기 시작한 날 */}
          <View
            style={styles.field}
            onLayout={(e) => onFieldLayout("startedAt", e.nativeEvent.layout.y)}
          >
            <Text style={[styles.sectionLabel, { color: theme.text }]}>
              키우기 시작한 날
            </Text>
            <TextInput
              placeholder="YYYY-MM-DD"
              placeholderTextColor="#909090"
              value={startedAt}
              onChangeText={(text) => setStartedAt(formatDateInput(text))}
              onFocus={() => scrollToField("startedAt")}
              keyboardType="number-pad"
              maxLength={10}
              style={[
                styles.input,
                { color: theme.text, borderColor: theme.border },
              ]}
            />
            {startedAt.length > 0 && !isDateLike && (
              <Text style={styles.warn}>YYYY-MM-DD 형식으로 입력해주세요.</Text>
            )}
          </View>

          {/* 하단 고정 버튼 (키보드 높이만큼 자동 상승) */}
          <View style={styles.bottomBar}>
            <Pressable
              onPress={() => {
                Keyboard.dismiss();
                router.replace("/(page)/home");
              }}
              style={[styles.cancelBtn, { borderColor: theme.border }]}
            >
              <Text style={[styles.cancelText, { color: theme.text }]}>
                취소
              </Text>
            </Pressable>
            <Pressable
              disabled={!isAllFilled || !isDateLike || busy}
              onPress={handleSubmit}
              style={[
                styles.submitBtn,
                {
                  backgroundColor:
                    !isAllFilled || !isDateLike || busy
                      ? theme.graybg
                      : theme.primary,
                },
              ]}
            >
              {busy ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <Text style={[styles.submitText, { color: "#fff" }]}>
                  등록하기
                </Text>
              )}
            </Pressable>
          </View>
        </View>
      </ScrollView>

      {/* 공통 Result Modal */}
      <ClassifierResultModal
        visible={resultVisible}
        theme={theme}
        result={result}
        onClose={() => setResultVisible(false)}
        onRetake={handlePickImage}
      />
    </KeyboardAvoidingView>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ④ Styles
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1 },

  sectionLabel: { fontSize: 16, fontWeight: "700", marginBottom: 8 },
  helper: { fontSize: 12, marginBottom: 8, opacity: 0.8 },

  photoBox: {
    alignItems: "center",
    position: "relative",
    height: 260,
    marginTop: 12,
  },
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

  busyOverlay: {
    position: "absolute",
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(0,0,0,0.08)",
    borderRadius: 12,
  },

  inputArea: { paddingHorizontal: 24 },
  field: { marginTop: 24 },
  input: {
    height: 50,
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 12,
  },
  notice: { fontSize: 12, marginTop: 6 },
  warn: { fontSize: 12, marginTop: 6, color: "#d93025" },
  bottomBar: {
    flexDirection: "row",
    gap: 8,
    alignItems: "center",
    marginTop: 40,
  },

  cancelBtn: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 14,
  },
  cancelText: { fontSize: 15, fontWeight: "600" },
  submitBtn: {
    flex: 2,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 14,
  },
  submitText: { fontWeight: "700", fontSize: 16 },

  changeBadge: {
    position: "absolute",
    right: 10,
    bottom: 10,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  changeBadgeText: { fontSize: 12, fontWeight: "700" },
});
