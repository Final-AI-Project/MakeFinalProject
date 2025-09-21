// app/(page)/diary.tsx

// ─────────────────────────────────────────────────────────────────────────────
// ① Imports
// ─────────────────────────────────────────────────────────────────────────────
import React, { useMemo, useRef, useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  TextInput,
  Pressable,
  Image,
  Alert,
  ActivityIndicator,
  Animated,
  Easing,
  PanResponder,
  Dimensions,
  Keyboard,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useColorScheme } from "react-native";
import { useRouter } from "expo-router";
import Colors from "../../constants/Colors";
import { fetchSimpleWeather } from "../../components/common/weatherBox";
import { getApiUrl } from "../../config/api";
import { getToken } from "../../libs/auth";
import { useFocusEffect } from "@react-navigation/native";

// ✅ 데코 이미지 (RN는 default import/require 사용)
import LLMDecoImage from "../../assets/images/LLM_setting.png"; // 고정
import LLMDecoImageFace from "../../assets/images/LLM_setting_face.png"; // 애니메 #1
import LLMDecoImageHand from "../../assets/images/LLM_setting_hand.png"; // 애니메 #2

// ─────────────────────────────────────────────────────────────────────────────
// ② Helpers & Types
// ─────────────────────────────────────────────────────────────────────────────
type Weather = "맑음" | "흐림" | "비" | "눈" | null;

// expo-image-picker 신/구 버전 호환(enum 폴리필)
const MEDIA =
  (ImagePicker as any).MediaType ?? (ImagePicker as any).MediaTypeOptions;

const todayStr = () => {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
};

// 한글 조사 자동(이/가, 을/를 등 지원 확장 가능)
function withJosa(word: string, type: "이가" | "을를" = "이가") {
  const code = word.charCodeAt(word.length - 1);
  const HANGUL_BASE = 0xac00;
  const HANGUL_END = 0xd7a3;
  let hasJong = false;
  if (code >= HANGUL_BASE && code <= HANGUL_END) {
    const jong = (code - HANGUL_BASE) % 28;
    hasJong = jong > 0;
  }
  if (type === "이가") return `${word}${hasJong ? "이" : "가"}`;
  return `${word}${hasJong ? "을" : "를"}`;
}

/** 인라인 드롭다운(모달 없이) */
function InlineSelect<T extends string>({
  label,
  value,
  options,
  onChange,
  placeholder = "선택하세요",
  theme,
}: {
  label: string;
  value: T | null;
  options: { label: string; value: T }[];
  onChange: (v: T) => void;
  placeholder?: string;
  theme: typeof Colors.light;
}) {
  const [open, setOpen] = useState(false);
  return (
    <View style={styles.field}>
      <Text style={[styles.sectionLabel, { color: theme.text }]}>{label}</Text>
      <Pressable
        onPress={() => setOpen((v) => !v)}
        style={[styles.input, { borderColor: theme.border }]}
      >
        <Text style={{ color: theme.text }}>
          {value ? options.find((o) => o.value === value)?.label : placeholder}
        </Text>
      </Pressable>
      {open && (
        <View style={[styles.dropdownPanel, { borderColor: theme.border }]}>
          {options.map((opt) => (
            <Pressable
              key={opt.value}
              onPress={() => {
                onChange(opt.value);
                setOpen(false);
              }}
              style={[styles.dropdownItem, { backgroundColor: theme.bg }]}
            >
              <Text style={{ color: theme.text }}>{opt.label}</Text>
            </Pressable>
          ))}
        </View>
      )}
    </View>
  );
}

