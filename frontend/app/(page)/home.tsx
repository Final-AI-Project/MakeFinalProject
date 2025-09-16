// app/(tabs)/index.tsx
import React, { useMemo, useState } from 'react';
import {
	View,
	Text,
	StyleSheet,
	Dimensions,
	useColorScheme,
	Pressable,
	Image,
} from 'react-native';
import { Link, useRouter } from 'expo-router';
import Colors from "../../constants/Colors";
import WeatherBox from "../../components/common/weatherBox";
import Carousel from 'react-native-reanimated-carousel';

const { width } = Dimensions.get('window');

type Slide = {
	key: string;
	label: string;
	bg: string;
	color?: string;
	species?: string;
	photoUri?: string | null;
	startedAt?: string;
	type?: "action";
};

export default function Home() {
	const router = useRouter();
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const [activeIndex, setActiveIndex] = useState(0);
	const [parentW, setParentW] = useState(0);

	const SIZE = 250;
	const HALF = SIZE / 2;

	// 내 식물 리스트 상태
	const [plants, setPlants] = useState<Slide[]>([
		{ key: "1", label: "몬스테라", bg: theme.bg, color: theme.text },
		{ key: "2", label: "금전수", bg: theme.bg, color: theme.text },
	]);

	const slides = useMemo(() => {
		return [
			...plants,
			{ key: "add", label: "+ \n 새 식물 등록", bg: theme.graybg, type: "action" as const },
		];
	}, [plants, theme]);

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
					width={width}
					height={250}
					data={slides}
					scrollAnimationDuration={700}
					onProgressChange={(_, abs) => setActiveIndex(Math.round(abs))}
					renderItem={({ item }) => (
						<View style={[styles.carouselSlide, { backgroundColor: item.bg }]}>
							{item.type === "action" ? (
								<Pressable onPress={() => router.push("/(page)/(stackless)/plant-new")}>
									<Text style={[styles.carouselSlideText, { color: theme.text, textAlign: 'center' }]}>
										{item.label}
									</Text>
								</Pressable>
							) : (
								<View 
									style={styles.plantCard}
									onLayout={e => setParentW(e.nativeEvent.layout.width)}
								>
									<View style={[styles.slotBox, {left: parentW / 2}]}>
										<View style={styles.slot1} />
										<View
											style={[
												styles.slot2,
												{
													left: parentW / 2,
													transform: [
														{ rotate: '45deg' },
													],
												}
											]}
										/>
										<View style={styles.slot3}/>
										<View style={styles.slot4}/>
									</View>
									{item.photoUri ? (
										// ✅ photoUri가 있는 경우에만 Image 렌더 → 타입 안전
										<Image
											source={{ uri: item.photoUri }}
											style={styles.plantImage}
											resizeMode="cover"
										/>
									) : (
										// ✅ placeholder
										<View style={styles.plantImagePlaceholder}>
											<Text style={{ color: theme.text }}>🌱</Text>
										</View>
									)}
									<Text style={[styles.plantName, {color:theme.text}]}>{item.label}</Text>
									{item.species && (
										<Text style={styles.plantSpecies}>{item.species}</Text>
									)}
								</View>
							)}
						</View>
					)}
				/>
				<View style={styles.carouselDots}>
					{slides.map((_, i) => (
						<View key={String(i)} style={[styles.carouselDot, i === activeIndex && styles.carouselDotActive]} />
					))}
				</View>
			</View>
			
			<View style={styles.linkList}>
				<Link style={styles.newPlant} href="/(page)/(stackless)/plant-new">
					<Text style={{ color: "#fff" }}>타임랩스를 경험해 보세요</Text>
				</Link>
				<Link style={styles.plantInfo} href="/(auth)/login">
					{/* ✅ 잘못된 색상코드 '#1a1a1' → '#1a1a1a'로 수정 */}
					<Text style={{ color: "#1a1a1a" }}>식물 정보방</Text>
				</Link>
			</View>
		</View>
	);
}

/** 스타일 (캐러셀/페이지용만 남김) */
const styles = StyleSheet.create({
	container: {
		flex: 1,
		paddingTop: 20,
		paddingHorizontal: 24,
		paddingBottom: 68,
	},
	// 캐러셀
	plantCard: {
		flex: 1,
		justifyContent: "center",
		alignItems: "center",
		width: '100%',
		padding: 16,
	},
	plantImage: {
		width: 120,
		height: 120,
		borderRadius: 60,
		marginTop:100,
		marginBottom: 12,
	},
	plantImagePlaceholder: {
		overflow: "hidden",
		width: 120,
		height: 120,
		borderRadius: 60,
		marginTop:100,
		marginBottom: 12,
		backgroundColor: "#ccc",
		justifyContent: "center",
		alignItems: "center",
	},
	plantName: {
		fontSize: 20,
		fontWeight: "700",
	},
	plantSpecies: {
		fontSize: 14,
		color: "#eee",
		marginTop: 4,
	},
	/*  */
	slotBox: {
		overflow:'hidden',
		position: 'absolute',
		top:20,
		width: 250,
		height: 250,
		transform: [{ translateX: -125 }],
		borderRadius: '100%',
		backgroundColor: 'red',
	},
	slot1: {
		position: 'absolute',
		top:0,
		width: 250,
		height: 250,
		transform: [{ translateX: -125 }],
		borderRadius: '100%',
		backgroundColor: 'red',
	},
	slot2: {
		overflow: 'hidden',
		position: 'absolute',
		top:0,
		width: 500,
		height: 500,
		marginLeft:-250,
		backgroundColor: '#e6e6e6',
	},
	slot3: {
		position: 'absolute',
		top:75,
		width: 150,
		height: 150,
		transform: [{ translateX: -75 }],
		borderRadius: '100%',
	},
	slot4: {
		position: 'absolute',
		top:160,
		width: '100%',
		height: '100%',
	},
	/*  */
	carouselRoot: {
		height: 250,
		alignSelf: 'stretch',
		marginBottom: 8,
		paddingHorizontal: 24,
		justifyContent: 'center',
		alignItems: 'center',
	},
	carouselSlide: {
		flex: 1,
		justifyContent: 'center',
		alignItems: 'center',
	},
	carouselSlideText: { color: '#fff', fontSize: 28, fontWeight: 'bold' },
	carouselDots: { position: 'absolute', bottom: -19, flexDirection: 'row', gap: 6 },
	carouselDot: { width: 6, height: 6, borderRadius: 4, backgroundColor: '#cfcfcf' },
	carouselDotActive: { backgroundColor: '#333' },
	linkList: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		flexDirection: 'row',
		gap: 8,
		marginTop:24,
	},
	newPlant: {
		flex: 1,
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'flex-end',
		height: 160,
		paddingHorizontal: 20,
		paddingVertical: 16,
		borderRadius: 16,
		textAlign: 'right',
		backgroundColor: '#00c73c',
		fontSize: 17,
	},
	plantInfo: {
		flex: 1,
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'flex-end',
		height: 160,
		paddingHorizontal: 20,
		paddingVertical: 16,
		borderRadius: 16,
		textAlign: 'right',
		backgroundColor: '#ffc900',
		fontSize: 17,
	},
});
