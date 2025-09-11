import React, { useEffect } from "react";
import { View, StyleSheet, Dimensions, SafeAreaView } from "react-native";
import { router } from "expo-router";
import { getToken } from "../../lib/auth";
import Animated, { Keyframe } from "react-native-reanimated";
import logoImage from "../../assets/images/logo_image.png";
import logoText from "../../assets/images/logo_text.png";

const LogoTextAni = new Keyframe({
	0:   { transform: [{ rotate: "90deg" }] },
	80:  { transform: [{ rotate: "0deg" }] },
	90:  { transform: [{ rotate: "5deg" }] },
	100: { transform: [{ rotate: "0deg" }] },
}).duration(800)

const LogoImageAni = new Keyframe({
	0:   { transform: [{ scaleX: 1   }, { scaleY: 0 }] },
	20:  { transform: [{ scaleX: 1.4 }, { scaleY: 0.2 }] },
	40:  { transform: [{ scaleX: 1.3 }, { scaleY: 0.2 }] },
	60:  { transform: [{ scaleX: 1.2 }, { scaleY: 0.2 }] },
	80:  { transform: [{ scaleX: 1   }, { scaleY: 1 }] },
	100: { transform: [{ scaleX: 1   }, { scaleY: 1 }] },
}).duration(400).delay(800)

const windowHei = Dimensions.get("window").height + 50;
const opningShow = new Keyframe({
	0:   { transform: [{ translateY: -windowHei }] },
	100: { transform: [{ translateY: 0 }] },
}).duration(600).delay(1600)

export default function SplashScreen() {
	useEffect(() => {
		(async () => {
			const token = await getToken();
			setTimeout(() => {
				if (token) router.replace("/(main)/home");
				else router.replace("/(auth)/login");
			}, 300000); // 살짝 노출용 딜레이 (옵션)
		})();
	}, []);

	return (
		<View style={styles.opningBox}>
			<Animated.Image 
				source={logoImage}
				entering={LogoImageAni}
				style={styles.opningImage}
				resizeMode="cover"
			/>
			<Animated.Image 
				source={logoText} 
				entering={LogoTextAni}
				style={styles.opningText} 
				resizeMode="cover" 
			/>
			<Animated.View
				entering={opningShow}
				style={styles.opningShowingBox} 
			/>
		</View>
	);
}

const styles = StyleSheet.create({
	opningBox: {
		display:'flex',
		justifyContent:'center',
		alignItems: 'center',
		position:'fixed',
		left:0,
		top:0,
		width:'100%',
		height:'100%',
		backgroundColor:'red',
	},
	opningImage: {
		width: 140,
		height:140,
		marginBottom:10,
		transformOrigin:'bottom',
	},
	opningText: {
		width: 140,
		height:30,
		transformOrigin:'right',
	},
	opningShowingBox: {
		position:'absolute',
		left:0,
		top:0,
		width:'100%',
		height:'100%',
		backgroundColor:'green',
	}
});