// config/api.ts
// API 관련 설정을 중앙화하는 파일

import { Platform } from "react-native";

// ─────────────────────────────────────────────────────────────────────────────
// 1) BASE_URL 해석 (ENV → 합리적 기본값)
// ─────────────────────────────────────────────────────────────────────────────
function resolveDefaultBaseUrl(): string {
	// 1순위: .env 파일의 EXPO_PUBLIC_API_BASE_URL
	const envUrl = process.env.EXPO_PUBLIC_API_BASE_URL?.trim();
	console.log("🔧 EXPO_PUBLIC_API_BASE_URL:", envUrl);

	if (envUrl) {
		// http://가 없으면 자동으로 추가
		const finalUrl = envUrl.startsWith("http") ? envUrl : `http://${envUrl}`;
		console.log("✅ .env에서 URL 사용:", finalUrl);
		return finalUrl;
	}

	// 2순위: 개발 기본값 (fallback)
	const host = Platform.OS === "android" ? "10.0.2.2" : "localhost";
	const fallbackUrl = `http://${host}:3000`;
	console.log("⚠️ fallback URL 사용:", fallbackUrl);
	return fallbackUrl;
}

export const API_BASE_URL = resolveDefaultBaseUrl();
console.log("🚀 최종 API_BASE_URL:", API_BASE_URL);

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
    	CLASSIFY: "/plants/classify-species", // ← 여기를 실제 서버 라우트로 고정
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
	const baseUrl = API_BASE_URL.endsWith("/")
		? API_BASE_URL.slice(0, -1)
		: API_BASE_URL;
	const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
	return `${baseUrl}${cleanEndpoint}`;
};

// 동기 API URL 생성 함수
export const getApiUrl = (endpoint: string): string => {
	return createApiUrl(endpoint);
};
