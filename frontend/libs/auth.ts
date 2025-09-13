// lib/auth.ts
import * as SecureStore from "expo-secure-store";

const TOKEN_KEY = "authorization";

export async function getToken(): Promise<string | null> {
    try {
        return await SecureStore.getItemAsync(TOKEN_KEY);
    } catch {
        return null;
    }
}

export async function setToken(token: string) {
    await SecureStore.setItemAsync(TOKEN_KEY, token);
}

export async function clearToken() {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
}