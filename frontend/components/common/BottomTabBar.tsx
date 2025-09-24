// app/components/common/BottomTabBar.tsx
import React from "react";
import { View, TouchableOpacity, StyleSheet, Platform } from "react-native";
import { BottomTabBarProps } from "@react-navigation/bottom-tabs";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { useColorScheme } from "react-native";
import Colors from "../../constants/Colors";
type RouteKey = "home" | "camera" | "diaryList" | "menu" | "medical";
const ICONS: Record<
	RouteKey,
	{
		active: keyof typeof Ionicons.glyphMap;
		inactive: keyof typeof Ionicons.glyphMap;
	}
> = {
	home: { active: "home", inactive: "home-outline" },
	medical: { active: "medkit", inactive: "medkit-outline" },
	camera: { active: "camera", inactive: "camera-outline" },
	diaryList: { active: "create", inactive: "create-outline" },
	menu: { active: "grid", inactive: "grid-outline" },
};
export default function BottomTabBar({
	state,
	descriptors,
	navigation,
}: BottomTabBarProps) {
	const insets = useSafeAreaInsets();
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const activeRoute = state.routes[state.index];
	const activeOpts = descriptors[activeRoute.key]?.options ?? {};
	const shouldHideBar =
		activeRoute.name.startsWith("(") ||
		((activeOpts as any)?.tabBarStyle &&
			(activeOpts as any).tabBarStyle.display === "none");
	if (shouldHideBar) return null;
	const visibleRoutes = state.routes.filter((route) => {
		const opts = descriptors[route.key]?.options ?? {};
		return !(route.name.startsWith("(") || (opts as any).href === null);
	});
	const onPress = (index: number) => {
		const route = state.routes[index];
		const event = navigation.emit({
			type: "tabPress",
			target: route.key,
			canPreventDefault: true,
		});
		if (!event.defaultPrevented) navigation.navigate(route.name);
	};
	return (
		<View pointerEvents="box-none" style={styles.wrap}>
			<View style={[styles.bar, { backgroundColor: theme.bg }]}>
				{visibleRoutes.map((route, index) => {
					const isFocused = state.index === index;
					const options = descriptors[route.key].options;
					const label =
						(options.tabBarLabel as string) ??
						options.title ??
						route.name.charAt(0).toUpperCase() + route.name.slice(1);
					const key = (route.name as RouteKey) || "home";
					const color = isFocused ? theme.primary : "#9AA0A6";
					const iconName = isFocused
						? ICONS[key]?.active
						: ICONS[key]?.inactive;
					const isFab = key === "camera";
					return (
						<TouchableOpacity
							key={route.key}
							accessibilityRole="button"
							accessibilityState={isFocused ? { selected: true } : {}}
							accessibilityLabel={label}
							onPress={() => onPress(index)}
							style={[styles.tabBtn, isFab && styles.fabSlot]}
							activeOpacity={0.9}
						>
							{isFab ? (
								<View
									style={[
										styles.fab,
										{
											backgroundColor: theme.primary,
										},
									]}
								>
									<Ionicons
										name={iconName || "camera-outline"}
										size={26}
										color="#fff"
									/>
								</View>
							) : (
								<View style={styles.pill}>
									<Ionicons
										name={iconName || "ellipse-outline"}
										size={22}
										color={color}
									/>
								</View>
							)}
						</TouchableOpacity>
					);
				})}
			</View>
		</View>
	);
}
const styles = StyleSheet.create({
	wrap: {
		alignItems: "center",
		bottom: 0,
		left: 0,
		right: 0,
		position: "absolute",
	},
	bar: {
		alignItems: "center",
		flexDirection: "row",
		gap: 8,
		height: 68,
		justifyContent: "space-between",
		paddingHorizontal: 24,
		...Platform.select({
			ios: {
				shadowOpacity: 0.15,
				shadowRadius: 14,
				shadowOffset: { width: 0, height: 8 },
			},
			android: { elevation: 12 },
		}),
	},
	tabBtn: {
		alignItems: "center",
		flex: 1,
		height: "100%",
		justifyContent: "center",
	},
	pill: {
		alignItems: "center",
		borderRadius: 999,
		flexDirection: "row",
		gap: 6,
		justifyContent: "center",
		paddingHorizontal: 12,
		paddingVertical: 8,
	},
	label: {
		fontSize: 12,
		fontWeight: "600",
	},
	fabSlot: {
		flex: 1,
	},
	fab: {
		alignItems: "center",
		borderRadius: 28,
		height: 56,
		justifyContent: "center",
		marginTop: -18,
		width: 56,
	},
});
