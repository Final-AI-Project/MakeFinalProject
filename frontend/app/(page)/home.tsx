// app/(tabs)/index.tsx
// ─────────────────────────────────────────────────────────────────────────────
// ① Imports
// ─────────────────────────────────────────────────────────────────────────────
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
import { LinearGradient } from "expo-linear-gradient";
import Animated, { useAnimatedStyle, useSharedValue, withTiming, useAnimatedReaction } from 'react-native-reanimated';

// ─────────────────────────────────────────────────────────────────────────────
// ② Types & Constants
// ─────────────────────────────────────────────────────────────────────────────
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
	waterLevel?: number;
	health?: "좋음" | "주의" | "나쁨";
};

// ─────────────────────────────────────────────────────────────────────────────
// ③ Component
// ─────────────────────────────────────────────────────────────────────────────
export default function Home() {
	// 3-1) Router & Theme
	const router = useRouter();
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];

	// 3-2) Shared/Local States
	const progress = useSharedValue(0);
	const [activeIndex, setActiveIndex] = useState(0);
	const [parentW, setParentW] = useState(0);

	// 3-3) Gauge layout constants
	const SIZE = 250;
	const HALF = SIZE / 2;

	// 3-4) Data: Plants & Slides
	const [plants, setPlants] = useState<Slide[]>([
		{ key: "1", label: "몬스테라", bg: theme.bg, color: theme.text, waterLevel: 75, species: "몬스테라", startedAt: "2025-05-01", photoUri: null, health: "좋음" },
		{ key: "2", label: "금전수", bg: theme.bg, color: theme.text, waterLevel: 30, species: "금전수", startedAt: "2025-06-10", photoUri: null, health: "주의" },
	]);

	const slides = useMemo(() => {
		return [
			...plants,
			{ key: "add", label: "+ \n 새 식물 등록", bg: theme.graybg, type: "action" as const },
		];
	}, [plants, theme]);

	// ─────────────────────────────────────────────────────────────────────────
	// 3-5) UI Sub-Component: AnimatedGauge (water level needle)
	// ─────────────────────────────────────────────────────────────────────────
	const AnimatedGauge = React.memo(function AnimatedGauge({
		index,
		progress,
		size,
		targetDeg,
		style,
	}: {
		index: number;
		progress: ReturnType<typeof useSharedValue<number>>;
		size: number;
		targetDeg: number;     // 0~180 (급수계 각도)
		style?: any;
	}) {
		// 현재 회전 각도(숫자)를 보관
		const rot = useSharedValue(0);

		// 보이는지 여부에 따라 rot를 0 ↔ targetDeg로 부드럽게 이동
		useAnimatedReaction(
			() => {
				const visible = Math.abs(progress.value - index) < 0.5; // 중앙 근처 = 보임
				return visible ? targetDeg : 0;
			},
			(to, prev) => {
				if (to !== prev) {
					rot.value = withTiming(to, { duration: 500 });
				}
			}
		);

		const slot2AnimatedStyle = useAnimatedStyle(() => ({
			transform: [
				{ translateY: -size / 2 }, 
				{ rotate: `${rot.value}deg` },
				{ translateY:  size / 2 },
			],
		}));

		return <Animated.View style={[style, slot2AnimatedStyle]} />;
	});

	// ─────────────────────────────────────────────────────────────────────────
	// 3-6) Render
	// ─────────────────────────────────────────────────────────────────────────
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
					defaultIndex={0}
					onProgressChange={(_, abs) => {
						progress.value = abs;
						setActiveIndex(Math.round(abs));
					}}
					renderItem={({ item, index }) => {
						// 급수계(%) → 각도(0~180deg) 변환
						const percent = Math.max(0, Math.min(100, item.waterLevel ?? 0));
						const targetDeg = percent * 1.8; // (percent / 100) * 180

						return (
							<View style={[styles.carouselSlide, { backgroundColor: item.bg }]}>
								{item.type === "action" ? (
									<Pressable onPress={() => router.push("/(page)/(stackless)/plant-new")}>
										<Text style={[styles.carouselSlideText, { color: theme.text, textAlign: 'center' }]}>
											{item.label}
										</Text>
									</Pressable>
								) : (
									/* ── [MINIMAL CHANGE] 식물 카드 전체를 눌러 상세로 이동 */
									<Pressable
										style={styles.plantCard}
										onLayout={e => setParentW(e.nativeEvent.layout.width)}
										onPress={() =>
											router.push({
												pathname: "/(page)/(stackless)/plant-detail",
												params: {
													id: item.key,
													imageUri: item.photoUri ?? "",
													nickname: item.label,
													species: item.species ?? "",
													startedAt: item.startedAt ?? "",
												},
											})
										}
									>
										{/* Gauge slots */}
										<View style={[styles.slotBox, { left: parentW / 2 }]}>
											<View style={styles.slot1} />
											<AnimatedGauge
												index={index}
												progress={progress}
												size={250}
												targetDeg={targetDeg}
												style={styles.slot2}
											/>
											<View style={[styles.slot3, { backgroundColor: theme.bg }]} />
										</View>

										<View style={[styles.slot4, { backgroundColor: theme.bg }]} />

										{/* Plant image */}
										<View style={ styles.photoBox }>
											{item.photoUri ? (
												<Image source={{ uri: item.photoUri }} style={styles.plantImage} resizeMode="cover" />
											) : (
												<View style={styles.plantImagePlaceholder}>
													<Text style={{ color: theme.text }}>🌱</Text>
												</View>
											)}
											
											{/* ✨ 상태에 따라 표시 */}
											{(item.health === "주의" || item.health === "나쁨" ) && (
												<View
													style={[
														styles.medicalInfo,
														item.health === "주의" ? { backgroundColor: "#ffc900" } : { backgroundColor: "#d32f2e" },
													]}
												/>
											)}
										</View>

										{/* Labels */}
										<Text style={[styles.plantName, { color: theme.text }]}>{item.label}
											{item.species && <Text style={[styles.plantSpecies, { color: theme.text }]}>({item.species})</Text>}
										</Text>
									</Pressable>
								)}
							</View>
						);
					}}
				/>
				{/* Dots */}
				<View style={styles.carouselDots}>
					{slides.map((_, i) => (
						<View key={String(i)} style={[styles.carouselDot, i === activeIndex && styles.carouselDotActive]} />
					))}
				</View>
			</View>
			
			{/* Links */}
			<View style={styles.linkList}>
				{/* newPlant */}
				<Link href="/(page)/(stackless)/plant-new" asChild>
					<Pressable style={styles.cardBase}>
						<LinearGradient
							colors={["#F97794", "#623AA2"]}
							start={{ x: 0, y: 0 }}
							end={{ x: 1, y: 1 }}
							style={StyleSheet.absoluteFillObject}
						/>
						<Text style={styles.cardTextLight}>타임랩스를 경험해 보세요</Text>
					</Pressable>
				</Link>
				
				{/* plantInfo */}
				<Link href="/(auth)/login" asChild>
					<Pressable style={styles.cardBase}>
						<LinearGradient
							colors={["#FFF6B7", "#F6416C"]}
							start={{ x: 0, y: 0 }}
							end={{ x: 1, y: 1 }}
							style={StyleSheet.absoluteFillObject}
						/>
						<Text style={styles.cardTextLight}>식물 정보방</Text>
					</Pressable>
				</Link>
			</View>
			
		</View>
	);
}

