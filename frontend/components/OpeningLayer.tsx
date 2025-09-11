// frontend/components/OpeningLayer.tsx
import Animated from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

export default function OpeningLayer() {
	const insets = useSafeAreaInsets();

	return (
		<Animated.View
			style={{
				position: "absolute",
				left: 0,
				right: 0,
				top: insets.top,		 // ← 노치/상태바 만큼 띄우기
				bottom: insets.bottom,	 // ← 홈바/내비게이션바 만큼 띄우기
			}}
		>
		</Animated.View>
	);
}
