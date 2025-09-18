// app/(page)/disease-diagnosis.tsx
import React, { useRef, useState } from "react";
import { View, Text, StyleSheet, Image, Pressable, Animated, Easing, useColorScheme } from "react-native";
import Colors from "../../constants/Colors";
import arrowDown from "../../assets/images/arrow_down.png";

// ── 로컬 전용 아코디언 (이 페이지에서만 사용)
function DiseaseAccordionCardLocal({ photoUri, nickname, diagnosedAt, diseaseName, children }: {
	photoUri?: string|null; nickname: string; diagnosedAt: string; diseaseName: string; children?: React.ReactNode;
}) {
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const [open, setOpen] = useState(false);
	const rotate = useRef(new Animated.Value(0)).current;
	const height = useRef(new Animated.Value(0)).current;
	const contentH = useRef(0);
	const arrowRotate = rotate.interpolate({
		inputRange: [0, 1],
		outputRange: ["0deg", "540deg"], // 펼침 시 1 → 540deg
	});

	function toggle() {
		setOpen(prev => {
			const next = !prev;

			// 펼칠 때 회전 0→1 / 닫힐 때 1→0
			if (next) rotate.setValue(0);

			Animated.timing(rotate, {
				toValue: next ? 1 : 0,
				duration: 260,
				useNativeDriver: true,
			}).start();

			Animated.timing(height, {
				toValue: next ? contentH.current : 0,
				duration: 220,
				useNativeDriver: false, // height는 false 필수
			}).start();

			return next;
		});
	}

	return (
		<View style={[styles.card, { borderColor: theme.border, backgroundColor: theme.bg }]}>
			<View style={styles.row}>
				<View style={styles.left}>
					<View style={[styles.photo, { borderColor: theme.border }]}>
						{photoUri ? <Image source={{ uri: photoUri }} style={{ width:"100%", height:"100%", borderRadius:8 }} /> :
							<View style={styles.placeholder}><Text style={{ color: theme.text }}>사진</Text></View>}
					</View>
				</View>
				<View style={styles.right}>
					<View style={[styles.box, { borderColor: theme.border }]}><Text numberOfLines={1} style={[styles.title, { color: theme.text }]}>{nickname} / {diagnosedAt}</Text></View>
					<View style={[styles.box, { borderColor: theme.border, marginTop:6 }]}><Text numberOfLines={1} style={[styles.sub, { color: theme.text }]}>{diseaseName}</Text></View>
				</View>
			</View>

			<Pressable onPress={toggle} style={styles.arrow}>
				<Animated.View style={{ transform: [{ rotate: arrowRotate }] }}>
					<Image source={arrowDown} style={styles.arrowImg}/>
				</Animated.View>
			</Pressable>

			<Animated.View style={{ height, overflow:"hidden" }}>
				<View
					style={{ position: "absolute", left: -9999, opacity: 0 }}
					onLayout={(e) => {
						if (!contentH.current) contentH.current = e.nativeEvent.layout.height;
					}}
					>
					{children}
				</View>
			</Animated.View>
		</View>
	);
}

// ── 아래는 페이지 본문에서 호출
export default function DiseaseDiagnosisPage() {
	return (
		<View style={{ flex:1, padding:16 }}>
			<DiseaseAccordionCardLocal
				nickname="초코(몬스테라)"
				diagnosedAt="2025-09-18"
				diseaseName="잎마름병(추정)"
			>
				<Text>여기에 상세 처방/주의사항 등 표시</Text>
			</DiseaseAccordionCardLocal>
		</View>
	);
}

const styles = StyleSheet.create({
	card:{ borderWidth:1, borderRadius:12, padding:12 },
	row:{ flexDirection:"row" },
	left:{ marginRight:10, justifyContent:"center" },
	photo:{ width:72, height:72, borderWidth:1, borderRadius:8, overflow:"hidden", backgroundColor:"#ddd", alignItems:"center", justifyContent:"center" },
	placeholder:{ flex:1, alignItems:"center", justifyContent:"center" },
	right:{ flex:1 },
	box:{ borderWidth:1, borderRadius:8, paddingHorizontal:10, paddingVertical:8 },
	title:{ fontSize:15, fontWeight:"600" },
	sub:{ fontSize:15, fontWeight:"500" },
	arrow: {
		alignSelf: "center",
		marginTop: 8,
		padding: 6,
	},
	arrowImg: {
		width: 24,          // 원하는 크기
		height: 24,
		tintColor: "#333",  // 다크모드/라이트모드 맞춰서 색 바꾸기 가능
	},
});
