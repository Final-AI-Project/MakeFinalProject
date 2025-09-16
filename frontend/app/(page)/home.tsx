// app/(tabs)/index.tsx
import React, { useMemo, useState } from 'react';
import { View, Text, StyleSheet, Dimensions, useColorScheme, Pressable } from 'react-native';
import { Link, useRouter } from 'expo-router';
import Colors from "../../constants/Colors";
import WeatherBox from "../../components/common/weatherBox";
import Carousel from 'react-native-reanimated-carousel';

const { width } = Dimensions.get('window');

type Slide = {
    key: string;
    label: string;   // ex) 별명
    bg: string;
    species?: string;
    photoUri?: string;
    startedAt?: string;
};

export default function Home() {
	const router = useRouter();
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];

	// 내 식물 리스트 상태
	const [plants, setPlants] = useState<Slide[]>([
		{ key: "1", label: "몬스테라", bg: "#9DD6EB" },
		{ key: "2", label: "금전수", bg: "#97CAE5" },
	]);

	// 캐러셀 전체 데이터 = 내 식물 + 등록하기 버튼
	const slides = useMemo(() => {
		return [
			...plants,
			{ key: "add", label: "새 식물 등록 +", bg: theme.graybg, type: "action" },
		];
	}, [plants, theme]);

	// 새 식물 등록 → plants 맨 앞에 추가 (예시)
	function addPlant() {
		const newPlant: Slide = {
			key: Date.now().toString(),
			label: "스투키",
			bg: "#92BBD9",
		};
		setPlants((prev) => [newPlant, ...prev]);
	}

	return (
		<View style={[styles.container, { backgroundColor: theme.bg }]}>
			{/* ✅ 공통 날씨 컴포넌트만 사용 */}
			<WeatherBox
				serviceKey="GTr1cI7Wi0FRbOTFBaUzUCzCDP4OnyyEmHnn11pxCUC5ehG5bQnbyztgeydnOWz1O04tjw1SE5RsX8RNo6XCgQ==" 
				location={{ lat: 37.4836, lon: 127.0326, label: "서울시 - 서초구" }}
			/>

			{/* 캐러셀 */}
			<View style={styles.carouselRoot}>
				<Carousel
					loop={false}
					width={width - 32}
					height={250}
					data={slides}
					scrollAnimationDuration={700}
					renderItem={({ item }) => (
						<View style={[styles.carouselSlide, { backgroundColor: item.bg }]}>
							{item.type === "action" ? (
								<Pressable onPress={() => router.push("../(stackless)/plant-new")}>
									<Text style={[styles.carouselSlideText, { color: "#fff" }]}>
										{item.label}
									</Text>
								</Pressable>
							) : (
								<View style={styles.plantCard}>
									{item.photoUri ? (
										<Image
											source={{ uri: item.photoUri }}
											style={styles.plantImage}
											resizeMode="cover"
										/>
									) : (
										<View style={styles.plantImagePlaceholder}>
											<Text style={{ color: "#fff" }}>🌱</Text>
										</View>
									)}
									<Text style={styles.plantName}>{item.label}</Text>
									{item.species && (
										<Text style={styles.plantSpecies}>{item.species}</Text>
									)}
								</View>
							)}
						</View>
					)}

				/>
			</View>
			
			<View style={styles.linkList}>
				<Link style={styles.newPlant} href="../(stackless)/plant-new">
					<Text style={{ color: "#fff" }}>타임랩스를 경험해 보세요</Text>
				</Link>
				<Link style={styles.plantInfo} href="../(auth)/login">
					<Text style={{ color: "#1a1a1" }}>식물 정보방</Text>
				</Link>
			</View>
		</View>
	);
}

/** 스타일 (캐러셀/페이지용만 남김) */
const styles = StyleSheet.create({
	container: {
		flex: 1,
		paddingTop:20,
		paddingHorizontal:24,
		paddingBottom:0,
	},
	// 캐러셀
	plantCard: {
		flex: 1,
		justifyContent: "center",
		alignItems: "center",
		borderRadius: 16,
		padding: 16,
	},
	plantImage: {
		width: 120,
		height: 120,
		borderRadius: 60,
		marginBottom: 12,
	},
	plantImagePlaceholder: {
		width: 120,
		height: 120,
		borderRadius: 60,
		marginBottom: 12,
		backgroundColor: "#ccc",
		justifyContent: "center",
		alignItems: "center",
	},
	plantName: {
		fontSize: 20,
		fontWeight: "700",
		color: "#fff",
	},
	plantSpecies: {
		fontSize: 14,
		color: "#eee",
		marginTop: 4,
	},

	carouselRoot: {
		height: 250,
		alignSelf: 'stretch',
		marginTop: 4,
		marginBottom: 8,
		justifyContent: 'center',
		alignItems: 'center',
	},
	carouselSlide: {
		flex: 1,
		borderRadius: 16,
		justifyContent: 'center',
		alignItems: 'center',
	},
	carouselSlideText: { color: '#fff', fontSize: 28, fontWeight: 'bold' },
	carouselDots: { position: 'absolute', bottom: 8, flexDirection: 'row', gap: 6 },
	carouselDot: { width: 6, height: 6, borderRadius: 4, backgroundColor: '#cfcfcf' },
	carouselDotActive: { backgroundColor: '#333' },
	linkList: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		flexDirection: 'row',
		gap: 8,
	},
	newPlant: {
		flex:1,
		display:'flex',
		alignItems:'center',
		justifyContent:'flex-end',
		height:160,
		paddingHorizontal:20,
		paddingVertical:16,
		borderRadius: 16,
		textAlign:'right',
		backgroundColor:'#00c73c',
		fontSize:17,
	},
	plantInfo: {
		flex:1,
		display:'flex',
		alignItems:'center',
		justifyContent:'flex-end',
		height:160,
		paddingHorizontal:20,
		paddingVertical:16,
		borderRadius: 16,
		textAlign:'right',
		backgroundColor:'#ffc900',
		fontSize:17,
	},
});
