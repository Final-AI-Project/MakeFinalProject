// app/(page)/diary.tsx

// ─────────────────────────────────────────────────────────────────────────────
// ① Imports
// ─────────────────────────────────────────────────────────────────────────────
import React, { useMemo, useRef, useState, useEffect } from "react";
import {
	View, Text, StyleSheet, ScrollView,
	TextInput, Pressable, Image, Alert, ActivityIndicator, Animated, Easing,
	PanResponder, Dimensions, Platform,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useColorScheme } from "react-native";
import { useRouter } from "expo-router";
import Colors from "../../constants/Colors";
import { fetchSimpleWeather } from "../../components/common/weatherBox";
import { startLoading } from "../../components/common/loading";
import useKeyboardPadding from "../../hooks/useKeyboardPadding"; // ⬅️ 추가

// ─────────────────────────────────────────────────────────────────────────────
// ② Helpers & Types
// ─────────────────────────────────────────────────────────────────────────────
type Weather = "맑음" | "흐림" | "비" | "눈" | null;

// expo-image-picker 신/구 버전 호환(enum 폴리필)
const MEDIA = (ImagePicker as any).MediaType ?? (ImagePicker as any).MediaTypeOptions;

// ❌ (버그) 컴포넌트 밖에서 useRouter() 호출 금지
// const router = useRouter();

const todayStr = () => {
	const d = new Date();
	const yyyy = d.getFullYear();
	const mm = String(d.getMonth() + 1).padStart(2, "0");
	const dd = String(d.getDate()).padStart(2, "0");
	return `${yyyy}-${mm}-${dd}`;
};

// 한글 조사 자동
function withJosa(word: string, type: "이가" | "을를" = "이가") {
	const code = word.charCodeAt(word.length - 1);
	const HANGUL_BASE = 0xac00;
	const HANGUL_END = 0xd7a3;
	let hasJong = false;
	if (code >= HANGUL_BASE && code <= HANGUL_END) {
		const jong = (code - HANGUL_BASE) % 28;
		hasJong = jong > 0;
	}
	if (type === "이가") return `${word}${hasJong ? "이" : "가"}`;
	return `${word}${hasJong ? "을" : "를"}`;
}

/** 인라인 드롭다운 */
function InlineSelect<T extends string>({
	label, value, options, onChange, placeholder = "선택하세요", theme,
}: {
	label: string;
	value: T | null;
	options: { label: string; value: T }[];
	onChange: (v: T) => void;
	placeholder?: string;
	theme: typeof Colors.light;
}) {
	const [open, setOpen] = useState(false);
	return (
		<View style={styles.field}>
			<Text style={[styles.sectionLabel, { color: theme.text }]}>{label}</Text>
			<Pressable onPress={() => setOpen(v => !v)} style={[styles.input, { borderColor: theme.border }]}>
				<Text style={{ color: theme.text }}>
					{value ? options.find(o => o.value === value)?.label : placeholder}
				</Text>
			</Pressable>
			{open && (
				<View style={[styles.dropdownPanel, { borderColor: theme.border }]}>
					{options.map(opt => (
						<Pressable
							key={opt.value}
							onPress={() => { onChange(opt.value); setOpen(false); }}
							style={[styles.dropdownItem, { backgroundColor: theme.bg }]}
						>
							<Text style={{ color: theme.text }}>{opt.label}</Text>
						</Pressable>
					))}
				</View>
			)}
		</View>
	);
}

/** 한 글자씩 등장하는 애니메이션 텍스트 */
function AnimatedChars({
	text,
	delayStep = 24,
	duration = 280,
	style,
}: {
	text: string;
	delayStep?: number;
	duration?: number;
	style?: any;
}) {
	const chars = React.useMemo(() => [...(text ?? "")], [text]);

	const valuesRef = React.useRef(chars.map(() => new Animated.Value(0)));
	if (valuesRef.current.length !== chars.length) {
		valuesRef.current = chars.map(() => new Animated.Value(0));
	}

	useEffect(() => {
		const animations = valuesRef.current.map((v, i) =>
			Animated.timing(v, {
				toValue: 1,
				duration,
				delay: i * delayStep,
				easing: Easing.out(Easing.cubic),
				useNativeDriver: true,
			})
		);
		Animated.stagger(delayStep, animations).start();
	}, [text, delayStep, duration]);

	return (
		<View style={{ flexDirection: "row", flexWrap: "wrap" }}>
			{chars.map((ch, i) => {
				const v = valuesRef.current[i];
				const translateY = v.interpolate({ inputRange: [0, 1], outputRange: [12, 0] });
				return (
					<Animated.Text
						key={`${ch}-${i}-${chars.length}`}
						style={[style, { opacity: v, transform: [{ translateY }] }]}
					>
						{ch}
					</Animated.Text>
				);
			})}
		</View>
	);
}

