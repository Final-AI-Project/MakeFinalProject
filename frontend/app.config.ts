// /app.config.ts
import 'dotenv/config';
import { ExpoConfig } from '@expo/config';

const config: ExpoConfig = {
	name: 'your-app-name',
	slug: 'your-app-slug',
	extra: {
		API_BASE_URL: process.env.EXPO_PUBLIC_API_BASE_URL,
	},
};

export default config;