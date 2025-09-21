// lib/auth.ts
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";
import { getApiUrl } from "../config/api";

const TOKEN_KEY = "authorization";
const REFRESH_TOKEN_KEY = "refresh_token";

// 웹 환경에서는 localStorage 사용, 모바일에서는 SecureStore 사용
const isWeb = Platform.OS === "web";

export async function getToken(): Promise<string | null> {
  try {
    if (isWeb) {
      return localStorage.getItem(TOKEN_KEY);
    } else {
      return await SecureStore.getItemAsync(TOKEN_KEY);
    }
  } catch {
    return null;
  }
}

export async function setToken(token: string) {
  if (isWeb) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    await SecureStore.setItemAsync(TOKEN_KEY, token);
  }
}

export async function clearToken() {
  if (isWeb) {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  } else {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
  }
}

export async function getRefreshToken(): Promise<string | null> {
  try {
    if (isWeb) {
      return localStorage.getItem(REFRESH_TOKEN_KEY);
    } else {
      return await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
    }
  } catch {
    return null;
  }
}

export async function setRefreshToken(token: string) {
  if (isWeb) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  } else {
    await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, token);
  }
}

export async function refreshToken(): Promise<string | null> {
  try {
    const refreshToken = await getRefreshToken();
    if (!refreshToken) {
      console.log("🔄 리프레시 토큰이 없습니다.");
      return null;
    }

    const apiUrl = getApiUrl("/auth/refresh");
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      console.log("🔄 토큰 갱신 실패:", response.status);
      await clearToken();
      return null;
    }

    const data = await response.json();
    await setToken(data.access_token);
    await setRefreshToken(data.refresh_token);

    console.log("🔄 토큰 갱신 성공");
    return data.access_token;
  } catch (error) {
    console.log("🔄 토큰 갱신 오류:", error);
    await clearToken();
    return null;
  }
}
