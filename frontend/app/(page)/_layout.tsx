// app/(page)/_layout.tsx
import { Tabs } from "expo-router";
import { useColorScheme, View } from "react-native";
import Colors from "../../constants/Colors";
import BottomTabBar from "../../components/common/BottomTabBar";

export default function PageLayout() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];

	return (
		<View style={{ flex: 1, backgroundColor: theme.bg }}>
			<Tabs
				screenOptions={{ headerShown: false }}
				tabBar={(props) => <BottomTabBar {...props} />}
			>
				<Tabs.Screen name="home" options={{ title: "홈" }} />
				<Tabs.Screen name="medical" options={{ title: "의료" }} />
				<Tabs.Screen name="camera" options={{ title: "카메라" }} />
				<Tabs.Screen name="diary" options={{ title: "일기장" }} />
				<Tabs.Screen name="menu" options={{ title: "전체메뉴" }} />
			</Tabs>
		</View>
	);
}
