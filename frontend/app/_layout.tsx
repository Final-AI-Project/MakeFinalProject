// app/_layout.tsx
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { Slot } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { StyleSheet, useColorScheme } from "react-native";
import Colors from "../constants/Colors";

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
				<Slot />
			</SafeAreaView>
		</SafeAreaProvider>
	);
}

const styles = StyleSheet.create({
	layout: {
		flex:1,
        paddingTop: 5,
		paddingHorizontal: 24,
		paddingBottom: 50,
    }
});