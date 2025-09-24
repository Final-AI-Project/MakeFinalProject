import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  useColorScheme,
} from "react-native";
import Colors from "../../constants/Colors";
import { getApiUrl } from "../../config/api";
import { getToken } from "../../libs/auth";
import { showAlert } from "../../components/common/appAlert";
import { WateringPredictionResponse } from "../../types/watering";

interface WateringPredictionBoxProps {
  plantIdx: number;
  currentHumidity: number;
  temperature?: number;
  onPredictionUpdate?: (prediction: WateringPredictionResponse) => void;
}

// 날씨 정보를 가져오는 함수
const getCurrentWeather = async (): Promise<number> => {
  try {
    // 공공데이터포털 KMA API를 사용하여 현재 온도 가져오기
    const serviceKey =
      "GTr1cI7Wi0FRbOTFBaUzUCzCDP4OnyyEmHnn11pxCUC5ehG5bQnbyztgeydnOWz1O04tjw1SE5RsX8RNo6XCgQ==";
    const baseDate = new Date().toISOString().slice(0, 10).replace(/-/g, "");
    const baseTime = "0500"; // 5시 기준 (실시간 데이터)

    const url = `https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst?serviceKey=${encodeURIComponent(
      serviceKey
    )}&numOfRows=10&pageNo=1&base_date=${baseDate}&base_time=${baseTime}&nx=61&ny=125&dataType=JSON`;

    const response = await fetch(url);
    const data = await response.json();

    if (
      data.response?.header?.resultCode === "00" &&
      data.response?.body?.items?.item
    ) {
      const items = data.response.body.items.item;
      const tempItem = items.find((item: any) => item.category === "TMP");
      if (tempItem) {
        return parseFloat(tempItem.fcstValue);
      }
    }

    // API 실패 시 기본값 반환
    return 20;
  } catch (error) {
    console.error("날씨 정보 가져오기 실패:", error);
    return 20; // 기본값
  }
};

export default function WateringPredictionBox({
  plantIdx,
  currentHumidity,
  temperature = 20,
  onPredictionUpdate,
}: WateringPredictionBoxProps) {
  const scheme = useColorScheme();
  const theme = Colors[scheme === "dark" ? "dark" : "light"];

  const [prediction, setPrediction] =
    useState<WateringPredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 급수 예측 API 호출
  const fetchWateringPrediction = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = await getToken();
      if (!token) {
        throw new Error("인증 토큰이 없습니다.");
      }

      // 현재 날씨 정보 가져오기
      const currentTemperature = await getCurrentWeather();

      const currentTime = new Date();
      const hourOfDay = currentTime.getHours() + currentTime.getMinutes() / 60;

      const requestData = {
        plant_idx: plantIdx,
        current_humidity: currentHumidity,
        temperature: currentTemperature,
        hour_of_day: hourOfDay,
      };

      const apiUrl = getApiUrl(`/plant-detail/${plantIdx}/watering-prediction`);
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: WateringPredictionResponse = await response.json();
      setPrediction(data);

      if (onPredictionUpdate) {
        onPredictionUpdate(data);
      }
    } catch (error) {
      console.error("급수 예측 오류:", error);
      setError("급수 예측을 불러올 수 없습니다.");
      showAlert({
        title: "오류",
        message: "급수 예측을 불러오는데 실패했습니다.",
        buttons: [{ text: "확인" }],
      });
    } finally {
      setLoading(false);
    }
  };

  // 컴포넌트 마운트 시 예측 실행
  useEffect(() => {
    if (plantIdx && currentHumidity !== undefined) {
      fetchWateringPrediction();
    }
  }, [plantIdx, currentHumidity, temperature]);

  // 날짜 형식 변환 함수
  const formatPredictionDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = date.getTime() - now.getTime();
      const diffHours = Math.round(diffMs / (1000 * 60 * 60));

      if (diffHours < 24) {
        return `${diffHours}시간 후`;
      } else {
        const diffDays = Math.round(diffHours / 24);
        return `${diffDays}일 후`;
      }
    } catch {
      return dateString;
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: theme.text }]}>💧 급수 예측</Text>
      </View>

      {loading && !prediction ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.primary} />
          <Text style={[styles.loadingText, { color: theme.text }]}>
            급수 예측 중...
          </Text>
        </View>
      ) : error ? (
        <View style={styles.errorContainer}>
          <Text style={[styles.errorText, { color: theme.text }]}>{error}</Text>
          <TouchableOpacity
            style={[styles.retryButton, { backgroundColor: theme.primary }]}
            onPress={fetchWateringPrediction}
          >
            <Text style={styles.retryButtonText}>다시 시도</Text>
          </TouchableOpacity>
        </View>
      ) : prediction ? (
        <View style={styles.predictionContainer}>
          <View style={styles.predictionRow}>
            <Text style={[styles.label, { color: theme.text }]}>
              현재 습도:
            </Text>
            <Text style={[styles.value, { color: theme.primary }]}>
              {prediction.current_humidity.toFixed(1)}%
            </Text>
          </View>

          <View style={styles.predictionRow}>
            <Text style={[styles.label, { color: theme.text }]}>
              예상 시간:
            </Text>
            <Text style={[styles.value, { color: theme.primary }]}>
              {prediction.predicted_hours.toFixed(1)}시간
            </Text>
          </View>

          <View style={styles.predictionRow}>
            <Text style={[styles.label, { color: theme.text }]}>
              다음 급수:
            </Text>
            <Text style={[styles.value, { color: theme.primary }]}>
              {formatPredictionDate(prediction.next_watering_date)}
            </Text>
          </View>

          <View style={styles.detailContainer}>
            <Text style={[styles.detailText, { color: theme.text }]}>
              {prediction.message}
            </Text>
          </View>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginVertical: 8,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#e0e0e0",
    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: "bold",
  },
  loadingContainer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 20,
  },
  loadingText: {
    marginLeft: 8,
    fontSize: 14,
  },
  errorContainer: {
    alignItems: "center",
    paddingVertical: 20,
  },
  errorText: {
    fontSize: 14,
    marginBottom: 12,
    textAlign: "center",
  },
  retryButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  retryButtonText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "500",
  },
  predictionContainer: {
    gap: 8,
  },
  predictionRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  label: {
    fontSize: 14,
    fontWeight: "500",
  },
  value: {
    fontSize: 14,
    fontWeight: "bold",
  },
  detailContainer: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#e0e0e0",
  },
  detailText: {
    fontSize: 12,
    textAlign: "center",
    fontStyle: "italic",
  },
});
