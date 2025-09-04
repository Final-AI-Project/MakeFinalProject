# backend/app/models/LMM/NLG.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import random

@dataclass
class PlantSpeechConfig:
    disease_prob_threshold: float = 0.5
    topk_diseases: int = 2
    locale: str = "ko"
    seed: Optional[int] = 2025  # 재현성 유지(랜덤 문구 셔플)
    # 신규: DB에서 넘어오는 식물 별명(없으면 종(common name)으로 대체)
    plant_nick: Optional[str] = None

# 질병 이름 → 간단 설명/권장 조치 (데이터셋 라벨명에 맞춰 확장)
DISEASE_TIPS_KO: Dict[str, Dict[str, List[str]]] = {
    "powdery_mildew": {
        "desc": ["하얀 가루처럼 덮여서 숨쉬기 불편해요", "잎 표면에 흰 곰팡이 느낌이 있어요"],
        "care": ["공기 순환을 좋아해요", "잎에 물 머금은 채로 오래 두지 말아주세요"],
    },
    "leaf_spot": {
        "desc": ["잎에 갈색 반점이 보여요", "작은 점들이 번지는 느낌이에요"],
        "care": ["오염된 잎은 분리/제거해주세요", "관수 시 잎을 과도하게 적시지 말아주세요"],
    },
    "blight": {
        "desc": ["잎이 빠르게 상처받고 있어요", "줄기/잎이 축 늘어져요"],
        "care": ["환기와 건조한 환경을 잠시 유지해주세요", "필요시 전용 방제법을 검토해주세요"],
    },
    "healthy": {
        "desc": ["지금은 아주 편안해요", "컨디션이 좋아요"],
        "care": ["지금처럼만 돌봐주세요", "빛/물/바람 균형을 좋아해요"],
    },
}

# [추후 활성화 예정: 습도 기반 문장]
# HUMIDITY_LINES_KO = {
#     "dry": [
#         "조금 목이 말라요.",
#         "잎끝이 말라 보이면 물이 더 필요할 수 있어요.",
#     ],
#     "ok": [
#         "공기가 적당해서 숨쉬기 편해요.",
#         "지금 환경이 꽤 아늑해요.",
#     ],
#     "wet": [
#         "공기가 눅눅해 조금 답답해요.",
#         "곰팡이나 뿌리 과습을 조심해 주세요.",
#     ],
# }

MOOD_OPENERS_KO = {
    "bright": [
        "안녕하세요 주인님! 저는 {plant_nick}이에요.",
        "반가워요! 저는 {plant_nick}이에요.",
    ],
    "concern": [
        "주인님, 잠깐만요… {plant_nick}가 조심스럽게 말할게요.",
        "혹시 들어주실래요? {plant_nick}가 살짝 걱정이 있어요.",
    ],
    "unwell": [
        "주인님… {plant_nick}가 조금 아파요.",
        "{plant_nick}가 도움이 필요해요.",
    ],
}

CLOSERS_KO = [
    "항상 돌봐주셔서 고마워요.",
    "천천히 성장해 나아가요. 고마워요!",
    "내일도 열심히 자라볼게요.",
    "주인님 내일도 꽃같은 하루되세요.",
    "오늘도 곁에 있어 주셔서 고마워요.",
    "내일도 함께 자라볼게요.",
    "내일도 행복한 하루 되세요.",
    "내일도 푸릇푸릇한 하루 보내세요.",
    "당신의 사랑스러운 시선이 느껴져요. 함께 성장해봐요!",
    "따뜻한 햇살 속에서 더욱 건강하게 자랄게요. 고마워요!",
    "작은 변화지만 큰 기쁨이에요. 함께 이 순간을 축하해요!",
    "오늘도 상쾌한 물방울 목욕 덕분에 다시 활력이 넘쳐요!",
    "당신의 정성어린 돌봄 덕분에 점점 튼튼해지고 있어요.",
    "세심한 관찰력에 감동이에요. 건강한 뿌리로 더 아름답게 자랄게요!",
    "빛을 향해 나아가는 것처럼, 우리 관계도 더 밝아지길 바라요.",
    "점점 더 아름다워지는 건 모두 당신 덕분이에요. 자신감이 생겨요!",
    "당신의 자랑이 될 수 있어서 영광이에요. 더 멋지게 자랄게요!",
    "당신 곁에서 빛나는 존재가 되어 기뻐요. 오늘도 아름다운 하루였어요.",
    "당신과 함께한 모든 순간이 제게는 보물이에요. 앞으로도 함께 걸어가요!"
]

def classify_humidity(humidity_pct: float) -> str:
    """Return 'dry' | 'ok' | 'wet'"""
    if humidity_pct < 35:
        return "dry"
    if humidity_pct > 60:
        return "wet"
    return "ok"