/** 바텀시트 */
function BottomSheet({
	visible,
	text,
	onClose,
	theme,
}: {
	visible: boolean;
	text: string;
	onClose: () => void;
	theme: typeof Colors.light;
}) {
	const screenH = Dimensions.get("window").height;
	const translateY = useRef(new Animated.Value(screenH)).current;
	const [interactive, setInteractive] = useState(false);

	const openSheet = () => {
		setInteractive(true);
		Animated.timing(translateY, {
			toValue: 0,
			duration: 260,
			easing: Easing.out(Easing.cubic),
			useNativeDriver: true,
		}).start();
	};

	const closeSheet = (after?: () => void) => {
		Animated.timing(translateY, {
			toValue: screenH,
			duration: 200,
			easing: Easing.in(Easing.cubic),
			useNativeDriver: true,
		}).start(() => {
			setInteractive(false);
			after?.();
		});
	};

	useEffect(() => {
		if (visible) openSheet();
		else closeSheet();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [visible]);

	const panResponder = useRef(
		PanResponder.create({
			onMoveShouldSetPanResponder: (_, g) => g.dy > 6,
			onPanResponderMove: (_, g) => {
				const dy = Math.max(0, g.dy);
				translateY.setValue(dy);
			},
			onPanResponderRelease: (_, g) => {
				const shouldClose = g.dy > 120 || g.vy > 0.8;
				if (shouldClose) closeSheet(onClose);
				else {
					Animated.spring(translateY, {
						toValue: 0,
						useNativeDriver: true,
						bounciness: 3,
					}).start();
				}
			},
		})
	).current;

	const dimOpacity = translateY.interpolate({
		inputRange: [0, screenH],
		outputRange: [1, 0],
	});

	// @ts-ignore
	if (!visible && translateY._value === screenH && !interactive) return null;

	return (
		<View style={[StyleSheet.absoluteFill, { pointerEvents: interactive ? "auto" : "none" }]}>
			<Animated.View
				style={[
					StyleSheet.absoluteFillObject,
					{ backgroundColor: "rgba(0,0,0,0.5)", opacity: dimOpacity },
				]}
			/>
			<Animated.View
				style={[styles.sheetWrap, { transform: [{ translateY }] }]}
				{...panResponder.panHandlers}
			>
				<View style={[styles.sheetHandle, { backgroundColor: theme.text === "#1a1a1a" ? "#d1d5db" : "#475569" }]} />
				<Text style={[styles.sheetTitle, { color: theme.text }]}>AI 코멘트</Text>

				<View style={styles.sheetBody}>
					<AnimatedChars
						text={text || "임시 응답 텍스트가 없습니다."}
						delayStep={22}
						duration={260}
						style={[styles.sheetText, { color: theme.text }]}
					/>
				</View>

				<View style={styles.sheetActions}>
					<Pressable onPress={() => closeSheet(onClose)} style={[styles.sheetBtn]}>
						<Text style={[styles.sheetBtnText, { color: theme.text }]}>오늘 즐거웠어 고마워👋</Text>
					</Pressable>
				</View>
			</Animated.View>
		</View>
	);
}

// ─────────────────────────────────────────────────────────────────────────────
// ③ Component
// ─────────────────────────────────────────────────────────────────────────────
export default function Diary() {
	// Theme & Router
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const router = useRouter();

	// 키보드/고정바
	const { paddingBottom, keyboardVisible, rawKeyboardHeight } = useKeyboardPadding(45); // ⬅️ 동일 보정
	const BASE_BAR_HEIGHT = 68;

	// 스크롤 자동 센터링 준비
	const scrollRef = useRef<ScrollView>(null);
	const fieldY = useRef<Record<string, number>>({});
	const onFieldLayout = (key: string, y: number) => { fieldY.current[key] = y; };
	const scrollToField = (key: string, inputHeight = 56) => {
		const y = fieldY.current[key] ?? 0;
		const screenH = Dimensions.get("window").height;
		const visibleH = screenH - (keyboardVisible ? rawKeyboardHeight : 0);
		const targetY = Math.max(0, y - (visibleH - inputHeight) / 2);
		scrollRef.current?.scrollTo({ y: targetY, animated: true });
	};

	// 폼 상태
	const [photoUri, setPhotoUri] = useState<string | null>(null);
	const [title, setTitle] = useState("");
	const [selectedPlant, setSelectedPlant] = useState<string | null>(null);
	const [date] = useState(todayStr());
	const [weather, setWeather] = useState<Weather>(null);
	const [body, setBody] = useState("");

	// 기타 UI
	const [busy, setBusy] = useState(false);
	const [sheetVisible, setSheetVisible] = useState(false);

	// AI 텍스트
	const [aiText, setAiText] = useState<string>("오늘은 통풍만 잘 시켜주세요. 물은 내일 추천! 🌤️");
	const [aiPreviewVisible, setAiPreviewVisible] = useState(false);

	// 내 식물(별명) — TODO: 실제 리스트로 교체
	const myPlants = useMemo(
		() => [
			{ label: "초록이 (몬스테라)", value: "초록이" },
			{ label: "복덩이 (금전수)", value: "복덩이" },
		],
		[]
	);

	// 날씨 자동 채움 + 로딩 페이지 연동
	useEffect(() => {
		startLoading(router, {
			task: async () => {
				try {
					const w = await fetchSimpleWeather(
						"GTr1cI7Wi0FRbOTFBaUzUCzCDP4OnyyEmHnn11pxCUC5ehG5bQnbyztgeydnOWz1O04tjw1SE5RsX8RNo6XCgQ==",
						{ lat: 37.4836, lon: 127.0326, label: "서울시 - 서초구" }
					);
					if (w) setWeather(prev => prev ?? w);
				} catch (e) {
					console.warn("[weather] fetch failed:", e);
				}
			},
			to: "/(page)/diary",
			replace: true,
		});
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	// 제출 버튼 활성 조건
	const canSubmit = Boolean(photoUri && title.trim() && selectedPlant && date && weather && body.trim());
	const aiSectionLabel = selectedPlant ? `${withJosa(selectedPlant, "이가")} 하고픈 말` : "AI 응답(미리보기)";

	// 사진 선택
	const pickImage = async () => {
		const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
		if (status !== "granted") return Alert.alert("권한 필요", "앨범 접근 권한을 허용해주세요.");
		setBusy(true);
		try {
			const res = await ImagePicker.launchImageLibraryAsync({
				allowsEditing: true,
				quality: 0.9,
				mediaTypes: MEDIA?.Images ?? ImagePicker.MediaTypeOptions.Images,
				aspect: [1, 1],
			});
			if (!res.canceled && res.assets?.[0]?.uri) setPhotoUri(res.assets[0].uri);
		} finally {
			setBusy(false);
		}
	};

	// 등록
	const handleSubmit = async () => {
		if (!canSubmit) return;
		// TODO: 서버 저장 & LLM 호출 후 setAiText(resp.message)
		setAiPreviewVisible(true);
		setSheetVisible(true);
	};

	return (
		// ⬇️ KeyboardAvoidingView 제거, View로 교체
		<View style={[styles.container, { backgroundColor: theme.bg }]}>
			<ScrollView
				ref={scrollRef}
				style={{ flex: 1 }}
				// ⬇️ 살짝 터치로 키보드가 닫히지 않게
				keyboardDismissMode="none"
				keyboardShouldPersistTaps="always"
				// ⬇️ 콘텐츠가 버튼에 가리지 않도록: 고정바 + 키보드만큼 바닥 여백
				contentContainerStyle={{ paddingBottom: BASE_BAR_HEIGHT + paddingBottom }}
				scrollIndicatorInsets={{ bottom: BASE_BAR_HEIGHT }}
			>
				{/* 사진 등록 */}
				<View style={styles.photoBox}>
					<Pressable
						onPress={pickImage}
						disabled={busy}
						onStartShouldSetResponder={() => false} // 스크롤 제스처 우선
						style={[styles.photoPlaceholder, { borderColor: theme.border, backgroundColor: theme.graybg }]}
					>
						{photoUri ? (
							<>
								<Image source={{ uri: photoUri }} style={styles.photo} resizeMode="cover" />
								<View style={[styles.changeBadge, { borderColor: theme.border, backgroundColor: theme.bg + "cc" }]}>
									<Text style={[styles.changeBadgeText, { color: theme.text }]}>사진 변경</Text>
								</View>
							</>
						) : (
							<>
								<Text style={{ color: theme.text, fontSize: 40 }}>+</Text>
								<Text style={{ color: theme.text, marginTop: 4 }}>사진을 등록하세요</Text>
							</>
						)}
					</Pressable>

					{busy && (
						<View style={styles.busyOverlay}>
							<ActivityIndicator size="large" />
						</View>
					)}
				</View>

				{/* 입력들 */}
				<View style={styles.inputArea}>
					{/* 제목 */}
					<View
						style={styles.field}
						onLayout={(e) => onFieldLayout("title", e.nativeEvent.layout.y)}
					/>
					<Text style={[styles.sectionLabel, { color: theme.text }]}>제목</Text>
					<TextInput
						placeholder="제목을 입력하세요"
						placeholderTextColor="#909090"
						value={title}
						onChangeText={setTitle}
						onFocus={() => scrollToField("title")}
						style={[styles.input, { color: theme.text, borderColor: theme.border }]}
						returnKeyType="next"
					/>

					{/* 내 식물(별명) */}
					<InlineSelect
						label="내 식물(별명)"
						value={selectedPlant}
						options={myPlants}
						onChange={setSelectedPlant}
						placeholder="내 식물을 선택하세요"
						theme={theme}
					/>

					{/* 날짜 (읽기전용) */}
					<View
						style={styles.field}
						onLayout={(e) => onFieldLayout("date", e.nativeEvent.layout.y)}
					>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>날짜</Text>
						<TextInput
							value={date}
							editable={false}
							style={[styles.input, { color: theme.text, borderColor: theme.border, opacity: 0.85 }]}
						/>
					</View>

					{/* 날씨 (자동/읽기전용) */}
					<View
						style={styles.field}
						onLayout={(e) => onFieldLayout("weather", e.nativeEvent.layout.y)}
					>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>날씨</Text>
						<TextInput
							value={weather ?? ""}
							editable={false}
							placeholder="조회 중…"
							placeholderTextColor="#909090"
							style={[styles.input, { color: theme.text, borderColor: theme.border, opacity: 0.85 }]}
						/>
					</View>

					{/* 일기 내용 */}
					<View
						style={styles.field}
						onLayout={(e) => onFieldLayout("body", e.nativeEvent.layout.y)}
					>
						<Text style={[styles.sectionLabel, { color: theme.text }]}>일기 내용</Text>
						<TextInput
							placeholder="오늘의 식물 이야기를 적어주세요…"
							placeholderTextColor="#909090"
							value={body}
							onChangeText={setBody}
							onFocus={() => scrollToField("body", 180)}
							multiline
							textAlignVertical="top"
							style={[styles.input, { color: theme.text, borderColor: theme.border, minHeight: 180, lineHeight: 22 }]}
						/>
					</View>

					{/* 🔹 AI 응답(미리보기) */}
					{aiPreviewVisible && (
						<View
							style={styles.field}
							onLayout={(e) => onFieldLayout("ai", e.nativeEvent.layout.y)}
						>
							<Text style={[styles.sectionLabel, { color: theme.text }]}>{aiSectionLabel}</Text>
							<View style={[styles.input, { borderColor: theme.border, paddingVertical: 14 }]}>
								<AnimatedChars text={aiText} style={{ color: theme.text, fontSize: 15, lineHeight: 22 }} />
							</View>
						</View>
					)}
				</View>
			</ScrollView>

			{/* 하단 고정 버튼 (absolute) */}
			<View
				style={[
					styles.fixedBar,
					{ backgroundColor: theme.bg, marginBottom: keyboardVisible ? paddingBottom : 0 },
				]}
			>
				<Pressable onPress={() => router.back()} style={[styles.cancelBtn, { borderColor: theme.border }]}>
					<Text style={[styles.cancelText, { color: theme.text }]}>취소</Text>
				</Pressable>
				<Pressable
					disabled={!canSubmit}
					onPress={handleSubmit}
					style={[styles.submitBtn, { backgroundColor: !canSubmit ? theme.graybg : theme.primary }]}
				>
					<Text style={[styles.submitText, { color: "#fff" }]}>등록</Text>
				</Pressable>
			</View>

			{/* 바텀시트 */}
			<BottomSheet
				visible={sheetVisible}
				text={aiText}
				onClose={() => setSheetVisible(false)}
				theme={theme}
			/>
		</View>
	);
}

// ─────────────────────────────────────────────────────────────────────────────
// ④ Styles
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
	container: { flex: 1 },

	sectionLabel: { fontSize: 16, fontWeight: "700", marginBottom: 8 },
	helper: { fontSize: 12, marginBottom: 8, opacity: 0.8 },

	photoBox: { alignItems: "center", position: "relative", height: 260, marginTop: 12 },
	photo: { position: "absolute", left: 0, top: 0, width: "100%", height: 260, resizeMode: "cover" },
	photoPlaceholder: { width: "100%", height: 260, alignItems: "center", justifyContent: "center" },

	busyOverlay: {
		position: "absolute", left: 0, right: 0, top: 0, bottom: 0,
		alignItems: "center", justifyContent: "center",
		backgroundColor: "rgba(0,0,0,0.08)", borderRadius: 12,
	},

	inputArea: { paddingHorizontal: 24 },
	field: { marginTop: 24 },
	input: { borderWidth: 1, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 12 },

	// ✅ 고정 하단 버튼 바 (absolute)
	fixedBar: {
		position: "absolute",
		left: 0,
		right: 0,
		bottom: 0,
		flexDirection: "row",
		gap: 8,
		padding: 12,
	},

	cancelBtn: { flex: 1, borderWidth: 1, borderRadius: 12, alignItems: "center", justifyContent: "center", paddingVertical: 14 },
	cancelText: { fontSize: 15, fontWeight: "600" },
	submitBtn: { flex: 2, borderRadius: 12, alignItems: "center", justifyContent: "center", paddingVertical: 14 },
	submitText: { fontWeight: "700", fontSize: 16 },

	changeBadge: { position: "absolute", right: 10, bottom: 10, borderWidth: 1, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6 },
	changeBadgeText: { fontSize: 12, fontWeight: "700" },

	dropdownPanel: { borderWidth: 1, borderRadius: 10, overflow: "hidden", marginTop: -6 },
	dropdownItem: { paddingHorizontal: 12, paddingVertical: 12 },

	// 바텀시트
	sheetWrap: {
		position: "absolute",
		left: 0,
		right: 0,
		bottom: 65,
		borderTopLeftRadius: 20,
		borderTopRightRadius: 20,
		paddingTop: 10,
		paddingHorizontal: 20,
		paddingBottom: 20,
		backgroundColor: "#fff",
	},
	sheetHandle: {
		alignSelf: "center",
		width: 42,
		height: 5,
		borderRadius: 999,
		opacity: 0.5,
		marginBottom: 12,
	},
	sheetTitle: { fontSize: 14, fontWeight: "800", marginBottom: 8, opacity: 0.8 },
	sheetBody: { paddingVertical: 6 },
	sheetText: { fontSize: 16, lineHeight: 24 },
	sheetActions: { marginTop: 12, alignItems: "flex-end" },
	sheetBtn: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 10, backgroundColor: "rgba(0,0,0,0.06)" },
	sheetBtnText: { fontWeight: "700" },
});
