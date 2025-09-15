import React from "react";
import { View, Text, TouchableOpacity, StyleSheet, Platform } from "react-native";
import { BottomTabBarProps } from "@react-navigation/bottom-tabs";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { useColorScheme } from "react-native";
import Colors from "../../constants/Colors";

type RouteKey = "home" | "camera" | "diary";

const ICONS: Record<RouteKey, { active: keyof typeof Ionicons.glyphMap; inactive: keyof typeof Ionicons.glyphMap }> = {
	home:	 { active: "home",		inactive: "home-outline" },
	camera: { active: "camera",	inactive: "camera-outline" },
	diary:	{ active: "create",	inactive: "create-outline" },
};

export default function BottomTabBar({ state, descriptors, navigation }: BottomTabBarProps) {
	const insets = useSafeAreaInsets();
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];

	const onPress = (index: number) => {
		const route = state.routes[index];
		const event = navigation.emit({ type: "tabPress", target: route.key, canPreventDefault: true });
		if (!event.defaultPrevented) navigation.navigate(route.name);
	};

	return (
		<View pointerEvents="box-none" style={[styles.wrap, { paddingBottom: Math.max(insets.bottom, 8) }]}>
			<View
				style={[
					styles.bar,
					{
						backgroundColor: theme.bg,
						shadowColor: scheme === "dark" ? "#000" : "#777",
					},
				]}
			>
				{state.routes.map((route, index) => {
					const isFocused = state.index === index;
					const options = descriptors[route.key].options;
					const label =
						(options.tabBarLabel as string) ??
						options.title ??
						(route.name.charAt(0).toUpperCase() + route.name.slice(1));
					const key = route.name.toLowerCase() as RouteKey;

					const color = isFocused ? theme.primary : "#9aa0a6";
					const iconName = isFocused ? ICONS[key]?.active : ICONS[key]?.inactive;

					// 가운데 카메라 탭을 FAB처럼 강조
					const isFab = key === "camera";

					return (
						<TouchableOpacity
							key={route.key}
							accessibilityRole="button"
							accessibilityState={isFocused ? { selected: true } : {}}
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
											shadowColor: scheme === "dark" ? "#000" : theme.primary,
										},
									]}
								>
									<Ionicons name={iconName || "camera-outline"} size={26} color="#fff" />
								</View>
							) : (
								<View style={styles.pill}>
									<Ionicons name={iconName || "ellipse-outline"} size={22} color={color} />
									<Text style={[styles.label, { color }]} numberOfLines={1}>{label}</Text>
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
		position: "absolute",
		left: 0, right: 0, bottom: 0,
		alignItems: "center",
	},
	bar: {
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "space-between",
		gap: 8,
		paddingHorizontal: 12,
		height: 68,
		borderRadius: 24,
		width: "92%",
		...Platform.select({
			ios:		 { shadowOpacity: 0.15, shadowRadius: 14, shadowOffset: { width: 0, height: 8 } },
			android: { elevation: 12 },
		}),
	},
	tabBtn: {
		flex: 1,
		height: "100%",
		alignItems: "center",
		justifyContent: "center",
	},
	pill: {
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "center",
		gap: 6,
		borderRadius: 999,
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
		width: 56, height: 56, borderRadius: 28,
		alignItems: "center", justifyContent: "center",
		marginTop: -18, // 살짝 떠보이게
		...Platform.select({
			ios:	 { shadowOpacity: 0.25, shadowRadius: 12, shadowOffset: { width: 0, height: 10 } },
			android: { elevation: 16 },
		}),
	},
});
