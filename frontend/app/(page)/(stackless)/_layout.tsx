import { Stack } from "expo-router";
import Colors from "../../../constants/Colors";

export default function StacklessLayout() {
	return (
		<Stack
			screenOptions={{
				headerShown: false,
				headerBackVisible: false,
				headerLeft: () => null,
				gestureEnabled: false,
			}}
		/>
	);
}
