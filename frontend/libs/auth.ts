// lib/auth.ts
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

const TOKEN_KEY = "authorization";

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
    } else {
        await SecureStore.deleteItemAsync(TOKEN_KEY);
    }
}