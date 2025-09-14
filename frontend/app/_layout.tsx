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
				<StatusBar style={theme.statusBarStyle} />
				<Stack
					screenOptions={{
						headerShown: false,
						contentStyle: { backgroundColor: "transparent" },
					}}
				/>
				{/* ✅ 전역 딤 로딩 모달 호스트 */}
				<GlobalLoadingHost />
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
