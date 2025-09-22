// /app.config.ts
import "dotenv/config";
import { ExpoConfig } from "@expo/config";

const config: ExpoConfig = {
  name: "Pland",
  slug: "pland",
  extra: {
    // API_BASE_URL은 api.ts에서 직접 처리
  },
};

export default config;
