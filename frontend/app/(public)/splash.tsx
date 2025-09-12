import React, { useEffect } from "react";
import { View, StyleSheet, Dimensions, useColorScheme } from "react-native";
import { router } from "expo-router";
import { getToken } from "../../libs/auth";
import Animated, { Keyframe } from "react-native-reanimated";
import logoImage from "../../assets/images/logo_image.png";
import logoTextLight from "../../assets/images/logo_text.png";
import logoTextDark from "../../assets/images/d_logo_text.png";
import Colors from "../../constants/Colors";

const LogoTextAni = new Keyframe({
	0:   { transform: [{ rotate: "90deg" }] },
	80:  { transform: [{ rotate: "0deg" }] },
	90:  { transform: [{ rotate: "5deg" }] },
	100: { transform: [{ rotate: "0deg" }] },
}).duration(800)

const LogoImageAni = new Keyframe({
	0:   { transform: [{ scaleX: 1   }, { scaleY: 0 }] },
	100: { transform: [{ scaleX: 1   }, { scaleY: 1 }] },
}).duration(400).delay(800)

export default function SplashScreen() {
	const scheme = useColorScheme();
  	const theme = Colors[scheme === "dark" ? "dark" : "light"];
	const logoTextSource = scheme === "dark" ? logoTextDark : logoTextLight;

	useEffect(() => {
		(async () => {
			const token = await getToken();
			setTimeout(() => {
				if (token) router.replace("/(main)/home");
				else router.replace("/(auth)/login");
			}, 3200); // 살짝 노출용 딜레이 (옵션) 3200
		})();
	}, []);

	return (
		<View style={styles.opningBox}>
			<Animated.Image 
				source={logoImage}
				entering={LogoImageAni}
				style={[styles.opningImage, { backgroundColor: theme.bg }]}
				resizeMode="cover"
			/>
			<Animated.Image 
				source={logoTextSource} 
				entering={LogoTextAni}
				style={styles.opningText} 
				resizeMode="cover" 
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
		padding:0,
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
	}
});