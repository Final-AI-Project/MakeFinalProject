import React, { useState } from "react";
import {
	View,
	Text,
	TextInput,
	StyleSheet,
	TouchableOpacity,
	useColorScheme,
	KeyboardAvoidingView,
	Platform,
	Alert,
} from "react-native";
import Colors from "../../constants/Colors";

export default function DiaryScreen() {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];

	const [title, setTitle] = useState("");
	const [body, setBody] = useState("");

	const onSave = async () => {
		if (!title.trim() || !body.trim()) {
			return Alert.alert("입력 필요", "제목과 내용을 모두 입력해 주세요.");
		}
		// TODO: 서버 API 연동
		// await fetch("https://your.api/diary", { method: "POST", headers: {...}, body: JSON.stringify({ title, body }) });
		Alert.alert("저장됨", "일기가 임시로 저장되었습니다.");
		setTitle("");
		setBody("");
	};

	return (
		<KeyboardAvoidingView
			style={{ flex: 1, backgroundColor: theme.bg }}
			behavior={Platform.select({ ios: "padding", android: undefined })}
		>
			<View style={[styles.container, { backgroundColor: theme.bg }]}>
				<Text style={[styles.title, { color: theme.text }]}>일기쓰기</Text>

				<TextInput
					value={title}
					onChangeText={setTitle}
					placeholder="제목"
					placeholderTextColor="#909090"
					style={[
						styles.input,
						styles.titleInput,
						{ color: theme.text, borderColor: "#d0d0d0", backgroundColor: "transparent" },
					]}
					returnKeyType="next"
				/>

				<TextInput
					value={body}
					onChangeText={setBody}
					placeholder="오늘의 식물 일기를 적어주세요…"
					placeholderTextColor="#909090"
					multiline
					textAlignVertical="top"
					style={[
						styles.input,
						styles.bodyInput,
						{ color: theme.text, borderColor: "#d0d0d0", backgroundColor: "transparent" },
					]}
				/>

				<TouchableOpacity style={[styles.saveBtn, { backgroundColor: theme.primary }]} onPress={onSave} activeOpacity={0.9}>
					<Text style={styles.saveText}>저장</Text>
				</TouchableOpacity>
			</View>
		</KeyboardAvoidingView>
	);
}

const styles = StyleSheet.create({
	container: { flex: 1, padding: 16 },
	title: { fontSize: 18, fontWeight: "700", marginBottom: 12 },
	input: {
		borderWidth: 1,
		borderRadius: 12,
		paddingHorizontal: 12,
		paddingVertical: 10,
		marginBottom: 12,
	},
	titleInput: { fontSize: 16 },
	bodyInput: { minHeight: 220, fontSize: 15, lineHeight: 22 },
	saveBtn: { height: 48, borderRadius: 12, alignItems: "center", justifyContent: "center" },
	saveText: { color: "#fff", fontSize: 16, fontWeight: "700" },
});
