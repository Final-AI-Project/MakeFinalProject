// babel.config.js
module.exports = function (api) {
  api.cache(true);
  return {
    presets: ["babel-preset-expo"],
    plugins: [
      "react-native-worklets/plugin", // ← reanimated/plugin 대신 이걸 사용
    ],
  };
};
