// Tab size: 4
import { useCallback } from "react";
import { useFocusEffect } from "@react-navigation/native";

/**
 * 화면이 focus될 때마다 callback을 실행한다.
 * 상태를 보존하면서 데이터만 갱신하고 싶을 때 사용.
 */
export default function useRefreshOnFocus(callback: () => void) {
	useFocusEffect(
		useCallback(() => {
			callback();
		}, [callback])
	);
}
