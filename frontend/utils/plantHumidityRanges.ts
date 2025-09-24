// 식물 품종별 최적 습도 범위 정의
export interface PlantHumidityRange {
  min: number;
  max: number;
  optimal: number;
  description: string;
}

// 식물 품종별 최적 습도 범위 매핑
export const PLANT_HUMIDITY_RANGES: Record<string, PlantHumidityRange> = {
  // 다육식물류
  선인장: { min: 10, max: 30, optimal: 20, description: "건조한 환경을 선호" },
  다육식물: {
    min: 15,
    max: 35,
    optimal: 25,
    description: "건조한 환경을 선호",
  },
  에케베리아: {
    min: 15,
    max: 35,
    optimal: 25,
    description: "건조한 환경을 선호",
  },
  하우스티아: {
    min: 15,
    max: 35,
    optimal: 25,
    description: "건조한 환경을 선호",
  },
  세덤: { min: 15, max: 35, optimal: 25, description: "건조한 환경을 선호" },
  크라슐라: {
    min: 15,
    max: 35,
    optimal: 25,
    description: "건조한 환경을 선호",
  },

  // 관엽식물류
  몬스테라: { min: 40, max: 70, optimal: 55, description: "적당한 습도 필요" },
  고무나무: { min: 40, max: 70, optimal: 55, description: "적당한 습도 필요" },
  스투키: { min: 30, max: 60, optimal: 45, description: "적당한 습도 필요" },
  산세베리아: {
    min: 30,
    max: 60,
    optimal: 45,
    description: "적당한 습도 필요",
  },
  필로덴드론: {
    min: 40,
    max: 70,
    optimal: 55,
    description: "적당한 습도 필요",
  },
  디펜바키아: {
    min: 40,
    max: 70,
    optimal: 55,
    description: "적당한 습도 필요",
  },
  칼라테아: { min: 50, max: 80, optimal: 65, description: "높은 습도 필요" },
  마란타: { min: 50, max: 80, optimal: 65, description: "높은 습도 필요" },
  피토니아: { min: 50, max: 80, optimal: 65, description: "높은 습도 필요" },
  아글라오네마: {
    min: 40,
    max: 70,
    optimal: 55,
    description: "적당한 습도 필요",
  },
  스파티필럼: {
    min: 40,
    max: 70,
    optimal: 55,
    description: "적당한 습도 필요",
  },
  안스리움: { min: 50, max: 80, optimal: 65, description: "높은 습도 필요" },

  // 허브류
  바질: { min: 40, max: 70, optimal: 55, description: "적당한 습도 필요" },
  로즈마리: { min: 30, max: 60, optimal: 45, description: "적당한 습도 필요" },
  민트: { min: 40, max: 70, optimal: 55, description: "적당한 습도 필요" },
  파슬리: { min: 40, max: 70, optimal: 55, description: "적당한 습도 필요" },
  타임: { min: 30, max: 60, optimal: 45, description: "적당한 습도 필요" },
  오레가노: { min: 30, max: 60, optimal: 45, description: "적당한 습도 필요" },

  // 꽃식물류
  장미: { min: 40, max: 70, optimal: 55, description: "적당한 습도 필요" },
  제라늄: { min: 30, max: 60, optimal: 45, description: "적당한 습도 필요" },
  베고니아: { min: 50, max: 80, optimal: 65, description: "높은 습도 필요" },
  시클라멘: { min: 40, max: 70, optimal: 55, description: "적당한 습도 필요" },
  포인세티아: {
    min: 40,
    max: 70,
    optimal: 55,
    description: "적당한 습도 필요",
  },
  히비스커스: {
    min: 40,
    max: 70,
    optimal: 55,
    description: "적당한 습도 필요",
  },

  // 과일나무류
  레몬: { min: 40, max: 70, optimal: 55, description: "적당한 습도 필요" },
  라임: { min: 40, max: 70, optimal: 55, description: "적당한 습도 필요" },
  오렌지: { min: 40, max: 70, optimal: 55, description: "적당한 습도 필요" },
  무화과: { min: 40, max: 70, optimal: 55, description: "적당한 습도 필요" },

  // 기타
  기본값: { min: 30, max: 70, optimal: 50, description: "일반적인 습도 범위" },
};

/**
 * 식물 품종에 따른 최적 습도 범위를 반환합니다.
 * @param species 식물 품종명
 * @returns 최적 습도 범위 정보
 */
export function getPlantHumidityRange(species?: string): PlantHumidityRange {
  if (!species) {
    return PLANT_HUMIDITY_RANGES["기본값"];
  }

  // 정확한 매칭 시도
  if (PLANT_HUMIDITY_RANGES[species]) {
    return PLANT_HUMIDITY_RANGES[species];
  }

  // 부분 매칭 시도 (품종명에 포함된 키워드로 검색)
  const speciesLower = species.toLowerCase();
  for (const [key, range] of Object.entries(PLANT_HUMIDITY_RANGES)) {
    if (
      speciesLower.includes(key.toLowerCase()) ||
      key.toLowerCase().includes(speciesLower)
    ) {
      return range;
    }
  }

  // 매칭되지 않으면 기본값 반환
  return PLANT_HUMIDITY_RANGES["기본값"];
}

/**
 * 현재 습도가 최적 범위 내에 있는지 확인합니다.
 * @param currentHumidity 현재 습도
 * @param range 최적 습도 범위
 * @returns 습도 상태 ("optimal" | "low" | "high" | "critical")
 */
export function getHumidityStatus(
  currentHumidity: number,
  range: PlantHumidityRange
): "optimal" | "low" | "high" | "critical" {
  if (currentHumidity >= range.min && currentHumidity <= range.max) {
    return "optimal";
  } else if (currentHumidity < range.min - 10) {
    return "critical";
  } else if (currentHumidity < range.min) {
    return "low";
  } else if (currentHumidity > range.max + 10) {
    return "critical";
  } else {
    return "high";
  }
}

/**
 * 습도 상태에 따른 색상을 반환합니다.
 * @param status 습도 상태
 * @returns 색상 코드
 */
export function getHumidityStatusColor(
  status: "optimal" | "low" | "high" | "critical"
): string {
  switch (status) {
    case "optimal":
      return "#4CAF50"; // 녹색
    case "low":
      return "#FF9800"; // 주황색
    case "high":
      return "#2196F3"; // 파란색
    case "critical":
      return "#F44336"; // 빨간색
    default:
      return "#9E9E9E"; // 회색
  }
}
