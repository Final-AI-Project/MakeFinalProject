import React, { useState, useEffect, useRef } from "react";
import { View, Text, StyleSheet, Image, Alert, useColorScheme, TouchableOpacity, ActivityIndicator } from "react-native";
import * as ImagePicker from "expo-image-picker";
import Colors from "../../constants/Colors";

export default function CameraScreen() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];

	const [uri, setUri] = useState<string | null>(null);
	const [busy, setBusy] = useState(false);

	const askCamera = async () => {
		const { status } = await ImagePicker.requestCameraPermissionsAsync();
		if (status !== "granted") {
			return Alert.alert("권한 필요", "카메라 권한을 허용해주세요.");
		}
		setBusy(true);
		try {
			const res = await ImagePicker.launchCameraAsync({
				quality: 0.85,
				exif: false,
				base64: false,
				allowsEditing: false,
			});
			if (!res.canceled) setUri(res.assets[0].uri);
		} finally {
			setBusy(false);
		}
	};

	const askGallery = async () => {
		const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
		if (status !== "granted") {
			return Alert.alert("권한 필요", "갤러리 접근 권한을 허용해주세요.");
		}
		setBusy(true);
		try {
			const res = await ImagePicker.launchImageLibraryAsync({
				quality: 0.85,
				exif: false,
				base64: false,
				allowsEditing: false,
			});
			if (!res.canceled) setUri(res.assets[0].uri);
		} finally {
			setBusy(false);
		}
	};

	const clearImage = () => setUri(null);

	const didAutoOpen = useRef(false);
	useEffect(() => {
		if (didAutoOpen.current) return;
		didAutoOpen.current = true;
		setTimeout(() => {
			askCamera().catch(() => {
				// 실패해도 페이지는 유지, 필요시 플래그 리셋 가능
			});
		}, 0);
	}, []);

	return (
		<View style={[styles.container, { backgroundColor: theme.bg }]}>
			<View style={styles.previewWrap}>
				{busy ? (
					<ActivityIndicator size="large" />
				) : uri ? (
					<Image source={{ uri }} style={styles.preview} />
				) : (
					<Text style={{ color: "#909090" }}>이미지를 선택하거나 촬영해 주세요.</Text>
				)}
			</View>
			<View style={styles.row}>
				<TouchableOpacity style={[styles.btn, { backgroundColor: theme.primary }]} onPress={askCamera} activeOpacity={0.9}>
					<Text style={styles.btnText}>촬영</Text>
				</TouchableOpacity>
				<TouchableOpacity style={[styles.btn, { backgroundColor: "#5f6368" }]} onPress={askGallery} activeOpacity={0.9}>
					<Text style={styles.btnText}>갤러리</Text>
				</TouchableOpacity>
				{uri && (
					<TouchableOpacity style={[styles.btn, { backgroundColor: "#d32f2f" }]} onPress={clearImage} activeOpacity={0.9}>
						<Text style={styles.btnText}>↺ 초기화</Text>
					</TouchableOpacity>
				)}
			</View>
		</View>
	);
}

const styles = StyleSheet.create({
	container: { flex: 1, paddingHorizontal:24, paddingBottom:72 },
	row: { flexDirection: "row", gap: 8, marginTop: 12 },
	btn: { flex: 1, height: 44, borderRadius: 12, alignItems: "center", justifyContent: "center" },
	btnText: { color: "#fff", fontSize: 15, fontWeight: "700" },
	previewWrap: {
		flex: 1,
		borderWidth: 1,
		borderColor: "#e0e0e0",
		borderRadius: 12,
		alignItems: "center",
		justifyContent: "center",
		overflow: "hidden",
	},
	preview: { width: "100%", height: "100%", resizeMode: "cover" },
});
