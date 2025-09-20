// /app.config.ts
import "dotenv/config";
import { ExpoConfig } from "@expo/config";

const config: ExpoConfig = {
  name: "plend",
  slug: "plend",
  extra: {
    API_BASE_URL:
      process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:3000/",
  },
};

export default config;
