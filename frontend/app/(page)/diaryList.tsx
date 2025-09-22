// app/(page)/diaryList.tsx
import React, { useMemo, useState, useEffect } from "react";
import { useFocusEffect } from "@react-navigation/native";
import { getApiUrl } from "../../config/api";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  Pressable,
  useColorScheme,
  Image,
  ActivityIndicator,
  Alert,
} from "react-native";
import { useRouter } from "expo-router";
import Colors from "../../constants/Colors";
import { Picker } from "@react-native-picker/picker";
import { getToken } from "../../libs/auth";

// ─────────────────────────────────────────────────────────────────────────────
// ① Types
// ─────────────────────────────────────────────────────────────────────────────
type Diary = {
  idx: number;
  user_title: string;
  user_content: string;
  plant_nickname?: string;
  plant_species?: string;
  plant_reply?: string; // AI 답변
  weather?: string;
  weather_icon?: string;
  img_url?: string;
  hashtag?: string;
  created_at: string;
  updated_at?: string;
};

// ─────────────────────────────────────────────────────────────────────────────
// ② Component
// ─────────────────────────────────────────────────────────────────────────────
export default function DiaryList() {
  const scheme = useColorScheme();
  const theme = Colors[scheme === "dark" ? "dark" : "light"];
  const router = useRouter();

  // 상태 관리
  const [diaries, setDiaries] = useState<Diary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 일기 목록 가져오기
  const fetchDiaries = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = await getToken();
      if (!token) {
        throw new Error("로그인이 필요합니다");
      }

      const apiUrl = getApiUrl("/diary-list");
      const response = await fetch(apiUrl, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(
          `일기 목록을 가져오는데 실패했습니다: ${response.status}`
        );
      }

      const data = await response.json();
      console.log("일기 목록 응답:", data);

      if (data.diaries && Array.isArray(data.diaries)) {
        setDiaries(data.diaries);
      } else {
        setDiaries([]);
      }
    } catch (err) {
      console.error("일기 목록 가져오기 오류:", err);
      setError(
        err instanceof Error
          ? err.message
          : "일기 목록을 가져오는데 실패했습니다"
      );
    } finally {
      setLoading(false);
    }
  };

  // 컴포넌트 마운트 시 일기 목록 가져오기 (즉시 새로고침)
  useEffect(() => {
    fetchDiaries();
  }, []);

  // 페이지 포커스 시 새로고침 (접속 시 + 일기 작성/수정/삭제 후 돌아올 때)
  useFocusEffect(
    React.useCallback(() => {
      fetchDiaries();
    }, [])
  );

  // 정렬 상태: "date" | "plant"
  const [sortBy, setSortBy] = useState<"date" | "plant">("date");

  // 간단 정렬 (날짜 ↔ 식물명)
  const data = useMemo(() => {
    const copy = [...diaries];
    if (sortBy === "date") {
      copy.sort((a, b) => (a.created_at < b.created_at ? 1 : -1)); // 최신 우선
    } else {
      copy.sort((a, b) =>
        (a.plant_nickname ?? "").localeCompare(b.plant_nickname ?? "")
      );
    }
    return copy;
  }, [diaries, sortBy]);

  // 항목 클릭 → 해당 일기 페이지로 이동
  // NOTE: 작성/상세 단일 페이지가 /(page)/diary 라는 전제
  const openDiary = (item: Diary) => {
    router.push({
      pathname: "/(page)/(stackless)/diary-edit",
      params: { id: item.idx.toString() },
    });
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      {/* 상단: 정렬 셀렉트 + 일기 쓰기 버튼 */}
      <View style={[styles.topBar, { backgroundColor: theme.bg }]}>
        <View
          style={[
            styles.leftSelect,
            { borderColor: theme.border, backgroundColor: theme.bg },
          ]}
        >
          <Picker
            selectedValue={sortBy}
            onValueChange={(v) => setSortBy(v as "date" | "plant")}
            mode="dropdown"
            dropdownIconColor={theme.text}
            style={[
              styles.picker,
              { color: theme.text, backgroundColor: theme.bg },
            ]}
          >
            <Picker.Item label="날짜별" value="date" />
            <Picker.Item label="식물별" value="plant" />
          </Picker>
        </View>

        <Pressable
          onPress={() => router.push("/(page)/diary")}
          style={[
            styles.writeBtn,
            { borderColor: theme.border, backgroundColor: theme.graybg },
          ]}
        >
          <Text style={[styles.writeBtnText, { color: theme.text }]}>
            일기 쓰기
          </Text>
        </Pressable>
      </View>

      {/* 로딩 상태 */}
      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.primary} />
          <Text style={[styles.loadingText, { color: theme.text }]}>
            일기 목록을 불러오는 중...
          </Text>
        </View>
      )}

      {/* 에러 상태 */}
      {error && (
        <View style={styles.errorContainer}>
          <Text style={[styles.errorText, { color: theme.text }]}>{error}</Text>
          <Pressable
            onPress={fetchDiaries}
            style={[styles.retryButton, { backgroundColor: theme.primary }]}
          >
            <Text style={styles.retryButtonText}>다시 시도</Text>
          </Pressable>
        </View>
      )}

      {/* 일기 목록 */}
      {!loading && !error && (
        <FlatList
          data={data}
          keyExtractor={(item) => item.idx.toString()}
          contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 120 }}
          renderItem={({ item }) => (
            <Pressable
              onPress={() => openDiary(item)}
              style={[
                styles.card,
                { borderColor: theme.border, backgroundColor: theme.bg },
              ]}
            >
              <View style={styles.cardRow}>
                {/* 썸네일 */}
                {item.img_url ? (
                  <Image
                    source={{
                      uri: item.img_url.startsWith("http")
                        ? item.img_url
                        : getApiUrl(item.img_url),
                    }}
                    style={styles.thumb}
                    resizeMode="cover"
                  />
                ) : (
                  <View
                    style={[
                      styles.thumb,
                      {
                        backgroundColor: theme.graybg,
                        alignItems: "center",
                        justifyContent: "center",
                      },
                    ]}
                  >
                    <Text
                      style={{ fontSize: 12, color: theme.text, opacity: 0.6 }}
                    >
                      No Image
                    </Text>
                  </View>
                )}

                {/* 내용 */}
                <View style={styles.cardBody}>
                  <Text
                    style={[styles.cardTitle, { color: theme.text }]}
                    numberOfLines={1}
                    ellipsizeMode="tail"
                  >
                    {item.user_title}
                  </Text>

                  <Text
                    style={[
                      styles.cardMeta,
                      { color: theme.text, opacity: 0.7 },
                    ]}
                    numberOfLines={1}
                  >
                    {[
                      item.plant_nickname,
                      item.plant_species,
                      item.created_at
                        ? (() => {
                            try {
                              const date = new Date(item.created_at);
                              // 유효한 날짜인지 확인
                              if (isNaN(date.getTime())) {
                                return "날짜 없음";
                              }
                              return date.toLocaleDateString("ko-KR");
                            } catch (error) {
                              console.error(
                                "날짜 파싱 오류:",
                                error,
                                item.created_at
                              );
                              return "날짜 없음";
                            }
                          })()
                        : "날짜 없음",
                    ]
                      .filter(Boolean)
                      .join(" · ")}
                  </Text>

                  {Boolean(item.user_content) && (
                    <Text
                      style={[
                        styles.cardContent,
                        { color: theme.text, opacity: 0.9 },
                      ]}
                      numberOfLines={2}
                      ellipsizeMode="tail"
                    >
                      {item.user_content}
                    </Text>
                  )}
                </View>
              </View>
            </Pressable>
          )}
          ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
          ListEmptyComponent={() => (
            <View style={styles.emptyContainer}>
              <Text style={[styles.emptyText, { color: theme.text }]}>
                아직 작성된 일기가 없습니다.
              </Text>
              <Text
                style={[
                  styles.emptySubText,
                  { color: theme.text, opacity: 0.7 },
                ]}
              >
                첫 번째 일기를 작성해보세요!
              </Text>
            </View>
          )}
        />
      )}

      {/* 우하단 원형 버튼 (타임 랩스 만들기) */}
      <Pressable
        onPress={() => {
          // TODO: 타임랩스 생성 페이지 경로로 교체
          // 예) router.push("/(page)/timelapse");
        }}
        style={[
          styles.fab,
          {
            borderColor: theme.border,
            backgroundColor: theme.bg,
          },
        ]}
      >
        <Text style={[styles.fabText, { color: theme.text }]}>
          타임 랩스{"\n"}만들기
        </Text>
      </Pressable>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ③ Styles
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1 },

  // 상단 바: 좌측 셀렉트, 우측 "일기 쓰기" 버튼
  topBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
    gap: 12,
  },
  leftSelect: {
    flex: 1,
    paddingVertical: 0,
    borderWidth: 1,
    borderRadius: 10,
    overflow: "hidden",
    height: 40,
    justifyContent: "center",
  },
  picker: {
    width: "100%",
    paddingVertical: 0,
  },
  writeBtn: {
    paddingHorizontal: 14,
    height: 40,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  writeBtnText: {
    fontSize: 14,
    fontWeight: "700",
  },

  // 카드
  card: {
    minHeight: 72,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  cardRow: {
    flexDirection: "row",
    gap: 12,
  },
  thumb: {
    width: 56,
    height: 56,
    borderRadius: 10,
    overflow: "hidden",
  },
  cardBody: {
    flex: 1,
    minHeight: 56,
    justifyContent: "center",
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: "800",
    marginBottom: 2,
  },
  cardMeta: {
    fontSize: 12,
    marginBottom: 6,
  },
  cardContent: {
    fontSize: 13,
    lineHeight: 18,
  },

  // FAB
  fab: {
    position: "absolute",
    right: 16,
    bottom: 90,
    width: 75,
    height: 75,
    borderRadius: 999,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
    // 살짝 그림자
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 3 },
    elevation: 6,
  },
  fabText: {
    fontSize: 13,
    textAlign: "center",
    fontWeight: "600",
    lineHeight: 18,
  },

  // 로딩, 에러, 빈 상태
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 32,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    textAlign: "center",
  },
  errorContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 32,
  },
  errorText: {
    fontSize: 16,
    textAlign: "center",
    marginBottom: 16,
  },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: "white",
    fontSize: 16,
    fontWeight: "600",
  },
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 32,
    paddingVertical: 64,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: "600",
    textAlign: "center",
    marginBottom: 8,
  },
  emptySubText: {
    fontSize: 14,
    textAlign: "center",
  },
});
