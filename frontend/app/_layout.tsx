// app/_layout.tsx
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { Slot, useSegments, useRootNavigationState } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { StyleSheet} from "react-native";

export default function RootLayout() {
	const segments = useSegments(); // ['(tab)', 'index'] 같은 배열
	const navState = useRootNavigationState();

	const group = navState?.key ? segments?.[0] : null;
    const isPublic = group === "(public)";

	return (
		<SafeAreaProvider>
			<SafeAreaView 
				edges={["top", "bottom"]} 
				style={styles.layout}
			>
				<StatusBar style={isPublic ? "light" : "dark"} backgroundColor={isPublic ? "#fafafa" : "#000000"} translucent={false} />
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