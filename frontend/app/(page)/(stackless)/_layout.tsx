import { Stack } from "expo-router";

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
