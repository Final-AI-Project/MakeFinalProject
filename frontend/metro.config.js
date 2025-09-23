const { getDefaultConfig } = require("expo/metro-config");

const config = getDefaultConfig(__dirname);

// common 폴더를 라우트에서 제외
config.resolver.platforms = ["ios", "android", "native", "web"];
config.resolver.assetExts.push("onnx", "txt");

module.exports = config;
