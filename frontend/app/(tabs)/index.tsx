// app/(tabs)/index.tsx
import React, { useMemo, useState } from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import Carousel from 'react-native-reanimated-carousel';
import WeatherBox from "../common/weatherBox";

const { width } = Dimensions.get('window');

export default function Home() {
	// 캐러셀 상태만 유지
	const [activeIndex, setActiveIndex] = useState(0);
	const slides = useMemo(() => ([
	{ key: '1', label: 'Hello Carousel', bg: '#9DD6EB' },
	{ key: '2', label: 'Beautiful',		bg: '#97CAE5' },
	{ key: '3', label: 'And simple',	 bg: '#92BBD9' },
	]), []);

	return (
	<View style={styles.container}>
		{/* ✅ 공통 날씨 컴포넌트만 사용 */}
		<WeatherBox
		serviceKey="GTr1cI7Wi0FRbOTFBaUzUCzCDP4OnyyEmHnn11pxCUC5ehG5bQnbyztgeydnOWz1O04tjw1SE5RsX8RNo6XCgQ==" 
		// 실제 키가 이미 있으면 그 값 그대로 두세요
		location={{ lat: 37.5665, lon: 126.9780, label: "서울시 - 중구" }}
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
	</View>
	);
}

/** 스타일 (캐러셀/페이지용만 남김) */
const styles = StyleSheet.create({
	container: {
	flex: 1,
	alignItems: 'stretch',
	backgroundColor: '#f0f0f0',
	padding: 24,
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
});
