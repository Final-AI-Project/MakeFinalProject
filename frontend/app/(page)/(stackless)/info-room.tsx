// frontend/app/(page)/(stackless)/info-room.tsx
import React, { useMemo, useRef, useState } from "react";
import {
    ScrollView,
    View,
    Text,
    StyleSheet,
    useColorScheme,
    Image,
    Pressable,
    LayoutAnimation,
    Platform,
    UIManager,
    Animated,
} from "react-native";
import { useRouter } from "expo-router";
import Colors from "../../../constants/Colors";
import arrowDownW from "../../../assets/images/w_arrow_down.png";
import arrowDownD from "../../../assets/images/d_arrow_down.png";

// Android 레이아웃 애니메이션 활성화
if (Platform.OS === "android" && UIManager.setLayoutAnimationEnabledExperimental) {
    UIManager.setLayoutAnimationEnabledExperimental(true);
}

type Item = { name: string; img: string };

export default function InfoRoom() {
    const scheme = useColorScheme();
    const theme = Colors[scheme === "dark" ? "dark" : "light"];
    const router = useRouter();

    const [openItem, setOpenItem] = useState<string | null>(null);

    // 데이터
    const species: Item[] = useMemo(
        () => [
            { name: "몬스테라", img: "https://picsum.photos/seed/plant1/80/80" },
            { name: "스투키", img: "https://picsum.photos/seed/plant2/80/80" },
            { name: "금전수", img: "https://picsum.photos/seed/plant3/80/80" },
            { name: "선인장/다육", img: "https://picsum.photos/seed/plant4/80/80" },
            { name: "호접란", img: "https://picsum.photos/seed/plant5/80/80" },
            { name: "테이블야자", img: "https://picsum.photos/seed/plant6/80/80" },
            { name: "홍콩야자", img: "https://picsum.photos/seed/plant7/80/80" },
            { name: "스파티필럼", img: "https://picsum.photos/seed/plant8/80/80" },
            { name: "관음죽", img: "https://picsum.photos/seed/plant9/80/80" },
            { name: "벵갈고무나무", img: "https://picsum.photos/seed/plant10/80/80" },
            { name: "올리브나무", img: "https://picsum.photos/seed/plant11/80/80" },
            { name: "디펜바키아", img: "https://picsum.photos/seed/plant12/80/80" },
            { name: "보스턴고사리", img: "https://picsum.photos/seed/plant13/80/80" },
        ],
        []
    );
    const pests: Item[] = useMemo(
        () => [{ name: "추후 추가 예정", img: "https://picsum.photos/seed/pest1/80/80" }],
        []
    );

    // 각 아이템별 회전 애니메이션 값을 메모리에 저장 (필요 시 생성)
    const rotateMap = useRef<Map<string, Animated.Value>>(new Map()).current;
    const getRotate = (key: string) => {
        if (!rotateMap.has(key)) rotateMap.set(key, new Animated.Value(0)); // 0: 닫힘, 1: 열림
        return rotateMap.get(key)!;
    };

    const animateArrow = (key: string, to: 0 | 1) => {
        const v = getRotate(key);
        Animated.timing(v, { toValue: to, duration: 220, useNativeDriver: true }).start();
    };

    const toggleItem = (name: string) => {
        LayoutAnimation.easeInEaseOut();
        const willOpen = openItem !== name;
        setOpenItem(willOpen ? name : null);
        // 현재 눌린 아이템은 목표 상태로 애니메이션
        animateArrow(name, willOpen ? 1 : 0);
        // 이전에 열려있던 아이템의 화살표는 닫힘(0)으로 되돌림
        if (openItem && openItem !== name) animateArrow(openItem, 0);
    };

    const Arrow = ({ itemName }: { itemName: string }) => {
        const v = getRotate(itemName);
        const arrowRotate = v.interpolate({ inputRange: [0, 1], outputRange: ["0deg", "180deg"] });
        return (
            <Animated.View style={{ transform: [{ rotate: arrowRotate }] }}>
                <Image
                    source={scheme === "dark" ? arrowDownD : arrowDownW}
                    style={styles.arrowImg}
                    resizeMode="contain"
                />
            </Animated.View>
        );
    };

    const renderCard = (item: Item) => {
        const isOpen = openItem === item.name;
        return (
            <View key={item.name}>
                <Pressable
                    onPress={() => toggleItem(item.name)}
                    style={[
                        styles.card,
                        { borderColor: theme.border, backgroundColor: theme.card },
                        isOpen && {
                            borderColor: theme.primary,
                            backgroundColor: scheme === "dark" ? (theme.primary + "22") : (theme.primary + "18"),
                        },
                    ]}
                >
                    <Image source={{ uri: item.img }} style={[styles.image, isOpen && styles.imageActive]} />
                    <View style={styles.cardTextArea}>
                        <Text style={[styles.item, { color: theme.text }, isOpen && styles.itemActive]}>
                            {item.name}
                        </Text>
                    </View>
                    {/* 회전 화살표 */}
                    <Arrow itemName={item.name} />
                </Pressable>

                {isOpen && (
                    <View style={[styles.detailBox, { borderColor: theme.border }]}>
                        <Text style={[styles.detailText, { color: theme.text }]}>
                            {item.name}에 대한 상세 설명은 추후 추가될 예정입니다.
                        </Text>
                    </View>
                )}
            </View>
        );
    };

    return (
        <ScrollView style={[styles.container, { backgroundColor: theme.bg }]}>
            {/* 품종 관련 정보 */}
            <Text style={[styles.title, { color: theme.text }]}>품종 관련 정보</Text>
            {species.map(renderCard)}

            {/* 병충해 관련 정보 */}
            <Text style={[styles.title, { color: theme.text, marginTop: 24 }]}>병충해 관련 정보</Text>
            {pests.map(renderCard)}

            {/* 뒤로가기 버튼 */}
            <Pressable
                style={[styles.backButton, { borderColor: theme.border, backgroundColor: theme.card }]}
                onPress={() => router.back()}
            >
                <Text style={[styles.backText, { color: theme.text }]}>뒤로가기</Text>
            </Pressable>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, paddingTop: 10, paddingHorizontal: 20 },
    title: { fontSize: 18, fontWeight: "800", marginBottom: 12 },

    card: {
        flexDirection: "row",
        alignItems: "center",
        borderWidth: 1,
        borderRadius: 20,
        paddingVertical: 12,
        paddingHorizontal: 12,
        marginBottom: 10,
    },
    image: { width: 60, height: 60, borderRadius: 12, marginRight: 12, opacity: 0.95 },
    imageActive: { opacity: 1 },

    cardTextArea: { flex: 1 },
    item: { fontSize: 15, fontWeight: "600" },
    itemActive: { fontWeight: "800" },

    arrowImg: { width: 20, height: 20, marginLeft: 6, opacity: 0.9 },

    detailBox: {
        borderWidth: 1,
        borderRadius: 16,
        padding: 16,
        marginBottom: 10,
    },
    detailText: { fontSize: 14, lineHeight: 20 },

    backButton: {
        marginTop: 30,
        paddingVertical: 14,
        marginBottom: 40,
        borderWidth: 1,
        borderRadius: 8,
        alignItems: "center",
        justifyContent: "center",
    },
    backText: { fontSize: 16, fontWeight: "700" },
});