/** 한 글자씩 등장하는 애니메이션 텍스트 */
function AnimatedChars({
  text,
  delayStep = 24,
  duration = 280,
  style,
}: {
  text: string;
  delayStep?: number;
  duration?: number;
  style?: any;
}) {
  const chars = React.useMemo(() => [...(text ?? "")], [text]);

  // 각 글자별 Animated.Value
  const valuesRef = React.useRef(chars.map(() => new Animated.Value(0)));
  if (valuesRef.current.length !== chars.length) {
    valuesRef.current = chars.map(() => new Animated.Value(0));
  }

  useEffect(() => {
    const animations = valuesRef.current.map((v, i) =>
      Animated.timing(v, {
        toValue: 1,
        duration,
        delay: i * delayStep,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      })
    );
    Animated.stagger(delayStep, animations).start();
  }, [text, delayStep, duration]);

  return (
    <View style={{ flexDirection: "row", flexWrap: "wrap" }}>
      {chars.map((ch, i) => {
        const v = valuesRef.current[i];
        const translateY = v.interpolate({
          inputRange: [0, 1],
          outputRange: [12, 0],
        });
        return (
          <Animated.Text
            key={`${ch}-${i}-${chars.length}`}
            style={[style, { opacity: v, transform: [{ translateY }] }]}
          >
            {ch}
          </Animated.Text>
        );
      })}
    </View>
  );
}

