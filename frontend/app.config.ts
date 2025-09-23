// /app.config.ts
import "dotenv/config";
import { ExpoConfig } from "@expo/config";

const config: ExpoConfig = {
	name: "Pland",
	slug: "pland",
	android: {
		package: "com.anonymous.pland",
		usesCleartextTraffic: true,
	},
	ios: {
		bundleIdentifier: "com.anonymous.pland",
		infoPlist: {
			NSAppTransportSecurity: {
				NSAllowsArbitraryLoads: true,
			},
		},
	},
	extra: {
		API_BASE_URL: process.env.EXPO_PUBLIC_API_BASE_URL,
	},
};

export default config;
