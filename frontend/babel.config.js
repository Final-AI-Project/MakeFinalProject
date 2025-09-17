// babel.config.js
module.exports = function (api) {
	api.cache(true);
	return {
		presets: ["babel-preset-expo"],     // ✅ expo-router/babel 제거
		plugins: [
			"react-native-worklets/plugin", // ✅ reanimated 플러그인 새 이름
		],
	};
};