/** 바텀시트 (딤 탭으로는 닫히지 않음 / 드래그 & 버튼만 닫힘 / 닫은 뒤 스크롤 잠김 방지) */
function BottomSheet({
  visible,
  text,
  title,
  onClose,
  theme,
  children,
}: {
  visible: boolean;
  text: string;
  title: string;
  onClose: () => void;
  theme: typeof Colors.light;
  children?: React.ReactNode; // ✅ 렌더만 추가 (기능 변화 없음)
}) {
  const screenH = Dimensions.get("window").height;
  const translateY = useRef(new Animated.Value(screenH)).current;
  const [interactive, setInteractive] = useState(false);
  const [isOpen, setIsOpen] = useState(false); // _value 대신 내부 상태로 가드
  const visibleRef = useRef(visible);
  useEffect(() => {
    visibleRef.current = visible;
  }, [visible]);

  const openSheet = () => {
    translateY.stopAnimation(); // ✅ 이전 애니메이션 중단
    setInteractive(true);
    setIsOpen(true);
    Animated.timing(translateY, {
      toValue: 0,
      duration: 260,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: true,
    }).start(({ finished }) => {
      if (!finished) return;
      // 열기 완료 후에도 최신 visible이 false면 즉시 닫기 일치화
      if (!visibleRef.current) closeSheet();
    });
  };

  const closeSheet = (after?: () => void) => {
    translateY.stopAnimation(); // ✅ 이전 애니메이션 중단
    Animated.timing(translateY, {
      toValue: screenH,
      duration: 200,
      easing: Easing.in(Easing.cubic),
      useNativeDriver: true,
    }).start(({ finished }) => {
      if (!finished) return;
      setIsOpen(false);
      // ❗ 최신 의도 상태를 보고 포인터 해제
      setInteractive(visibleRef.current ? true : false);
      after?.();
    });
  };

  useEffect(() => {
    if (visible) openSheet();
    else closeSheet();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, g) => g.dy > 6,
      onPanResponderGrant: () => {
        // ✅ 드래그 시작 시 포인터 보장
        setInteractive(true);
      },
      onPanResponderMove: (_, g) => {
        const dy = Math.max(0, g.dy);
        translateY.setValue(dy);
      },
      onPanResponderRelease: (_, g) => {
        const shouldClose = g.dy > 120 || g.vy > 0.8;
        if (shouldClose) closeSheet(onClose);
        else {
          Animated.spring(translateY, {
            toValue: 0,
            useNativeDriver: true,
            bounciness: 3,
          }).start();
        }
      },
    })
  ).current;

  // ✅ _value 의존 제거: 의도(visible)와 내부 상태(isOpen), 포인터(interactive)로 판단
  if (!visible && !isOpen && !interactive) return null;

  const dimOpacity = translateY.interpolate({
    inputRange: [0, screenH],
    outputRange: [1, 0],
  });

  return (
    <View
      style={[
        StyleSheet.absoluteFill,
        { pointerEvents: interactive ? "auto" : "none" },
      ]}
    >
      <Animated.View
        style={[
          StyleSheet.absoluteFillObject,
          { backgroundColor: "rgba(0,0,0,0.5)", opacity: dimOpacity },
        ]}
      />
      <Animated.View
        style={[styles.sheetWrap, { transform: [{ translateY }] }]}
        {...panResponder.panHandlers}
      >
        <View
          style={[
            styles.sheetHandle,
            {
              backgroundColor: theme.text === "#1a1a1a" ? "#d1d5db" : "#475569",
            },
          ]}
        />
        <Text style={[styles.sheetTitle, { color: theme.text }]}>{title}</Text>
        <View style={styles.sheetBody}>
          <AnimatedChars
            text={text || "임시 응답 텍스트가 없습니다."}
            delayStep={22}
            duration={260}
            style={[styles.sheetText, { color: theme.text }]}
          />
          {/* ✅ 데코(children) 영역 — 기능 변화 없음, 렌더만 */}
          {children ? <View style={styles.sheetDeco}>{children}</View> : null}
        </View>
        <View style={styles.sheetActions}>
          <Pressable
            onPress={() => closeSheet(onClose)}
            style={[styles.sheetBtn]}
          >
            <Text style={[styles.sheetBtnText, { color: theme.text }]}>
              닫기
            </Text>
          </Pressable>
        </View>
      </Animated.View>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ③ Component
// ─────────────────────────────────────────────────────────────────────────────
export default function Diary() {
  // Theme & Router
  const scheme = useColorScheme();
  const theme = Colors[scheme === "dark" ? "dark" : "light"];
  const router = useRouter();

  // 폼 상태
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [selectedPlant, setSelectedPlant] = useState<string | null>(null);
  const [date] = useState(todayStr());
  const [weather, setWeather] = useState<Weather>(null); // 자동/readonly
  const [body, setBody] = useState("");

  // 기타 UI
  const [busy, setBusy] = useState(false);
  const [sheetVisible, setSheetVisible] = useState(false);

  // AI 텍스트 (단일 소스)
  const [aiText, setAiText] = useState<string>(
    "오늘은 통풍만 잘 시켜주세요. 물은 내일 추천! 🌤️오늘은 통풍만 잘 시켜주세요. 물은 내일 추천! 🌤️오늘은 통풍만 잘 시켜주세요. 물은 내일 추천! 🌤️오늘은 통풍만 잘 시켜주세요. 물은 내일 추천! 🌤️"
  );

  // 등록 후에만 미리보기 표시
  const [aiPreviewVisible, setAiPreviewVisible] = useState(false);

  // ✅ 등록 여부: 등록 1회 후 '수정' 모드로 전환
  const [isSubmitted, setIsSubmitted] = useState(false);

  // 내 식물(별명) - 실제 API에서 가져오기
  const [myPlants, setMyPlants] = useState<{ label: string; value: string }[]>(
    []
  );
  const [plantsLoading, setPlantsLoading] = useState(true);

  // 식물 목록 가져오기
  useEffect(() => {
    const fetchMyPlants = async () => {
      try {
        const token = await getToken();
        if (!token) return;

        const apiUrl = await getApiUrl("/home/plants/current");
        const response = await fetch(apiUrl, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (response.ok) {
          const data = await response.json();
          if (data.plants && Array.isArray(data.plants)) {
            const plantOptions = data.plants.map((plant: any) => ({
              label: `${plant.plant_name} (${plant.species || "기타"})`,
              value: plant.plant_name,
            }));
            setMyPlants(plantOptions);
          }
        }
      } catch (error) {
        console.error("식물 목록 가져오기 실패:", error);
      } finally {
        setPlantsLoading(false);
      }
    };

    fetchMyPlants();
  }, []);

  // 날씨 자동 채움 (WeatherBox 렌더링 없이) — 기존 그대로 유지
  useEffect(() => {
    (async () => {
      try {
        const w = await fetchSimpleWeather(
          "GTr1cI7Wi0FRbOTFBaUzUCzCDP4OnyyEmHnn11pxCUC5ehG5bQnbyztgeydnOWz1O04tjw1SE5RsX8RNo6XCgQ==",
          { lat: 37.4836, lon: 127.0326, label: "서울시 - 서초구" }
        );
        if (w) setWeather((prev) => prev ?? w);
      } catch (e) {
        console.warn("[weather] fetch failed:", e);
      }
    })();
  }, []);

  // ✅ 제출 버튼 활성 조건 (모든 입력 완료 판정)
  const canSubmit = Boolean(
    photoUri && title.trim() && selectedPlant && date && weather && body.trim()
  );

  // 사진 선택
  const pickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted")
      return Alert.alert("권한 필요", "앨범 접근 권한을 허용해주세요.");
    setBusy(true);
    try {
      const res = await ImagePicker.launchImageLibraryAsync({
        allowsEditing: true,
        quality: 0.9,
        mediaTypes: MEDIA?.Images ?? ImagePicker.MediaTypeOptions.Images,
        aspect: [1, 1],
      });
      if (!res.canceled && res.assets?.[0]?.uri) setPhotoUri(res.assets[0].uri);
    } finally {
      setBusy(false);
    }
  };

  // 등록: 시트는 등록하면 열림
  const handleSubmit = async () => {
    if (!canSubmit) return;

    try {
      const token = await getToken();
      if (!token) {
        Alert.alert("오류", "로그인이 필요합니다.");
        return;
      }

      // 일기 작성 API 호출
      const diaryData = {
        user_title: title,
        user_content: body,
        plant_nickname: selectedPlant,
        plant_species: selectedPlant, // TODO: 실제 식물 종으로 교체
        hashtag: `#${selectedPlant} #${weather || "일상"}`,
      };

      const apiUrl = await getApiUrl("/diary-list/create");
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(diaryData),
      });

      if (!response.ok) {
        throw new Error(`일기 작성 실패: ${response.status}`);
      }

      const result = await response.json();
      console.log("일기 작성 성공:", result);

      // TODO: LLM 호출 후 setAiText(resp.message)
      setAiPreviewVisible(true); // 등록 후에만 미리보기 표시
      setSheetVisible(true); // 등록하면 바텀시트 열림
      setIsSubmitted(true); // 이후부터 '수정' 모드
    } catch (error) {
      console.error("일기 작성 오류:", error);
      Alert.alert("일기 작성 실패", "일기 작성 중 문제가 발생했습니다.");
    }
  };

  // 수정: 오늘의 일기 업데이트 + LLM 재호출 + 알럿 + 시트 오픈
  const handleUpdate = async () => {
    if (!canSubmit) return;
    try {
      // 1) 서버에 업데이트
      // await fetch("/api/diaries/today", {...})

      // 2) (예시) LLM 코멘트 갱신
      // const llmResp = await fetch("/api/diaries/today/llm-comment", {...}).then(r => r.json());
      // setAiText(llmResp.message ?? aiText);

      // 데모 문구
      setAiText("업데이트 반영 완료! 오늘 컨디션 좋아요 🌿");

      // 3) 미리보기/시트 표시
      if (!aiPreviewVisible) setAiPreviewVisible(true);
      setSheetVisible(true);
    } catch {
      Alert.alert("수정 실패", "잠시 후 다시 시도해 주세요.");
    }
  };

  // 버튼 라벨/핸들러 스위칭
  const primaryLabel = isSubmitted ? "수정하기" : "등록하기";
  const primaryOnPress = isSubmitted ? handleUpdate : handleSubmit;

  // 바텀시트 타이틀
  const sheetTitle = `${selectedPlant ?? "식물"}의 하고픈 말`;

  // ✨ 무한 애니메이션 (face, hand)
  const move1 = useRef(new Animated.Value(0)).current;
  const move2 = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const loop1 = Animated.loop(
      Animated.sequence([
        Animated.timing(move1, {
          toValue: 1,
          duration: 2000,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
        Animated.timing(move1, {
          toValue: 0,
          duration: 2000,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
      ])
    );
    const loop2 = Animated.loop(
      Animated.sequence([
        Animated.timing(move2, {
          toValue: 1,
          duration: 2000,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
        Animated.timing(move2, {
          toValue: 0,
          duration: 2000,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
      ])
    );
    loop1.start();
    const id = setTimeout(() => loop2.start(), 400); // 약간 시간차
    return () => {
      loop1.stop();
      loop2.stop();
      clearTimeout(id);
    };
  }, [move1, move2]);

  const tx1 = move1.interpolate({ inputRange: [0, 1], outputRange: [-3, 3] });
  const tx2 = move2.interpolate({ inputRange: [0, 1], outputRange: [3, -3] });

  // ─────────────────────────────────────────────────────────────────────
  // ✅ 포커스 시 전체 리셋 (날씨/날짜는 건드리지 않음)
  // ─────────────────────────────────────────────────────────────────────
  const resetDiary = React.useCallback(() => {
    Keyboard.dismiss();
    setPhotoUri(null);
    setTitle("");
    setSelectedPlant(null);
    setBody("");
    setAiPreviewVisible(false);
    setIsSubmitted(false);
    setSheetVisible(false);
    setAiText(
      "오늘은 통풍만 잘 시켜주세요. 물은 내일 추천! 🌤️오늘은 통풍만 잘 시켜주세요. 물은 내일 추천! 🌤️오늘은 통풍만 잘 시켜주세요. 물은 내일 추천! 🌤️오늘은 통풍만 잘 시켜주세요. 물은 내일 추천! 🌤️"
    );
  }, []);

  useFocusEffect(
    React.useCallback(() => {
      resetDiary();
    }, [resetDiary])
  );

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: (theme as any).bg }]}
      behavior={Platform.select({ ios: "padding", android: "height" })}
    >
      <ScrollView
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="interactive"
      >
        {/* 사진 등록 */}
        <View style={styles.photoBox}>
          <Pressable
            onPress={pickImage}
            disabled={busy}
            style={[
              styles.photoPlaceholder,
              { borderColor: theme.border, backgroundColor: theme.graybg },
            ]}
          >
            {photoUri ? (
              <>
                <Image
                  source={{ uri: photoUri }}
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

        {/* 입력들 */}
        <View style={styles.inputArea}>
          {/* 제목 */}
          <View style={styles.field}>
            <Text style={[styles.sectionLabel, { color: theme.text }]}>
              제목
            </Text>
            <TextInput
              placeholder="제목을 입력하세요"
              placeholderTextColor="#909090"
              value={title}
              onChangeText={setTitle}
              style={[
                styles.input,
                { color: theme.text, borderColor: theme.border },
              ]}
              returnKeyType="next"
            />
          </View>

          {/* 내 식물(별명) */}
          <InlineSelect
            label="내 식물(별명)"
            value={selectedPlant}
            options={myPlants}
            onChange={setSelectedPlant}
            placeholder={
              plantsLoading ? "식물 목록 로딩 중..." : "내 식물을 선택하세요"
            }
            theme={theme as any}
          />

          {/* 날짜 (읽기전용) */}
          <View style={styles.field}>
            <Text style={[styles.sectionLabel, { color: theme.text }]}>
              날짜
            </Text>
            <TextInput
              value={date}
              editable={false}
              style={[
                styles.input,
                { color: theme.text, borderColor: theme.border, opacity: 0.85 },
              ]}
            />
          </View>

          {/* 날씨 (자동/읽기전용) */}
          <View style={styles.field}>
            <Text style={[styles.sectionLabel, { color: theme.text }]}>
              날씨
            </Text>
            <TextInput
              value={weather ?? ""}
              editable={false}
              placeholder="조회 중…"
              placeholderTextColor="#909090"
              style={[
                styles.input,
                { color: theme.text, borderColor: theme.border, opacity: 0.85 },
              ]}
            />
          </View>

          {/* 일기 내용 */}
          <View style={styles.field}>
            <Text style={[styles.sectionLabel, { color: theme.text }]}>
              일기 내용
            </Text>
            <TextInput
              placeholder="오늘의 식물 이야기를 적어주세요…"
              placeholderTextColor="#909090"
              value={body}
              onChangeText={setBody}
              multiline
              textAlignVertical="top"
              style={[
                styles.input,
                {
                  color: theme.text,
                  borderColor: theme.border,
                  minHeight: 180,
                  lineHeight: 22,
                },
              ]}
            />
          </View>

          {/* 🔹 AI 응답(미리보기): 등록 전엔 숨김, 등록 후에만 표시 */}
          {aiPreviewVisible && (
            <View style={styles.field}>
              <Text style={[styles.sectionLabel, { color: theme.text }]}>
                {selectedPlant
                  ? `${withJosa(selectedPlant, "이가")} 하고픈 말`
                  : "AI 응답(미리보기)"}
              </Text>
              <View
                style={[
                  styles.input,
                  { borderColor: theme.border, paddingVertical: 14 },
                ]}
              >
                <AnimatedChars
                  text={aiText}
                  style={{ color: theme.text, fontSize: 15, lineHeight: 22 }}
                />
              </View>
            </View>
          )}

          {/* 하단 버튼 */}
          <View style={[styles.bottomBar, { backgroundColor: theme.bg }]}>
            <Pressable
              onPress={() => router.back()}
              style={[styles.cancelBtn, { borderColor: theme.border }]}
            >
              <Text style={[styles.cancelText, { color: theme.text }]}>
                취소
              </Text>
            </Pressable>
            <Pressable
              disabled={!canSubmit}
              onPress={() => {
                Keyboard.dismiss();
                primaryOnPress();
              }} // ← 먼저 키패드 닫기
              style={[
                styles.submitBtn,
                { backgroundColor: !canSubmit ? theme.graybg : theme.primary },
              ]}
            >
              <Text style={[styles.submitText, { color: "#fff" }]}>
                {primaryLabel}
              </Text>
            </Pressable>
          </View>
        </View>
      </ScrollView>

      {/* 바텀시트 (등록 시 자동 열림, 드래그/닫기버튼만 닫힘) */}
      <BottomSheet
        visible={sheetVisible}
        text={aiText}
        title={sheetTitle}
        onClose={() => setSheetVisible(false)}
        theme={theme as any}
      >
        <View style={styles.LLMDecoBox}>
          {/* 고정 이미지 */}
          <Image
            source={LLMDecoImage}
            style={styles.LLMDecoImage}
            resizeMode="contain"
          />
          {/* 움직이는 얼굴 */}
          <Animated.Image
            source={LLMDecoImageFace}
            style={[styles.LLMDecoFace, { transform: [{ translateX: tx1 }] }]}
            resizeMode="contain"
          />
          {/* 움직이는 손 */}
          <Animated.Image
            source={LLMDecoImageHand}
            style={[styles.LLMDecoHand, { transform: [{ translateX: tx2 }] }]}
            resizeMode="contain"
          />
        </View>
      </BottomSheet>
    </KeyboardAvoidingView>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ④ Styles (plant-new.tsx 톤과 동일 스케일)
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1, paddingBottom: 72 },

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
    borderWidth: 1,
    minHeight: 50,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 12,
  },

  bottomBar: { flexDirection: "row", gap: 8, marginTop: 24 },
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

  dropdownPanel: {
    borderWidth: 1,
    borderRadius: 10,
    overflow: "hidden",
    marginTop: -6,
  },
  dropdownItem: { paddingHorizontal: 12, paddingVertical: 12 },

  // ── 바텀시트
  sheetWrap: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 65,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 10,
    paddingHorizontal: 20,
    paddingBottom: 20,
    backgroundColor: "#ffffff",
  },
  sheetHandle: {
    alignSelf: "center",
    width: 42,
    height: 5,
    borderRadius: 999,
    opacity: 0.5,
    marginBottom: 12,
  },
  sheetTitle: {
    fontSize: 14,
    fontWeight: "800",
    marginBottom: 8,
    opacity: 0.8,
  },
  sheetBody: { paddingVertical: 6 },
  sheetText: { fontSize: 16, lineHeight: 24 },

  // ✅ 데코(children) 영역 — 시각만, 기능 변경 없음
  sheetDeco: {
    marginTop: 6,
    marginBottom: 6,
    alignSelf: "stretch",
    alignItems: "center",
    justifyContent: "center",
    overflow: "visible",
  },

  sheetActions: { marginTop: 12, alignItems: "flex-end" },
  sheetBtn: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 10,
    backgroundColor: "rgba(0,0,0,0.06)",
  },
  sheetBtnText: { fontWeight: "700" },

  LLMDecoBox: {
    display: "flex",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "flex-end",
    position: "relative",
    width: "100%",
  },
  LLMDecoImage: {
    width: 120,
    height: 100,
  },
  LLMDecoFace: {
    position: "absolute",
    width: 70,
    height: 48,
    right: 22,
    top: 4,
  },
  LLMDecoHand: {
    position: "absolute",
    width: 42,
    height: 42,
    right: 50,
    top: 46,
  },
});
