// app/(page)/(stackless)/plant-new.tsx
import React, { useMemo, useState } from "react";
import {
	View,
	Text,
	StyleSheet,
	ScrollView,
	KeyboardAvoidingView,
	Platform,
	TextInput,
	Pressable,
	Image,
	Alert,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useRouter } from "expo-router";
import { useColorScheme } from "react-native";
import Colors from "../../../constants/Colors";

type IndoorOutdoor = "indoor" | "outdoor" | null;

const SPECIES = [
	"몬스테라",
	"스투키",
	"금전수",
	"선인장",
	"호접란",
	"테이블야자",
	"홍콩야자",
	"스파티필럼",
	"관음죽",
	"벵갈고무나무",
	"올리브나무",
	"디펜바키아",
	"보스턴고사리",
] as const;

export default function PlantNew() {
	const router = useRouter();
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];

	const [imageUri, setImageUri] = useState<string | null>(null);
	const [species, setSpecies] = useState<string>("");
	const [nickname, setNickname] = useState<string>("");
	const [startedAt, setStartedAt] = useState<string>("");

	const isKnownSpecies = useMemo(
		() => (species ? (SPECIES as readonly string[]).includes(species) : true),
		[species],
	);

	const isAllFilled = Boolean(
		imageUri &&
			species.trim() &&
			nickname.trim() &&
			startedAt.trim()
	);

	const isDateLike = useMemo(() => {
		if (!startedAt) return true;
		return /^\d{4}-\d{2}-\d{2}$/.test(startedAt);
	}, [startedAt]);

	function handlePickImage() {
		if (Platform.OS === "web") {
			pickFromLibrary();
			return;
		}
		
		Alert.alert("사진 등록", "사진을 불러올 방법을 선택하세요.", [
			{ text: "사진 찍기", onPress: takePhoto },
			{ text: "앨범 선택", onPress: pickFromLibrary },
			{ text: "취소", style: "cancel" },
		]);
	}

	async function pickFromLibrary() {
		const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
		if (status !== "granted") {
			Alert.alert("권한 필요", "앨범 접근 권한을 허용해주세요.");
			return;
		}
		const res = await ImagePicker.launchImageLibraryAsync({
			allowsEditing: true,
			quality: 0.9,
			mediaTypes: ImagePicker.MediaTypeOptions.Images,
			aspect: [1, 1],
		});
		if (!res.canceled && res.assets?.[0]?.uri) {
			setImageUri(res.assets[0].uri);
		}
	}

	async function takePhoto() {
		const { status } = await ImagePicker.requestCameraPermissionsAsync();
		if (status !== "granted") {
			Alert.alert("권한 필요", "카메라 권한을 허용해주세요.");
			return;
		}
		const res = await ImagePicker.launchCameraAsync({
			allowsEditing: true,
			quality: 0.9,
			aspect: [1, 1],
		});
		if (!res.canceled && res.assets?.[0]?.uri) {
			setImageUri(res.assets[0].uri);
		}
	}

	function handleSubmit() {
		if (!isAllFilled) return;
		if (!isDateLike) {
			Alert.alert("날짜 형식 확인", "날짜는 YYYY-MM-DD 형식으로 입력해주세요.");
			return;
		}

		// place 제거했으니 species, nickname, startedAt, inout만 사용
		Alert.alert("등록 완료", "새 식물이 등록되었습니다! (로컬 처리 가정)", [
			{ text: "확인", onPress: () => router.replace("/(page)/home") },
		]);
	}

	function formatDateInput(text: string): string {
		const digits = text.replace(/\D/g, "").slice(0, 8);
		if (digits.length <= 4) return digits;
		if (digits.length <= 6) return `${digits.slice(0, 4)}-${digits.slice(4)}`;
		return `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6, 8)}`;
	}

	return (
		<KeyboardAvoidingView
			style={[styles.container, { backgroundColor: theme.bg }]}
			behavior={Platform.select({ ios: "padding", android: "height" })}
		>
			<ScrollView
				keyboardShouldPersistTaps="handled"
				keyboardDismissMode="interactive"
				contentContainerStyle={{ paddingBottom: 120 }}
			>
				{/* 사진 */}
				<View style={styles.photoBox}>
					{imageUri ? (
						<Image source={{ uri: imageUri }} style={styles.photo} />
					) : (
						<Pressable
							style={[
								styles.photoPlaceholder,
								{ borderColor: theme.border, backgroundColor: theme.graybg },
							]}
							onPress={handlePickImage}
						>
							{imageUri ? (
								<Image
									source={{ uri: imageUri }}
									style={styles.photo}
									resizeMode="cover"   // object-fit: cover 역할
								/>
							) : (
								<>
									<Text style={{ color: theme.text, fontSize: 40 }}>+</Text>
									<Text style={{ color: theme.text, marginTop: 4 }}>키우는 식물을 자랑해주세요!</Text>
								</>
							)}
						</Pressable>
					)}
				</View>

				<View style={styles.inputArea}>
					{/* 품종 분류 */}
					<View style={styles.field}>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>품종 분류</Text>
						<TextInput
							placeholder="직접입력 (예: 몬스테라)"
							placeholderTextColor="#909090"
							value={species}
							onChangeText={setSpecies}
							style={[styles.input, { color: theme.text, borderColor: theme.border }]}
						/>
						<Text style={[styles.notice, { color: theme.text }]}>
							* 직접입력 시 올바른 품종정보나 생육정보의 제공이 어려울 수 있습니다.
						</Text>
						{species.trim().length > 0 && !isKnownSpecies && (
							<Text style={styles.warn}>
								* 데이터 베이스에 없는 식물입니다. 식물주님의 품종을 학습하여 조만간 업데이트 하겠습니다.
							</Text>
						)}
					</View>

					{/* 별명 */}
					<View style={styles.field}>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>내 식물 별명</Text>
						<TextInput
							placeholder="예: 몬몬이"
							placeholderTextColor="#909090"
							value={nickname}
							onChangeText={setNickname}
							style={[styles.input, { color: theme.text, borderColor: theme.border }]}
						/>
					</View>

					{/* 키우기 시작한 날 */}
					<View style={styles.field}>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>키우기 시작한 날</Text>
						<TextInput
							placeholder="YYYY-MM-DD"
							placeholderTextColor="#909090"
							value={startedAt}
							onChangeText={(text) => setStartedAt(formatDateInput(text))}
							keyboardType="number-pad"
							maxLength={10}
							style={[styles.input, { color: theme.text, borderColor: theme.border }]}
						/>
						{startedAt.length > 0 && !isDateLike && (
							<Text style={styles.warn}>YYYY-MM-DD 형식으로 입력해주세요.</Text>
						)}
					</View>
				</View>
			</ScrollView>

			{/* 하단 고정 버튼 영역 */}
			<View style={[styles.bottomBar, { backgroundColor: theme.bg, borderTopColor: theme.border }]}>
				<Pressable onPress={() => router.replace("/(page)/home")} style={[styles.cancelBtn, { borderColor: theme.border }]}>
					<Text style={[styles.cancelText, { color: theme.text }]}>취소</Text>
				</Pressable>

				<Pressable
					disabled={!isAllFilled || !isDateLike}
					onPress={handleSubmit}
					style={[styles.submitBtn, { backgroundColor: !isAllFilled || !isDateLike ? theme.graybg : theme.primary }]}
				>
					<Text style={[styles.submitText, { color: theme.text }]}>등록하기</Text>
				</Pressable>
			</View>
		</KeyboardAvoidingView>
	);
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
	},
	sectionLabel: {
		fontSize: 16,
		fontWeight: "700",
		marginBottom: 8,
	},
	helper: {
		fontSize: 12,
		marginBottom: 8,
		opacity: 0.8,
	},
	photoBox: {
		alignItems: "center",
		position:'relative',
		height:260,
		marginTop: 12,
	},
	photo: {
		position:'absolute',
		left:0,
		top:0,
		width:'100%',
		height:260,
		resizeMode:'cover',
	},
	photoPlaceholder: {
		width:'100%',
		height: 260,
		alignItems: "center",
		justifyContent: "center",
	},
	inputArea: {
		paddingHorizontal:24,
	},
	field:{
		marginTop:24,
	},
	input: {
		borderWidth: 1,
		borderRadius: 10,
		paddingHorizontal: 12,
		paddingVertical: 12,
	},
	notice: {
		fontSize: 12,
		marginTop: 6,
	},
	warn: {
		fontSize: 12,
		marginTop: 6,
		color: "#d93025",
	},
	smallLabel: {
		fontSize: 13,
		fontWeight: "600",
		marginTop: 8,
	},
	radioRow: {
		flexDirection: "row",
		gap: 8,
		marginTop: 10,
	},
	radio: {
		paddingVertical: 10,
		paddingHorizontal: 14,
		borderRadius: 10,
		borderWidth: 1,
	},
	bottomBar: {
		position: "absolute",
		left: 0,
		right: 0,
		bottom: 0,
		flexDirection: "row",
		gap: 8,
		padding: 12,
		borderTopWidth: 1,
	},
	cancelBtn: {
		flex: 1,
		borderWidth: 1,
		borderRadius: 12,
		alignItems: "center",
		justifyContent: "center",
		paddingVertical: 14,
	},
	cancelText: {
		fontSize: 15,
		fontWeight: "600",
	},
	submitBtn: {
		flex: 2,
		borderRadius: 12,
		alignItems: "center",
		justifyContent: "center",
		paddingVertical: 14,
	},
	submitText: {
		fontWeight: "700",
		fontSize: 16,
	},
});
