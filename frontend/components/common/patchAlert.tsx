// components/common/patchAlert.ts
import { Alert } from "react-native";
import type { AlertButton as RNAlertButton } from "react-native";
import { showAlert } from "./appAlert";

/**
 * React Native의 Alert.alert를 전역으로 패치해서
 * 기존 호출부를 전혀 수정하지 않아도 커스텀 Alert UI가 뜨도록 함.
 *
 * 사용: 루트에서 `import "./components/common/patchAlert"` 한 줄만 추가.
 */
(() => {
    // 이미 패치되어 있으면 중복 패치 방지
    if ((Alert as any).__patched_by_app__) return;

    const originalAlert = Alert.alert.bind(Alert);

    const patched = (
        title: string,
        message?: string,
        buttons?: RNAlertButton[],
        options?: { cancelable?: boolean; onDismiss?: () => void }
    ) => {
        // RN의 다양한 오버로드를 방어적으로 처리
        let _title = title ?? "";
        let _message = message ?? "";

        // buttons 정규화
        const btns = Array.isArray(buttons) ? buttons : [];

        // 커스텀 알럿 호출
        showAlert({
            title: _title,
            message: _message,
            dismissible: !!options?.cancelable,
            buttons:
                btns.length > 0
                    ? btns.map((b) => ({
                          text: b.text ?? "확인",
                          style:
                              b.style === "destructive"
                                  ? "destructive"
                                  : b.style === "cancel"
                                  ? "cancel"
                                  : "default",
                          onPress: b.onPress,
                      }))
                    : [
                          {
                              text: "확인",
                              onPress: options?.onDismiss,
                          },
                      ],
        });
    };

    // 타입 경고 회피용 any 캐스트
    (Alert as any).alert = patched;
    (Alert as any).__patched_by_app__ = true;

    // 필요하면 되돌릴 수 있도록 원본도 보관
    (Alert as any).__original_alert__ = originalAlert;
})();
