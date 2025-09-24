// app/(tabs)/index.tsx
// ─────────────────────────────────────────────────────────────────────────────
// ① Imports
// ─────────────────────────────────────────────────────────────────────────────
import React, { useMemo, useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  useColorScheme,
  Pressable,
  Image,
} from "react-native";
import { showAlert } from "../../components/common/appAlert";
import { Link, useRouter, useLocalSearchParams } from "expo-router";
import Colors from "../../constants/Colors";
import WeatherBox from "../../components/common/weatherBox";
import Carousel from "react-native-reanimated-carousel";
import { LinearGradient } from "expo-linear-gradient";
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  useAnimatedReaction,
} from "react-native-reanimated";
import { useAuthGuard } from "../../hooks/useAuthGuard";
import { getApiUrl } from "../../config/api";
import { getToken } from "../../libs/auth";
import { startLoading, stopLoading } from "../../components/common/loading";
import { useFocusEffect } from "@react-navigation/native";
import { API_BASE_URL } from "../../config/api";

// API_BASE_URL 확인 (개발용)
// console.log("🏠 Home에서 API_BASE_URL:", API_BASE_URL);

// ─────────────────────────────────────────────────────────────────────────────
// ② Types & Constants
// ─────────────────────────────────────────────────────────────────────────────
const { width } = Dimensions.get("window");

type Slide = {
  key: string;
  label: string;
  bg: string;
  color?: string;
  species?: string;
  photoUri?: string | null;
  startedAt?: string;
  type?: "action";
  waterLevel?: number;
  health?: "좋음" | "주의" | "나쁨";
};

// 백엔드 API 응답 타입
type PlantStatusResponse = {
  idx: number;
  user_id: string;
  plant_id: number;
  plant_name: string;
  species?: string;
  pest_id?: number;
  meet_day?: string;
  on?: string;
  current_humidity?: number;
  humidity_date?: string;
  wiki_img?: string;
  feature?: string;
  temp?: string;
  watering?: string;
  pest_cause?: string;
  pest_cure?: string;
  user_plant_image?: string;
};

type DashboardResponse = {
  user_id: string;
  total_plants: number;
  plants: PlantStatusResponse[];
  message: string;
};