def pick_top_diseases(disease_probs: Dict[str, float], thr: float, k: int) -> List[Tuple[str, float]]:
    # 모델이 이미 top2만 전달해도 dict 그대로 상한 정렬·필터링
    cand = [(k_, v) for k_, v in disease_probs.items() if v >= thr and k_ != "healthy"]
    cand.sort(key=lambda x: x[1], reverse=True)
    return cand[:k]

# def compute_mood(humidity_band: str, has_disease: bool):  # [미래용] 습도 반영 버전
def compute_mood(has_disease: bool) -> str:
    mood_score = 0
    # [미래용] if humidity_band in ("dry", "wet"): mood_score -= 1
    if has_disease:
        mood_score -= 2
    if mood_score >= -1:
        return "bright"
    if mood_score >= -3:
        return "concern"
    return "unwell"

def render_message_ko(
    species_common: str,
    humidity_pct: float,
    disease_probs: Dict[str, float],
    cfg: PlantSpeechConfig = PlantSpeechConfig(),
) -> str:
    rng = random.Random(cfg.seed)

    # [미래용] 습도 밴드(현재 미사용; 아래 문장 생성도 주석 처리)
    # humidity_band = classify_humidity(humidity_pct)

    top_diseases = pick_top_diseases(disease_probs, cfg.disease_prob_threshold, cfg.topk_diseases)
    has_disease = len(top_diseases) > 0

    # 현재는 질병만으로 무드 결정
    mood = compute_mood(has_disease)

    # 별명 없으면 종(common name)으로 대체
    plant_display = (cfg.plant_nick or species_common).strip()
    opener_tpl = rng.choice(MOOD_OPENERS_KO[mood])
    opener = opener_tpl.format(plant_nick=plant_display, species_name=species_common)

    # [미래용] 습도 문장 (현재 비활성화)
    # humidity_line = rng.choice(HUMIDITY_LINES_KO[humidity_band])

    # 질병 문장/케어
    disease_lines: List[str] = []
    if has_disease:
        for name, prob in top_diseases:
            desc_pool = DISEASE_TIPS_KO.get(name, {}).get(
                "desc", ["조금 컨디션이 좋지 않아요. 가까이서 한 번만 살펴봐 주세요."]
            )
            care_pool = DISEASE_TIPS_KO.get(name, {}).get(
                "care", ["빛·물·바람 균형을 점검해 주세요."]
            )
            if desc_pool:
                disease_lines.append(rng.choice(desc_pool) + f" (신뢰도 {int(prob*100)}%)")
            if care_pool:
                disease_lines.append("케어 팁: " + rng.choice(care_pool))
    else:
        # 건강 라인
        desc_pool = DISEASE_TIPS_KO["healthy"]["desc"]
        care_pool = DISEASE_TIPS_KO["healthy"]["care"]
        disease_lines.append(rng.choice(desc_pool))
        disease_lines.append("케어 팁: " + rng.choice(care_pool))

    closer = rng.choice(CLOSERS_KO)

    # 3~5문장 구성(현재 3~4문장: 오프너 + 질병 1~2줄 + 클로저)
    # [미래용] parts = [opener, humidity_line] + disease_lines[:2] + [closer]
    parts = [opener] + disease_lines[:2] + [closer]

    # 불필요한 공백 제거
    parts = [p.strip() for p in parts if p.strip()]
    return " ".join(parts)

def generate_plant_message(
    species_common: str,
    humidity_pct: float,
    disease_probs: Dict[str, float],
    cfg: Optional[PlantSpeechConfig] = None,
) -> str:
    """Public API.

    다른 모듈에서:
    - species_common: 품종/일반명 (예: "몬스테라")
    - disease_probs: top2 결과만 담긴 dict도 허용 (예: {"leaf_spot":0.81,"blight":0.55})
    - cfg.plant_nick: DB의 별명을 설정하면 오프너에 사용됨
    - humidity_pct: 현재는 미사용(주석 처리), 향후 활성화 예정
    """
    cfg = cfg or PlantSpeechConfig()
    if cfg.locale != "ko":
        # 확장 여지: en 등 다국어 템플릿 분기
        cfg.locale = "ko"
    return render_message_ko(species_common, humidity_pct, disease_probs, cfg)


''' 사용 예시 (나중에 백엔드에서 사용 예정)
from backend.app.models.LMM.NLG import generate_plant_message, PlantSpeechConfig

cfg = PlantSpeechConfig(
    plant_nick="초록이",       # DB 별명
    disease_prob_threshold=0.5 # top2 dict만 넘어오는 경우에도 안전
)

msg = generate_plant_message(
    species_common="몬스테라",
    humidity_pct=48.0,  # 현재 미사용(향후 활성화)
    disease_probs={"leaf_spot": 0.82, "blight": 0.57}  # 모델 top2
)
print(msg)
'''