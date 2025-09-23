// app/(page)/_layout.tsx
import { Tabs } from "expo-router";
import { useColorScheme, View } from "react-native";
import Colors from "../../constants/Colors";
import BottomTabBar from "../../components/common/BottomTabBar";
import { GlobalAlertHost } from "../../components/common/appAlert";
export default function PageLayout() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	return (
		<>
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
				<Tabs.Screen name="diaryList" options={{ title: "일기장" }} />
				<Tabs.Screen name="menu" options={{ title: "전체메뉴" }} />
				<Tabs.Screen
					name="(stackless)"
					options={{ href: null, headerShown: false }}
				/>
			</Tabs>
			<GlobalAlertHost />
		</>
	);
}