// ─────────────────────────────────────────────────────────────────────────────
// ③ Component
// ─────────────────────────────────────────────────────────────────────────────
export default function Home() {
  // 3-1) Router & Theme
  const router = useRouter();
  const params = useLocalSearchParams();
  const scheme = useColorScheme();
  const theme = Colors[scheme === "dark" ? "dark" : "light"];

  // 인증 가드 추가
  useAuthGuard();

  // 3-2) Shared/Local States
  const progress = useSharedValue(0);
  const [activeIndex, setActiveIndex] = useState(0);
  const [parentW, setParentW] = useState(0);
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState<DashboardResponse | null>(
    null
  );

  // 3-3) Gauge layout constants
  const SIZE = 250;
  const HALF = SIZE / 2;

  // 3-4) API 호출 함수 (최초 진입용: 오버레이 표시)
  const fetchUserPlants = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) {
        console.log("🔑 No token found in fetchUserPlants, skipping API call");
        setLoading(false);
        return;
      }

      // 로딩 시작(오버레이)
      startLoading(router, {
        message: "식물 정보를 불러오는 중...",
        to: "/(page)/home" as any,
        task: async () => {
          const apiUrl = getApiUrl("/home/plants/current");
          const response = await fetch(apiUrl, {
            method: "GET",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const data: DashboardResponse = await response.json();
          setDashboardData(data);
        },
      });
    } catch (error) {
      console.error("식물 데이터 조회 실패:", error);
      showAlert({
        title: "오류",
        message: "식물 정보를 불러오는데 실패했습니다.",
        buttons: [{ text: "확인" }],
      });
      stopLoading(router);
    } finally {
      setLoading(false);
    }
  };

  // ✅ 3-4-1) 포커스 시 사용할 '조용한' 리패치 (오버레이 X)
  const refetchUserPlantsSilently = async () => {
    try {
      const token = await getToken();
      if (!token) {
        console.log("🔑 토큰이 없어서 리패치 중단");
        return;
      }

      const apiUrl = getApiUrl("/home/plants/current");
      console.log("🌐 API URL:", apiUrl);
      console.log("🔑 토큰 존재:", !!token);

      const response = await fetch(apiUrl, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      console.log("📡 응답 상태:", response.status, response.ok);

      if (!response.ok) {
        console.log("❌ 응답 실패:", response.status, response.statusText);
        return;
      }

      const data: DashboardResponse = await response.json();
      console.log("✅ 데이터 받음:", data);
      setDashboardData(data);
    } catch (e) {
      console.error("❌ refetchUserPlantsSilently error:", e);
    }
  };

  // ✅ 3-4-2) 홈 전체 초기화 + 최신 데이터 재로딩
  const resetHome = React.useCallback(() => {
    // 상태 초기화
    setActiveIndex(0);
    setParentW(0);
    setDashboardData(null);
    setLoading(true);
    progress.value = 0;

    // 최신 데이터 로딩(오버레이 없이 조용히)
    refetchUserPlantsSilently().finally(() => setLoading(false));
  }, [progress]);

  // 3-5) 최초 진입: 한 번 로딩 (오버레이 포함)
  useEffect(() => {
    fetchUserPlants();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ✅ 3-5-1) 홈 탭에 '들어올 때마다' 조용한 새로고침 (불필요한 호출 방지)
  const lastFetchTime = React.useRef<number>(0);
  useFocusEffect(
    React.useCallback(() => {
      const now = Date.now();
      // 홈페이지에 들어올 때마다 데이터 새로고침 (간격 제한: 5초)
      if (dashboardData && !loading && now - lastFetchTime.current > 5000) {
        lastFetchTime.current = now;
        refetchUserPlantsSilently();
      }
    }, [refetchUserPlantsSilently, dashboardData, loading])
  );

  // 3-6) 백엔드 데이터를 UI 데이터로 변환
  const convertToSlide = (plant: PlantStatusResponse): Slide => {
    // 건강 상태 결정 (병해충이 있으면 "나쁨", 습도가 낮으면 "주의", 그 외는 "좋음")
    let health: "좋음" | "주의" | "나쁨" = "좋음";
    if (plant.pest_id) {
      health = "나쁨";
    } else if (plant.current_humidity && plant.current_humidity < 30) {
      health = "주의";
    }

    // 이미지 URL을 완전한 URL로 변환
    let photoUri: string | null = null;
    if (plant.user_plant_image) {
      // 상대 경로인 경우 절대 경로로 변환
      if (plant.user_plant_image.startsWith("/static/")) {
        // API_BASE_URL을 사용해서 일관성 있게 처리
        const apiBaseUrl = API_BASE_URL;
        photoUri = `${apiBaseUrl}${plant.user_plant_image}`;
      } else {
        photoUri = plant.user_plant_image;
      }
    }

    return {
      key: plant.plant_id.toString(),
      label: plant.plant_name,
      bg: theme.bg,
      color: theme.text,
      waterLevel: plant.current_humidity || 0,
      species: plant.species,
      startedAt: plant.meet_day,
      photoUri: photoUri,
      health: health,
    };
  };

  // 3-7) 실제 데이터만 사용 (하드코딩 제거)
  const plants = useMemo(() => {
    if (dashboardData && dashboardData.plants.length > 0) {
      return dashboardData.plants.map(convertToSlide);
    }
    // API 호출 실패/없음 → 빈 배열
    return [];
  }, [dashboardData, theme]);

  const slides = useMemo(() => {
    // 식물이 없으면 "새 식물 등록" 버튼만 표시
    if (plants.length === 0) {
      return [
        {
          key: "add",
          label: "+ \n 새 식물 등록",
          bg: theme.graybg,
          type: "action" as const,
        },
      ];
    }

    // 식물이 있으면 식물들 + 새 식물 등록 버튼
    return [
      ...plants,
      {
        key: "add",
        label: "+ \n 새 식물 등록",
        bg: theme.graybg,
        type: "action" as const,
      },
    ];
  }, [plants, theme]);

  // ─────────────────────────────────────────────────────────────────────────
  // 3-5) UI Sub-Component: AnimatedGauge (water level needle)
  // ─────────────────────────────────────────────────────────────────────────
  const AnimatedGauge = React.memo(function AnimatedGauge({
    index,
    progress,
    size,
    targetDeg,
    style,
  }: {
    index: number;
    progress: ReturnType<typeof useSharedValue<number>>;
    size: number;
    targetDeg: number; // 0~180 (급수계 각도)
    style?: any;
  }) {
    // 현재 회전 각도(숫자)를 보관
    const rot = useSharedValue(0);

    // 보이는지 여부에 따라 rot를 0 ↔ targetDeg로 부드럽게 이동
    useAnimatedReaction(
      () => {
        const visible = Math.abs(progress.value - index) < 0.5; // 중앙 근처 = 보임
        return visible ? targetDeg : 0;
      },
      (to, prev) => {
        if (to !== prev) {
          rot.value = withTiming(to, { duration: 500 });
        }
      }
    );

    const slot2AnimatedStyle = useAnimatedStyle(() => ({
      transform: [
        { translateY: -size / 2 },
        { rotate: `${rot.value}deg` },
        { translateY: size / 2 },
      ],
    }));

    return <Animated.View style={[style, slot2AnimatedStyle]} />;
  });

  // ─────────────────────────────────────────────────────────────────────────
  // 3-6) Render
  // ─────────────────────────────────────────────────────────────────────────
  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      {/* ✅ 공통 날씨 컴포넌트만 사용 */}
      <WeatherBox
        serviceKey="GTr1cI7Wi0FRbOTFBaUzUCzCDP4OnyyEmHnn11pxCUC5ehG5bQnbyztgeydnOWz1O04tjw1SE5RsX8RNo6XCgQ=="
        location={{ lat: 37.4836, lon: 127.0326, label: "서울시 - 서초구" }}
      />

      {/* 캐러셀 */}
      <View style={styles.carouselRoot}>
        <Carousel
          loop={false}
          width={width}
          height={250}
          data={slides}
          scrollAnimationDuration={700}
          defaultIndex={0}
          onProgressChange={(_, abs) => {
            progress.value = abs;
            setActiveIndex(Math.round(abs));
          }}
          renderItem={({ item, index }) => {
            // 습도(%) → 각도(0~180deg) 변환
            const percent = Math.max(0, Math.min(100, item.waterLevel ?? 0));
            const targetDeg = percent * 1.8; // (percent / 100) * 180

            return (
              <View
                style={[styles.carouselSlide, { backgroundColor: item.bg }]}
              >
                {item.type === "action" ? (
                  <Pressable
                    onPress={() => router.push("/(page)/(stackless)/plant-new")}
                  >
                    <Text
                      style={[
                        styles.carouselSlideText,
                        { color: theme.text, textAlign: "center" },
                      ]}
                    >
                      {item.label}
                    </Text>
                  </Pressable>
                ) : (
                  /* ── [MINIMAL CHANGE] 식물 카드 전체를 눌러 상세로 이동 */
                  <Pressable
                    style={styles.plantCard}
                    onLayout={(e) => setParentW(e.nativeEvent.layout.width)}
                    onPress={() => {
                      // activeIndex 업데이트
                      const plantIndex = slides.findIndex(
                        (slide) => slide.key === item.key
                      );

                      if (plantIndex !== -1) {
                        setActiveIndex(plantIndex);
                      }

                      router.push({
                        pathname: "/(page)/(stackless)/plant-detail",
                        params: {
                          id: item.key,
                          imageUri: item.photoUri ?? "",
                          nickname: item.label,
                          species: item.species ?? "",
                          startedAt: item.startedAt ?? "",
                          timestamp: Date.now().toString(), // 캐싱 방지를 위한 타임스탬프
                        },
                      });
                    }}
                  >
                    {/* Gauge slots */}
                    <View style={[styles.slotBox, { left: parentW / 2 }]}>
                      <View style={styles.slot1} />
                      <AnimatedGauge
                        index={index}
                        progress={progress}
                        size={250}
                        targetDeg={targetDeg}
                        style={styles.slot2}
                      />
                      <View
                        style={[styles.slot3, { backgroundColor: theme.bg }]}
                      />
                    </View>

                    <View
                      style={[styles.slot4, { backgroundColor: theme.bg }]}
                    />

                    {/* Plant image */}
                    <View style={styles.photoBox}>
                      {item.photoUri ? (
                        <Image
                          source={{ uri: item.photoUri }}
                          style={styles.plantImage}
                          resizeMode="cover"
                        />
                      ) : (
                        <View style={styles.plantImagePlaceholder}>
                          <Text style={{ color: theme.text }}>🌱</Text>
                        </View>
                      )}

                      {/* ✨ 상태에 따라 표시 */}
                      {(item.health === "주의" || item.health === "나쁨") && (
                        <View
                          style={[
                            styles.medicalInfo,
                            item.health === "주의"
                              ? { backgroundColor: "#ffc900" }
                              : { backgroundColor: "#d32f2e" },
                          ]}
                        />
                      )}
                    </View>

                    {/* Labels */}
                    <Text style={[styles.plantName, { color: theme.text }]}>
                      {item.label}
                      {item.species && (
                        <Text
                          style={[styles.plantSpecies, { color: theme.text }]}
                        >
                          ({item.species})
                        </Text>
                      )}
                    </Text>
                  </Pressable>
                )}
              </View>
            );
          }}
        />
        {/* Dots */}
        <View style={styles.carouselDots}>
          {slides.map((_, i) => (
            <View
              key={String(i)}
              style={[
                styles.carouselDot,
                i === activeIndex && styles.carouselDotActive,
              ]}
            />
          ))}
        </View>
      </View>

      {/* Links */}
      <View style={styles.linkList}>
        {/* newPlant */}
        <Link href="/(page)/(stackless)/timelapse" asChild>
          <Pressable style={styles.cardBase}>
            <LinearGradient
              colors={["#F97794", "#623AA2"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFillObject}
            />
            <Text style={styles.cardTextLight}>
              타임랩스를{"\n"}경험해 보세요
            </Text>
          </Pressable>
        </Link>

        {/* plantInfo */}
        <Link href="/(page)/(stackless)/info-room" asChild>
          <Pressable style={styles.cardBase}>
            <LinearGradient
              colors={["#FFF6B7", "#F6416C"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFillObject}
            />
            <Text style={styles.cardTextLight}>식물{"\n"}정보방</Text>
          </Pressable>
        </Link>
      </View>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ④ Styles (섹션별 주석 유지)
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 20,
    paddingHorizontal: 24,
    paddingBottom: 68,
  },

  // ── Logout button
  logoutContainer: {
    alignItems: "flex-end",
    marginBottom: 16,
  },
  logoutButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: "rgba(0,0,0,0.1)",
  },
  logoutText: {
    fontSize: 14,
    fontWeight: "500",
  },

  // ── Carousel card & image
  plantCard: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    width: "100%",
    padding: 16,
  },
  photoBox: {
    position: "relative",
    width: 120,
    height: 120,
    borderRadius: 60,
    marginTop: 75,
  },
  plantImage: {
    width: 120,
    height: 120,
    borderRadius: 60,
    objectFit: "cover",
  },
  plantImagePlaceholder: {
    overflow: "hidden",
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: "#ccc",
    justifyContent: "center",
    alignItems: "center",
  },
  medicalInfo: {
    position: "absolute",
    right: 0,
    bottom: 0,
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: "center",
    alignItems: "center",
  },
  plantName: {
    fontSize: 20,
    fontWeight: "700",
  },
  plantSpecies: {
    fontSize: 14,
    marginTop: 4,
  },

  // ── Gauge slots
  slotBox: {
    overflow: "hidden",
    position: "absolute",
    top: 20,
    width: 250,
    height: 250,
    transform: [{ translateX: -125 }],
    borderRadius: 125,
  },
  slot1: {
    position: "absolute",
    top: 0,
    width: 250,
    height: 125,
    backgroundColor: "#e6e6e6",
  },
  slot2: {
    position: "absolute",
    top: 125,
    width: "100%",
    height: "100%",
    backgroundColor: "#6a9eff",
  },
  slot3: {
    position: "absolute",
    top: 40,
    left: -45,
    transform: [{ translateX: 85 }],
    width: 170,
    height: 170,
    borderRadius: 85,
  },
  slot4: {
    position: "absolute",
    top: 145,
    width: 290,
    height: 290,
    transform: [{ translateX: -20 }],
  },

  // ── Carousel wrapper
  carouselRoot: {
    height: 250,
    alignSelf: "stretch",
    marginBottom: 8,
    paddingHorizontal: 24,
    justifyContent: "center",
    alignItems: "center",
  },
  carouselSlide: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  carouselSlideText: { color: "#fff", fontSize: 28, fontWeight: "bold" },
  carouselDots: {
    position: "absolute",
    bottom: 0,
    flexDirection: "row",
    gap: 6,
  },
  carouselDot: {
    width: 6,
    height: 6,
    borderRadius: 4,
    backgroundColor: "#cfcfcf",
  },
  carouselDotActive: { backgroundColor: "#666" },

  // ── Link cards
  linkList: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    marginTop: 24,
  },
  cardBase: {
    flex: 1,
    height: 160,
    borderRadius: 16,
    paddingHorizontal: 20,
    paddingVertical: 16,
    alignItems: "center",
    justifyContent: "flex-end",
    overflow: "hidden",
  },
  cardTextLight: {
    width: "100%",
    color: "#fff",
    fontSize: 17,
    fontWeight: "600",
    textAlign: "right",
  },
});
