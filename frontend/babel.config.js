// https://docs.expo.dev/guides/using-eslint/
module.exports = function (api) {
    api.cache(true);
    return {
        presets: ['babel-preset-expo'],
        plugins: [
            'expo-router/babel',
            // Reanimated 플러그인은 항상 마지막
            'react-native-reanimated/plugin',
        ],
    };
};
