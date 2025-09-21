// app/(page)/(stackless)/medical-detail.tsx
import React, { useMemo, useState, useEffect } from "react";
import {
	View, Text, StyleSheet, ScrollView, KeyboardAvoidingView, Platform,
	Pressable, Image, Alert, ActivityIndicator,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useColorScheme } from "react-native";
import { useRouter } from "expo-router";
import Colors from "../../../constants/Colors";
import { fetchSimpleWeather } from "../../../components/common/weatherBox";

// ─────────────────────────────────────────────────────────────────────────────
// ① Helpers & Types
// ─────────────────────────────────────────────────────────────────────────────
type Weather = "맑음" | "흐림" | "비" | "눈" | null;
const MEDIA = (ImagePicker as any).MediaType ?? (ImagePicker as any).MediaTypeOptions;

const todayStr = () => {
	const d = new Date();
	const yyyy = d.getFullYear();
	const mm = String(d.getMonth() + 1).padStart(2, "0");
	const dd = String(d.getDate()).padStart(2, "0");
	return `${yyyy}-${mm}-${dd}`;
};

type Candidate = {
	id: string;
	name: string;
	desc?: string;
	confidence?: number;
};

// ─────────────────────────────────────────────────────────────────────────────
// ② InlineSelect (간단 셀렉트) — style prop 포함
// ─────────────────────────────────────────────────────────────────────────────
function InlineSelect<T extends string>({
	label, value, options, onChange, placeholder = "선택하세요", theme, style,
}: {
	label: string;
	value: T | null;
	options: { label: string; value: T }[];
	onChange: (v: T) => void;
	placeholder?: string;
	theme: typeof Colors.light;
	style?: any;
}) {
	const [open, setOpen] = useState(false);
	return (
		<View style={style}>
			<Text style={[styles.sectionLabel, { color: theme.text, marginBottom: 8 }]}>{label}</Text>
			<Pressable onPress={() => setOpen(v => !v)} style={[styles.rowBox, { borderColor: theme.border }]}>
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

// ─────────────────────────────────────────────────────────────────────────────
// ③ Component
// ─────────────────────────────────────────────────────────────────────────────
export default function medicalDetail() {
	// Theme & Router
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const router = useRouter();

	// 상태
	const [photoUri, setPhotoUri] = useState<string | null>(null);
	const [busy, setBusy] = useState(false);           // 사진 선택 중
	const [inferBusy, setInferBusy] = useState(false); // 진단 실행 중

	const [isMine, setIsMine] = useState<"mine" | "not-mine">("mine");
	const [selectedPlant, setSelectedPlant] = useState<string | null>(null);
	const [date] = useState(todayStr());
	const [weather, setWeather] = useState<Weather>(null); // 서버 저장에 활용 가능

	// 병충해 후보 top3 (초기엔 비워둠 → 박스는 렌더하되 텍스트만 “기본”)
	const [candidates, setCandidates] = useState<Candidate[]>([]);

	// 내 식물(별명) — TODO: 실제 내 식물 리스트로 교체
	const myPlants = useMemo(
		() => [
			{ label: "초록이 (몬스테라)", value: "초록이" },
			{ label: "복덩이 (금전수)", value: "복덩이" },
		],
		[]
	);

	// 날씨 자동 채움
	useEffect(() => {
		(async () => {
			try {
				const w = await fetchSimpleWeather(
					"GTr1cI7Wi0FRbOTFBaUzUCzCDP4OnyyEmHnn11pxCUC5ehG5bQnbyztgeydnOWz1O04tjw1SE5RsX8RNo6XCgQ==",
					{ lat: 37.4836, lon: 127.0326, label: "서울시 - 서초구" }
				);
				if (w) setWeather(prev => prev ?? w);
			} catch {}
		})();
	}, []);

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
			if (!res.canceled && res.assets?.[0]?.uri) {
				const uri = res.assets[0].uri;
				setPhotoUri(uri);
				await runDiagnosis(uri); // 새 사진마다 재진단
			}
		} finally {
			setBusy(false);
		}
	};

	// 토글 시 초기화(요청사항)
	const onPickMineMode = (mode: "mine" | "not-mine") => {
		setIsMine(mode);
		setSelectedPlant(null);
		setPhotoUri(null);
		setCandidates([]);
		setInferBusy(false);
	};

	// 제출 가능 조건
	const canSubmit = Boolean(photoUri && selectedPlant && isMine === "mine");

	// 등록
	const handleSubmit = async () => {
		if (!canSubmit) return;
		// TODO: 서버 저장 (photoUri, selectedPlant, date, weather, candidates)
		Alert.alert("등록 완료", "진단 결과가 저장되었습니다.");
		router.back();
	};

	// 모델 연동
	const runDiagnosis = async (uri: string) => {
		try {
			setInferBusy(true);
			setCandidates([]); // 텍스트를 “병충해 진단/진단 중…”으로 보이게 초기화

			// TODO: 여기를 실제 백엔드 호출로 교체
			// 예: const resp = await fetch(INFER_URL, { method:"POST", body: formData(uri) }).then(r=>r.json());
			// setCandidates(resp.top3);
			await new Promise(r => setTimeout(r, 1000));
			setCandidates([
				{ id: "1", name: "흰가루병", desc: "잎 표면에 흰 가루처럼 보임" },
				{ id: "2", name: "응애", desc: "미세한 거미류, 잎 뒷면 피해" },
				{ id: "3", name: "탄저병", desc: "갈색 반점, 원형 병반" },
			]);
		} catch (e) {
			Alert.alert("진단 실패", "사진 진단 중 문제가 발생했습니다.");
			setCandidates([]);
		} finally {
			setInferBusy(false);
		}
	};

	// 병충해 박스 내 텍스트 계산
	const getDiseaseContent = (idx: number) => {
		if (!photoUri) return { title: "사진을 등록하세요", desc: "" };
		if (inferBusy) return { title: "진단 중…", desc: "" };
		const item = candidates[idx];
		if (item) return { title: item.name, desc: item.desc ?? "" };
		return { title: "병충해 진단", desc: "" };
	};

	return (
		<KeyboardAvoidingView
			style={[styles.container, { backgroundColor: theme.bg }]}
			behavior={Platform.select({ ios: "padding", android: "height" })}
		>
			<ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingVertical: 16 }}>
				{/* 1) 사진 */}
				<View style={{ marginBottom: 16 }}>
					<Pressable
						onPress={pickImage}
						disabled={busy}
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

				{/* 2) 내 식물인지/아닌지 선택 */}
				<View style={{ marginBottom: 12, paddingHorizontal: 24 }}>
					<View style={{ flexDirection: "row", gap: 8 }}>
						<Pressable
							onPress={() => onPickMineMode("mine")}
							style={[
								styles.choiceBtn,
								{ borderColor: theme.border, backgroundColor: isMine === "mine" ? theme.primary : theme.bg },
							]}
						>
							<Text style={[styles.choiceText, { color: isMine === "mine" ? "#fff" : theme.text }]}>내 식물</Text>
						</Pressable>
						<Pressable
							onPress={() => onPickMineMode("not-mine")}
							style={[
								styles.choiceBtn,
								{ borderColor: theme.border, backgroundColor: isMine === "not-mine" ? theme.primary : theme.bg },
							]}
						>
							<Text style={[styles.choiceText, { color: isMine === "not-mine" ? "#fff" : theme.text }]}>다른 식물</Text>
						</Pressable>
					</View>
				</View>

				{/* 3) 내 식물 별명 선택 / 진단 날짜(당일) — 내 식물일 때만 노출 */}
				{isMine === "mine" && (
					<View style={{ marginBottom: 4, paddingHorizontal: 24 }}>
						<InlineSelect
							label=""
							value={selectedPlant}
							options={myPlants}
							onChange={setSelectedPlant}
							placeholder="내 식물을 선택하세요"
							theme={theme}
							style={{ marginTop: 0 }}
						/>
					</View>
				)}

				{/* 4) 병충해 1/2/3 박스 — 항상 렌더, 텍스트만 상태에 맞게 변경 */}
				<View style={{ marginTop: 8, paddingHorizontal: 24 }}>
					{[0, 1, 2].map((idx) => {
						const c = getDiseaseContent(idx);
						return (
							<View key={idx} style={[styles.rowBox, { borderColor: theme.border, marginBottom: 8 }]}>
								<Text style={[styles.rank, { color: theme.text }]}>{idx + 1}.</Text>
								<View style={{ flex: 1 }}>
									<Text style={[styles.diseaseName, { color: theme.text }]}>{c.title}</Text>
									{!!c.desc && (
										<Text style={[styles.diseaseDesc, { color: theme.text, opacity: 0.8 }]}>{c.desc}</Text>
									)}
								</View>
							</View>
						);
					})}
				</View>

				{/* 안내 문구 (다른 식물 선택 시) */}
				{isMine === "not-mine" && (
					<Text style={{ marginTop: 8, color: theme.text, opacity: 0.8, textAlign: "center" }}>
						다른 식물로 선택되어 등록할 수 없습니다.
					</Text>
				)}

				{/* 5) 하단 버튼: 등록 / 취소 */}
				<View style={[styles.bottomBar]}>
					<Pressable
						onPress={() => router.back()}
						style={[styles.cancelBtn, { borderColor: theme.border }]}
					>
						<Text style={[styles.cancelText, { color: theme.text }]}>취소</Text>
					</Pressable>
					<Pressable
						disabled={!canSubmit}
						onPress={handleSubmit}
						style={[
						 styles.submitBtn,
						 { backgroundColor: !canSubmit ? theme.graybg : theme.primary },
						]}
					>
						<Text style={[styles.submitText, { color: "#fff" }]}>등록</Text>
					</Pressable>
				</View>
			</ScrollView>
		</KeyboardAvoidingView>
	);
}

