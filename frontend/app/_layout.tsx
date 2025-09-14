// app/_layout.tsx
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { StyleSheet, useColorScheme } from "react-native";
import Colors from "../constants/Colors";
import { GlobalLoadingHost } from "./common/loading";   // ✅ 추가

export default function RootLayout() {
  const scheme = useColorScheme();
  const theme = Colors[scheme === "dark" ? "dark" : "light"];

	return (
		<SafeAreaProvider>
			<SafeAreaView
				edges={["top", "bottom"]}
				style={[styles.layout, { backgroundColor: theme.bg }]}
			>
				<StatusBar
					style={theme.statusBarStyle}
					backgroundColor={theme.bg}
					translucent={false}
				/>
				<Stack
					screenOptions={{
						headerShown: false,
						// 각 화면의 배경은 투명 처리 → 바깥 SafeAreaView의 배경/패딩이 그대로 적용됨
						contentStyle: { backgroundColor: "transparent" },
					}}
				/>
			</SafeAreaView>
		</SafeAreaProvider>
	);
}

const styles = StyleSheet.create({
  layout: {
    flex: 1,
    paddingTop: 5,
    paddingHorizontal: 24,
  },
});
