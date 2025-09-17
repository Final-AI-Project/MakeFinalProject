import { Stack } from "expo-router";
import Colors from "../../../constants/Colors";
import { useAuthGuard } from "../../../hooks/useAuthGuard";

export default function StacklessLayout() {
  // 인증 가드 적용 - 토큰이 없으면 로그인 페이지로 리다이렉트
  useAuthGuard();

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        headerBackVisible: false,
        headerLeft: () => null,
        gestureEnabled: false,
      }}
    />
  );
}
