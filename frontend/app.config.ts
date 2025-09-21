// /app.config.ts
import 'dotenv/config';
import { ExpoConfig } from '@expo/config';

const config: ExpoConfig = {
	name: 'Pland',
	slug: 'pland',
	extra: {
		API_BASE_URL: process.env.EXPO_PUBLIC_API_BASE_URL,
	},
};

export default config;