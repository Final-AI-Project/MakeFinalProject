// app/(page)/(stackless)/camera.tsx
// ─────────────────────────────────────────────────────────────────────────────
// Expo Go에서 구동: 온디바이스 ONNX 제거, 서버(포트 4000) 추론 업로드 방식
// ─────────────────────────────────────────────────────────────────────────────

import React, { useState, useEffect, useRef, useMemo } from "react";
import {
  View,
  Text,
  StyleSheet,
  Image,
  useColorScheme,
  TouchableOpacity,
  ActivityIndicator,
  AccessibilityInfo,
  Alert,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  withSequence,
  Easing,
} from "react-native-reanimated";
import Colors from "../../constants/Colors";

// 결과 모달(프로젝트 컴포넌트 유지)
import ClassifierResultModal, {
  ClassifyResult,
} from "../../components/common/ClassifierResultModal";

// ─────────────────────────────────────────────────────────────────────────────
// 서버 분류 API (FastAPI/uvicorn이 4000번에서 동작 중)
// 필요 시 로컬 네트워크 IP로 교체
// ─────────────────────────────────────────────────────────────────────────────
const SERVER_IP = process.env.EXPO_PUBLIC_SERVER_IP as string;
const CLASSIFIER_URL = `${SERVER_IP}:4000/plants/classify-species`;

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────
type ModalMode = "result" | null;

// ─────────────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────────────
export default function CameraScreen() {
  const scheme = useColorScheme();
  const theme = useMemo(
    () => Colors[scheme === "dark" ? "dark" : "light"],
    [scheme]
  );

  const handY = useSharedValue(0);

  const [uri, setUri] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ClassifyResult | null>(null);
  const [modalMode, setModalMode] = useState<ModalMode>(null);

  const mountedRef = useRef(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // 작은 애니메이션(그대로 유지)
  useEffect(() => {
    handY.value = withRepeat(
      withSequence(
        withTiming(-2, { duration: 250, easing: Easing.inOut(Easing.quad) }),
        withTiming(0, { duration: 600, easing: Easing.inOut(Easing.quad) }),
        withTiming(0, { duration: 250, easing: Easing.inOut(Easing.quad) })
      ),
      -1,
      false
    );
  }, []);
  const handAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateY: handY.value }],
  }));

  // 최초 진입 시 카메라 자동 실행(접근성 ON이면 생략)
  const didAutoOpen = useRef(false);
  useEffect(() => {
    if (didAutoOpen.current) return;
    didAutoOpen.current = true;
    AccessibilityInfo.isScreenReaderEnabled().then((enabled) => {
      if (enabled) return;
      setTimeout(() => {
        askCamera().catch(() => {});
      }, 0);
    });
  }, []);

  // ─────────────────────────────────────────────────────────────────────────
  // 서버 추론: 파일 업로드 → species/confidence 수신
  // ─────────────────────────────────────────────────────────────────────────
  const runInference = async (pickedUri: string) => {
    setBusy(true);
    try {
      const form = new FormData();
      form.append(
        "image",
        {
          uri: pickedUri,
          type: "image/jpeg",
          name: pickedUri.split("/").pop() ?? "image.jpg",
        } as any
      );

      const res = await fetch(CLASSIFIER_URL, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();

      if (!data?.success || !data?.species) {
        throw new Error(data?.error || "분류 실패");
      }

      setResult({
        species: String(data.species),
        confidence: Math.round(Number(data.confidence) || 0),
      });
      setModalMode("result");
    } catch (e: any) {
      console.error("[infer] error:", e);
      Alert.alert("추론 실패", e?.message ?? "서버 요청 중 오류가 발생했습니다.");
    } finally {
      if (mountedRef.current) setBusy(false);
    }
  };

  // ─────────────────────────────────────────────────────────────────────────
  // Handlers
  // ─────────────────────────────────────────────────────────────────────────
  const handlePicked = async (pickedUri: string) => {
    if (!pickedUri) return;
    setUri(pickedUri);
    setResult(null);
    await runInference(pickedUri);
  };

  const askCamera = async () => {
    if (busy) return;
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== "granted") {
      return Alert.alert("권한 필요", "카메라 권한을 허용해주세요.");
    }
    try {
      const res = await ImagePicker.launchCameraAsync({
        quality: 0.9,
        exif: false,
        base64: false,
        allowsEditing: false,
      });
      if (!res.canceled) await handlePicked(res.assets[0].uri);
    } catch {}
  };

  const askGallery = async () => {
    if (busy) return;
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") {
      return Alert.alert("권한 필요", "갤러리 접근 권한을 허용해주세요.");
    }
    try {
      const res = await ImagePicker.launchImageLibraryAsync({
        quality: 0.9,
        exif: false,
        base64: false,
        allowsEditing: false,
      });
      if (!res.canceled) await handlePicked(res.assets[0].uri);
    } catch {}
  };

  const clearImage = () => {
    if (busy) return;
    setUri(null);
    setResult(null);
    setModalMode(null);
  };

  // ─────────────────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────────────────
  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      {/* Preview */}
      <View style={styles.previewWrap} accessibilityLabel="사진 미리보기 영역">
        {busy ? (
          <ActivityIndicator size="large" />
        ) : uri ? (
          <Image source={{ uri }} style={styles.preview} />
        ) : (
          <Text style={{ color: "#909090" }}>
            이미지를 선택하거나 촬영해 주세요.
          </Text>
        )}
      </View>

      {/* Controls */}
      <View style={styles.row}>
        <TouchableOpacity
          style={[
            styles.btn,
            { backgroundColor: theme.primary, opacity: busy ? 0.6 : 1 },
          ]}
          onPress={askCamera}
          activeOpacity={0.9}
          disabled={busy}
          accessibilityRole="button"
          accessibilityLabel="카메라 촬영"
        >
          <Text style={styles.btnText}>촬영</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.btn,
            { backgroundColor: "#5f6368", opacity: busy ? 0.6 : 1 },
          ]}
          onPress={askGallery}
          activeOpacity={0.9}
          disabled={busy}
          accessibilityRole="button"
          accessibilityLabel="갤러리에서 선택"
        >
          <Text style={styles.btnText}>갤러리</Text>
        </TouchableOpacity>

        {uri && (
          <TouchableOpacity
            style={[
              styles.btn,
              { backgroundColor: "#d32f2f", opacity: busy ? 0.6 : 1 },
            ]}
            onPress={clearImage}
            activeOpacity={0.9}
            disabled={busy}
            accessibilityRole="button"
            accessibilityLabel="초기화"
          >
            <Text style={styles.btnText}>↺ 초기화</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Result Modal */}
      <ClassifierResultModal
        visible={modalMode === "result"}
        theme={theme}
        result={result}
        onClose={() => setModalMode(null)}
        onRetake={askCamera}
      />

      {/* Decorative tiny bar */}
      <Animated.View style={[{ height: 2 }, handAnimatedStyle]} />
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Styles
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1, paddingHorizontal: 24, paddingBottom: 72 },

  // Controls
  row: { flexDirection: "row", gap: 8, marginTop: 12 },
  btn: {
    flex: 1,
    height: 44,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  btnText: { color: "#fff", fontSize: 15, fontWeight: "700" },

  // Preview
  previewWrap: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#e0e0e0",
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
  },
  preview: { width: "100%", height: "100%", resizeMode: "cover" },
});