// ─────────────────────────────────────────────────────────────────────────────
// ④ Styles (섹션별 주석 유지)
// ─────────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
	container: {
		flex: 1,
		paddingTop: 20,
		paddingHorizontal: 24,
		paddingBottom: 68,
	},

	// ── Carousel card & image
	plantCard: {
		flex: 1,
		justifyContent: "center",
		alignItems: "center",
		width: '100%',
		padding: 16,
	},
	photoBox: {
		position:'relative',
		width: 120,
		height: 120,
		borderRadius: 60,
		marginTop:75,
	},
	plantImage: {
		width: 120,
		height: 120,
		borderRadius: 60,
		objectFit: 'cover',
	},
	plantImagePlaceholder: {
		overflow: "hidden",
		width: 120,
		height: 120,
		borderRadius: 60,
		backgroundColor: "#ccc",
		justifyContent: "center",
		alignItems: "center",
	},
	medicalInfo: {
		position:'absolute',
		right:0,
		bottom:0,
		width:36,
		height:36,
		borderRadius:18,
		justifyContent:'center',
		alignItems:'center',
	},
	plantName: {
		fontSize: 20,
		fontWeight: "700",
	},
	plantSpecies: {
		fontSize: 14,
		marginTop: 4,
	},

	// ── Gauge slots
	slotBox: {
		overflow:'hidden',
		position: 'absolute',
		top:20,
		width: 250,
		height: 250,
		transform: [{ translateX: -125 }],
		borderRadius: '100%',
	},
	slot1: {
		position: 'absolute',
		top:0,
		width: 250,
		height: 125,
		backgroundColor:'#e6e6e6',
	},
	slot2: {
		position: 'absolute',
		top:125,
		width: '100%',
		height: '100%',
		backgroundColor: '#6a9eff',
		transitionProperty:'transform',
		transitionDuration:'0.5s'
	},
	slot3: {
		position: 'absolute',
		top:40,
		left:-45,
		transform:[{ translateX:'50%' }],
		width: 170,
		height: 170,
		borderRadius: '100%',
	},
	slot4: {
		position: 'absolute',
		top:145,
		width: 290,
		height: 290,
		transform:[{ translateX:-20 }],
	},

	// ── Carousel wrapper
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
	carouselDotActive: { backgroundColor: '#666' },

	// ── Link cards
	linkList: {
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "center",
		gap: 8,
		marginTop: 24,
	},
	cardBase: {
		flex: 1,
		height: 160,
		borderRadius: 16,
		paddingHorizontal: 20,
		paddingVertical: 16,
		alignItems: "center",
		justifyContent: "flex-end",
		overflow: "hidden",
		
	},
	cardTextLight: { width:'100%', color: "#fff", fontSize: 17, fontWeight: "600", textAlign:'right' },
});
