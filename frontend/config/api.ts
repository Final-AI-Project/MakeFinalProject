// config/api.ts
// API 관련 설정을 중앙화하는 파일

// 서버 주소를 환경에 맞게 설정
export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:3000";

// 디버깅용: 여러 포트 시도 (외부 환경 고려)
export const POSSIBLE_PORTS = [3000, 5000, 8080, 8000, 8001, 9000, 4000];

// API 엔드포인트들
export const API_ENDPOINTS = {
  // 인증 관련
  AUTH: {
    LOGIN: "/auth/login",
    SIGNUP: "/auth/signup",
    LOGOUT: "/auth/logout",
  },

  // 식물 관련
  PLANTS: {
    LIST: "/plants",
    CREATE: "/plants",
    GET: (plantId: number) => `/plants/${plantId}`,
    UPDATE: (plantId: number) => `/plants/${plantId}`,
  },

  // 식물 정보 관련
  PLANT_INFO: {
    TIPS: "/plant-info/tips",
    SPECIES: "/plant-info/species",
    GROWTH: "/plant-info/growth",
    GET: (idx: number) => `/plant-info/${idx}`,
    GET_BY_SPECIES: (species: string) => `/plant-info/species/${species}`,
  },

  // AI 관련
  AI: {
    CLASSIFY: "/ai/classify",
    DIAGNOSE: "/ai/diagnose",
  },

  // 이미지 관련
  IMAGES: {
    UPLOAD: "/images/upload",
    GET: (imageId: string) => `/images/${imageId}`,
  },

  // 헬스체크
  HEALTH: {
    CHECK: "/healthcheck",
    DB: "/health/db",
  },
} as const;

// API 요청 헬퍼 함수
export const createApiUrl = (endpoint: string): string => {
  return `${API_BASE_URL}${endpoint}`;
};

// 서버 연결 테스트 함수
export const findWorkingPort = async (): Promise<number | null> => {
  console.log("Testing server connection...");

  for (const port of POSSIBLE_PORTS) {
    try {
      const testUrl = `http://localhost:${port}/healthcheck`;
      console.log(`Trying port ${port}: ${testUrl}`);

      const testRes = await fetch(testUrl, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        mode: "cors",
      });

      console.log(`Port ${port} - Status:`, testRes.status);

      if (testRes.ok) {
        console.log(`Working port found: ${port}`);
        return port;
      }
    } catch (testError: any) {
      console.log(`Port ${port} failed:`, testError?.message || testError);
    }
  }

  return null;
};

// 동적 API URL 생성 함수
export const getApiUrl = async (endpoint: string): Promise<string> => {
  // 환경변수로 설정된 URL이 있으면 그대로 사용
  if (process.env.EXPO_PUBLIC_API_BASE_URL) {
    return createApiUrl(endpoint);
  }

  // 로컬 개발 환경에서는 동적으로 포트 찾기
  const workingPort = await findWorkingPort();

  if (!workingPort) {
    throw new Error(
      "모든 포트에서 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요."
    );
  }

  return `http://localhost:${workingPort}${endpoint}`;
};
