// app/_layout.tsx
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { Slot, useSegments, useRootNavigationState } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { StyleSheet} from "react-native";
import { useColorScheme } from "react-native";

export default function RootLayout() {
	const scheme = useColorScheme();
	const dark = scheme === "dark";

	return (
		<SafeAreaProvider>
			<SafeAreaView 
				edges={["top", "bottom"]} 
				style={styles.layout}
			>
				<StatusBar 
					style={dark  ? "light" : "dark"} 
					backgroundColor={dark ? "#000000" : "#fafafa"} 
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
		backgroundColor:'#fafafa',
        paddingTop: 5,
    }
});