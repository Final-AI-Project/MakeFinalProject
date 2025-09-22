// config/api.ts
// API 관련 설정을 중앙화하는 파일

import Constants from "expo-constants";
import { Platform } from "react-native";

// ─────────────────────────────────────────────────────────────────────────────
// 1) BASE_URL 해석 (ENV → app.config.ts extra → 합리적 기본값)
// ─────────────────────────────────────────────────────────────────────────────
function resolveDefaultBaseUrl(): string {
	// 1순위: .env 파일의 EXPO_PUBLIC_API_BASE_URL
	const envUrl = process.env.EXPO_PUBLIC_API_BASE_URL?.trim();
	if (envUrl) return envUrl;

	// 2순위: app.config.ts의 extra.API_BASE_URL
	const extraUrl = ((Constants.expoConfig?.extra as any)?.API_BASE_URL as string | undefined)?.trim();
	if (extraUrl) return extraUrl;

	// 3순위: 개발 기본값 (fallback)
	const host = Platform.OS === "android" ? "10.0.2.2" : "localhost";
	return `http://${host}:3000`;
}

export const API_BASE_URL = resolveDefaultBaseUrl();

// ─────────────────────────────────────────────────────────────────────────────
// 2) 엔드포인트
// ─────────────────────────────────────────────────────────────────────────────
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
		DELETE: (plantId: number) => `/plants/${plantId}`,
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

// ─────────────────────────────────────────────────────────────────────────────
// 3) URL 헬퍼
// ─────────────────────────────────────────────────────────────────────────────
export const createApiUrl = (endpoint: string): string => {
	// Base URL 끝의 슬래시와 endpoint 시작의 슬래시 중복 제거
	const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
	const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
	return `${baseUrl}${cleanEndpoint}`;
};

// 디버깅용: 여러 포트 시도 (외부 환경 고려)
export const POSSIBLE_PORTS = [3000, 8000, 5000, 8080, 8001, 9000, 4000];

function getOriginParts(baseUrl: string) {
	try {
		const u = new URL(baseUrl);
		return {
			protocol: u.protocol.replace(":", "") || "http",
			host: u.hostname, // ← IP/도메인만
		};
	} catch {
		// baseUrl이 이상해도 최소 동작
		return { protocol: "http", host: "localhost" };
	}
}

// 서버 연결 테스트 함수(하드코딩 제거: BASE_URL의 host/protocol 기준으로만 포트 바꿈)
export const findWorkingPort = async (): Promise<number | null> => {
	console.log("[api] Testing server connection...");

	const { protocol, host } = getOriginParts(API_BASE_URL);

	for (const port of POSSIBLE_PORTS) {
		const testUrl = `${protocol}://${host}:${port}${API_ENDPOINTS.HEALTH.CHECK}`;
		try {
			const res = await fetch(testUrl, { method: "GET" });
			console.log(`[api] Try ${testUrl} → ${res.status}`);
			if (res.ok) return port;
		} catch (e: any) {
			console.log(`[api] FAIL ${testUrl} →`, e?.message || e);
		}
	}
	return null;
};

// 동적 API URL 생성 함수
export const getApiUrl = async (endpoint: string): Promise<string> => {
	// ENV나 extra로 지정되어 있으면 그대로 사용
	if (process.env.EXPO_PUBLIC_API_BASE_URL || (Constants.expoConfig?.extra as any)?.API_BASE_URL) {
		return createApiUrl(endpoint);
	}

	// 로컬 개발: 포트 탐색
	const workingPort = await findWorkingPort();
	if (!workingPort) {
		throw new Error("모든 포트에서 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.");
	}

	const { protocol, host } = getOriginParts(API_BASE_URL);
	return `${protocol}://${host}:${workingPort}${endpoint}`;
};
