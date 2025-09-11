// app/_layout.tsx
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { Slot } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { StyleSheet, useColorScheme } from "react-native";
import Colors from "../constants/Colors"; // ← 경로 확인

export default function RootLayout() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];

	return (
		<SafeAreaProvider>
			<SafeAreaView 
				edges={["top", "bottom"]} 
				style={[styles.layout, { backgroundColor: theme.background }]}
			>
				<StatusBar 
					style={theme.statusBarStyle}
					backgroundColor={theme.background} 
					translucent={false}
				/>
				<Slot />
			</SafeAreaView>
		</SafeAreaProvider>
	);
}

const styles = StyleSheet.create({
	layout: {
		flex:1,
        paddingTop: 5,
    }
});