// ─────────────────────────────────────────────────────────────────────────────
// ④ Styles
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
	container: { flex: 1 },

	sectionLabel: { fontSize: 14, fontWeight: "700" },

	photoPlaceholder: {
		width: "100%",
		height: 260,
		alignItems: "center",
		justifyContent: "center",
		overflow: "hidden",
	},
	photo: { position: "absolute", left: 0, top: 0, width: "100%", height: 260 },
	busyOverlay: {
		position: "absolute", left: 0, right: 0, top: 0, bottom: 0,
		alignItems: "center", justifyContent: "center",
		backgroundColor: "rgba(0,0,0,0.08)", borderRadius: 12,
	},
	changeBadge: { position: "absolute", right: 10, bottom: 10, borderWidth: 1, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6 },
	changeBadgeText: { fontSize: 12, fontWeight: "700" },

	rowBox: {
		minHeight: 50,
		borderWidth: 1,
		borderRadius: 10,
		paddingHorizontal: 12,
		paddingVertical: 12,
		alignItems: "center",
		flexDirection: "row",
		gap: 8,
	},

	choiceBtn: {
		flex: 1,
		borderWidth: 1,
		borderRadius: 10,
		alignItems: "center",
		justifyContent: "center",
		paddingVertical: 12,
	},
	choiceText: { fontSize: 14, fontWeight: "700" },

	dropdownPanel: { borderWidth: 1, borderRadius: 10, overflow: "hidden", marginTop: -6 },
	dropdownItem: { paddingHorizontal: 12, paddingVertical: 12 },

	rank: { width: 20, textAlign: "center", fontWeight: "800" },
	diseaseName: { fontSize: 15, fontWeight: "700", marginBottom: 2 },
	diseaseDesc: { fontSize: 13, lineHeight: 18 },

	bottomBar: { flexDirection: "row", gap: 8, marginTop: 12, paddingHorizontal: 24 },
	cancelBtn: { flex: 1, borderWidth: 1, borderRadius: 12, alignItems: "center", justifyContent: "center", paddingVertical: 14 },
	cancelText: { fontSize: 15, fontWeight: "600" },
	submitBtn: { flex: 2, borderRadius: 12, alignItems: "center", justifyContent: "center", paddingVertical: 14 },
	submitText: { fontWeight: "700", fontSize: 16 },
});
