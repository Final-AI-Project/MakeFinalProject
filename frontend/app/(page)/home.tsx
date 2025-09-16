// app/(tabs)/index.tsx
import React, { useMemo, useState } from 'react';
import { View, Text, StyleSheet, Dimensions, useColorScheme } from 'react-native';
import { Link, useRouter } from 'expo-router';
import Colors from "../../constants/Colors";
import WeatherBox from "../../components/common/weatherBox";
import Carousel from 'react-native-reanimated-carousel';

const { width } = Dimensions.get('window');

export default function Home() {
	const router = useRouter();
	const scheme = useColorScheme();
	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	
	// 캐러셀 상태만 유지
	const [activeIndex, setActiveIndex] = useState(0);
	const slides = useMemo(() => ([
		{ key: '1', label: 'Hello Carousel', bg: '#9DD6EB'},
		{ key: '2', label: 'Beautiful', bg: '#97CAE5'},
		{ key: '3', label: 'And simple', bg: '#92BBD9'},
	]), []);

	return (
		<View style={[styles.container, {backgroundColor: theme.bg}]}>
			{/* ✅ 공통 날씨 컴포넌트만 사용 */}
			<WeatherBox
				serviceKey="GTr1cI7Wi0FRbOTFBaUzUCzCDP4OnyyEmHnn11pxCUC5ehG5bQnbyztgeydnOWz1O04tjw1SE5RsX8RNo6XCgQ==" 
				location={{ lat: 37.4836, lon: 127.0326, label: "서울시 - 서초구" }}
			/>

			{/* 기존 캐러셀 뼈대 유지 */}
			<View style={styles.carouselRoot}>
				<Carousel
					loop
					width={width - 32}
					height={250}
					data={slides}
					scrollAnimationDuration={700}
					onSnapToItem={(index) => setActiveIndex(index)}
					renderItem={({ item }) => (
					<View style={[styles.carouselSlide, { backgroundColor: item.bg }]}>
						<Text style={styles.carouselSlideText}>{item.label}</Text>
					</View>
					)}
				/>
				<View style={styles.carouselDots}>
					{slides.map((_, i) => (
					<View
						key={i}
						style={[styles.carouselDot, i === activeIndex && styles.carouselDotActive]}
					/>
					))}
				</View>
			</View>

			<View style={styles.linkList}>
				<Link style={styles.newPlant} href="../(stackless)/plant-new">
					<Text style={{ color: "#fff" }}>새 식물 등록</Text>
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
