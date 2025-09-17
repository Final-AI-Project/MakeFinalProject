// app/(page)/_layout.tsx
import { Tabs } from "expo-router";
import { useColorScheme, View } from "react-native";
import Colors from "../../constants/Colors";
import BottomTabBar from "../../components/common/BottomTabBar";
import { useAuthGuard } from "../../hooks/useAuthGuard";

export default function PageLayout() {
  const scheme = useColorScheme();
  const theme = Colors[scheme === "dark" ? "dark" : "light"];

  // 인증 가드 적용 - 토큰이 없으면 로그인 페이지로 리다이렉트
  useAuthGuard();

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: { backgroundColor: theme.bg }, // 기존 배경 유지
      }}
      tabBar={(props) => <BottomTabBar {...props} />}
    >
      <Tabs.Screen name="home" options={{ title: "홈" }} />
      <Tabs.Screen name="medical" options={{ title: "의료" }} />
      <Tabs.Screen name="camera" options={{ title: "카메라" }} />
      <Tabs.Screen name="diary" options={{ title: "일기장" }} />
      <Tabs.Screen name="menu" options={{ title: "전체메뉴" }} />

      <Tabs.Screen
        name="(stackless)"
        options={{ href: null, headerShown: false }}
      />
    </Tabs>
  );
}
