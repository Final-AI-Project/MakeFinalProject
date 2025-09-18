import { useEffect, useMemo, useState } from "react";
import { Keyboard, KeyboardEvent, Platform } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

/**
 * 안드로이드 기준:
 * - 키보드 열릴 때 endCoordinates.height 로 실제 높이 획득
 * - bottom inset(내비게이션 바/홈 인디케이터)을 빼서 과도 상승 방지
 * - iOS는 패스(요청사항), 하지만 호환은 유지
 */
export default function useKeyboardPadding(extra: number = 0) {
	const insets = useSafeAreaInsets();
	const [kbHeight, setKbHeight] = useState(0);
	const [visible, setVisible] = useState(false);

	useEffect(() => {
		const onShow = (e: KeyboardEvent) => {
			const h = e.endCoordinates?.height ?? 0;
			setKbHeight(h);
			setVisible(true);
		};
		const onHide = () => {
			setKbHeight(0);
			setVisible(false);
		};

		// Android는 did 이벤트를 주로 사용
		const subShow =
			Platform.OS === "ios"
				? Keyboard.addListener("keyboardWillShow", onShow)
				: Keyboard.addListener("keyboardDidShow", onShow);

		const subHide =
			Platform.OS === "ios"
				? Keyboard.addListener("keyboardWillHide", onHide)
				: Keyboard.addListener("keyboardDidHide", onHide);

		return () => {
			subShow.remove();
			subHide.remove();
		};
	}, []);

	// 실제로 줄 paddingBottom = max(0, kbHeight - bottomInset) + extra
	const paddingBottom = useMemo(() => {
		const base = Math.max(0, kbHeight - insets.bottom);
		return base + (extra || 0);
	}, [kbHeight, insets.bottom, extra]);

	return { paddingBottom, keyboardVisible: visible, rawKeyboardHeight: kbHeight };
}
