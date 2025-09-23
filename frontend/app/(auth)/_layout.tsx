// 수정후: app/(auth)/_layout.tsx
import { Stack } from "expo-router";
import { useColorScheme } from "react-native";
import Colors from "../../constants/Colors";
import { GlobalAlertHost } from "../../components/common/appAlert";

export default function AuthLayout() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	return (
		<>
			<Stack
				screenOptions={{
					headerShown: false,
					contentStyle: { backgroundColor: theme.bg },
				}}
			/>
			<GlobalAlertHost /> {/* ← (auth) 트리에도 장착 */}
		</>
	);
}
