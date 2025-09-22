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
import { getApiUrl } from "../../../config/api";
import { getToken } from "../../../libs/auth";

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

	// 진단 결과 상태
	const [diagnosisResult, setDiagnosisResult] = useState<{
		healthStatus: string;
		healthConfidence: number;
		message: string;
		recommendation: string;
		diseasePredictions: any[];
	} | null>(null);

	// 내 식물(별명) - 실제 API에서 가져오기
	const [myPlants, setMyPlants] = useState<{ label: string; value: string }[]>([]);
	const [plantsLoading, setPlantsLoading] = useState(true);

	// 식물 목록 가져오기
	useEffect(() => {
		const fetchMyPlants = async () => {
			try {
				const token = await getToken();
				if (!token) return;

				const apiUrl = await getApiUrl("/home/plants/current");
				const response = await fetch(apiUrl, {
					method: "GET",
					headers: {
						Authorization: `Bearer ${token}`,
						"Content-Type": "application/json",
					},
				});

				if (response.ok) {
					const data = await response.json();
					if (data.plants && Array.isArray(data.plants)) {
						const plantOptions = data.plants.map((plant: any) => ({
							label: `${plant.plant_name} (${plant.species || "기타"})`,
							value: plant.plant_name,
						}));
						setMyPlants(plantOptions);
					}
				}
			} catch (error) {
				console.error("식물 목록 가져오기 실패:", error);
			} finally {
				setPlantsLoading(false);
			}
		};

		fetchMyPlants();
	}, []);

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
		setDiagnosisResult(null);
		setInferBusy(false);
	};

	// 제출 가능 조건
	const canSubmit = Boolean(photoUri && selectedPlant && isMine === "mine");

	// 등록
	const handleSubmit = async () => {
		if (!canSubmit) return;
		
		try {
			const token = await getToken();
			if (!token) {
				Alert.alert("오류", "로그인이 필요합니다.");
				return;
			}

			// 진단 결과 저장
			if (candidates.length > 0) {
				const formData = new FormData();
				formData.append("plant_id", "1"); // TODO: 실제 식물 ID로 교체
				formData.append("pest_id", "1"); // TODO: 실제 병충해 ID로 교체
				formData.append("pest_date", date);

				// 이미지가 있으면 추가
				if (photoUri) {
					formData.append("image", {
						uri: photoUri,
						type: "image/jpeg",
						name: "diagnosis.jpg",
					} as any);
				}

				const apiUrl = await getApiUrl("/medical/diagnoses/with-image");
				const response = await fetch(apiUrl, {
					method: "POST",
					body: formData,
					headers: {
						Authorization: `Bearer ${token}`,
						"Content-Type": "multipart/form-data",
					},
				});

				if (!response.ok) {
					throw new Error(`저장 실패: ${response.status}`);
				}
			}

			Alert.alert("등록 완료", "진단 결과가 저장되었습니다.");
			router.back();
		} catch (error) {
			console.error("저장 오류:", error);
			Alert.alert("저장 실패", "진단 결과 저장 중 문제가 발생했습니다.");
		}
	};

	// 모델 연동
	const runDiagnosis = async (uri: string) => {
		try {
			setInferBusy(true);
			setDiagnosisResult(null); // 초기화

			// 실제 백엔드 API 호출
			const token = await getToken();
			if (!token) {
				throw new Error("로그인이 필요합니다.");
			}

			const formData = new FormData();
			formData.append("image", {
				uri: uri,
				type: "image/jpeg",
				name: "disease.jpg",
			} as any);

			const apiUrl = await getApiUrl("/disease-diagnosis/diagnose");
			console.log("진단 API URL:", apiUrl);
			
			const response = await fetch(apiUrl, {
				method: "POST",
				body: formData,
				headers: {
					Authorization: `Bearer ${token}`,
				},
			});

			console.log("진단 응답 상태:", response.status);

			if (!response.ok) {
				const errorText = await response.text();
				console.error("진단 API 오류:", errorText);
				throw new Error(`진단 실패: ${response.status} - ${errorText}`);
			}

			const result = await response.json();
			console.log("진단 결과:", result);
			
			if (result.success) {
				setDiagnosisResult({
					healthStatus: result.health_status,
					healthConfidence: result.health_confidence,
					message: result.message,
					recommendation: result.recommendation,
					diseasePredictions: result.disease_predictions || []
				});
			} else {
				throw new Error("진단 결과를 받을 수 없습니다.");
			}
		} catch (e) {
			console.error("진단 오류:", e);
			Alert.alert("진단 실패", `사진 진단 중 문제가 발생했습니다: ${e.message}`);
			setDiagnosisResult(null);
		} finally {
			setInferBusy(false);
		}
	};

	// 진단 결과 표시 함수
	const getDiagnosisDisplay = () => {
		if (!photoUri) return { type: "empty", title: "사진을 등록하세요", desc: "" };
		if (inferBusy) return { type: "loading", title: "진단 중…", desc: "" };
		
		if (!diagnosisResult) return { type: "empty", title: "병충해 진단", desc: "" };
		
		// 건강한 경우
		if (diagnosisResult.healthStatus === "healthy") {
			return {
				type: "healthy",
				title: "건강한 식물입니다!",
				desc: diagnosisResult.recommendation,
				confidence: diagnosisResult.healthConfidence
			};
		}
		
		// 건강하지 않은 경우 - 병충해 진단 결과 표시
		return {
			type: "diseased",
			title: diagnosisResult.message,
			desc: diagnosisResult.recommendation,
			diseases: diagnosisResult.diseasePredictions
		};
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
							placeholder={plantsLoading ? "식물 목록 로딩 중..." : "내 식물을 선택하세요"}
							theme={theme}
							style={{ marginTop: 0 }}
						/>
					</View>
				)}

				{/* 4) 진단 결과 표시 */}
				<View style={{ marginTop: 8, paddingHorizontal: 24 }}>
					{(() => {
						const display = getDiagnosisDisplay();
						
						if (display.type === "healthy") {
							// 건강한 경우 - 단일 박스
							return (
								<View style={[styles.rowBox, { borderColor: "#4CAF50", backgroundColor: "#E8F5E8", marginBottom: 8 }]}>
									<Text style={[styles.rank, { color: "#2E7D32" }]}>✓</Text>
									<View style={{ flex: 1 }}>
										<Text style={[styles.diseaseName, { color: "#2E7D32" }]}>{display.title}</Text>
										<Text style={[styles.diseaseDesc, { color: "#2E7D32", opacity: 0.8 }]}>
											{display.desc}
										</Text>
										<Text style={[styles.diseaseDesc, { color: "#2E7D32", opacity: 0.6, fontSize: 12 }]}>
											신뢰도: {(display.confidence * 100).toFixed(1)}%
										</Text>
									</View>
								</View>
							);
						} else if (display.type === "diseased" && display.diseases) {
							// 병충해 진단 결과 - 상위 3개 표시
							return display.diseases.map((disease, idx) => (
								<View key={idx} style={[styles.rowBox, { borderColor: theme.border, marginBottom: 8 }]}>
									<Text style={[styles.rank, { color: theme.text }]}>{disease.rank}.</Text>
									<View style={{ flex: 1 }}>
										<Text style={[styles.diseaseName, { color: theme.text }]}>{disease.class_name}</Text>
										<Text style={[styles.diseaseDesc, { color: theme.text, opacity: 0.8 }]}>
											신뢰도: {(disease.confidence * 100).toFixed(1)}%
										</Text>
									</View>
								</View>
							));
						} else {
							// 기본 상태 (사진 없음, 로딩 중 등)
							return (
								<View style={[styles.rowBox, { borderColor: theme.border, marginBottom: 8 }]}>
									<Text style={[styles.rank, { color: theme.text }]}>1.</Text>
									<View style={{ flex: 1 }}>
										<Text style={[styles.diseaseName, { color: theme.text }]}>{display.title}</Text>
										{!!display.desc && (
											<Text style={[styles.diseaseDesc, { color: theme.text, opacity: 0.8 }]}>{display.desc}</Text>
										)}
									</View>
								</View>
							);
						}
					})()}
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
