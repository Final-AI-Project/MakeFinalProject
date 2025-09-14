# NLG.py
import random

# 패키지/직접실행 모두 지원
try:
    from .disease import DISEASE_INFO as disease_info
except Exception:
    from disease import DISEASE_INFO as disease_info

# 🌿 랜덤 엔딩 멘트 후보
ENDING_MESSAGES = [
    "🍀 조금만 신경 쓰면 우리 식물이 더 건강해질 거예요!",
    "🌱 사랑을 담아 돌봐주면 금세 회복할 수 있을 거예요!",
    "☀️ 환경을 조금만 조정해주면 식물이 훨씬 좋아질 거예요!",
    "💧 물과 빛을 잘 맞춰주면 우리 식물이 다시 힘을 낼 거예요!",
    "🌸 따뜻한 관심만으로도 식물이 더 튼튼해질 수 있어요!",
]

def _first_available(d: dict, keys, default=None):
    """여러 키 후보들 중 존재하는 첫 값을 반환."""
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default

def _to_line(value):
    """리스트/문자열 모두 보기 좋게 한 줄로."""
    if value is None:
        return "-"
    if isinstance(value, (list, tuple)):
        return " / ".join(map(str, value))
    return str(value)

def generate_response(plant_nickname, plant_species, preds):
    """
    preds: [(label:str, prob:float), ...]  # top-k
    """
    lines = []

    # (향후 DB 토큰으로 대체 예정)
    # lines.append(f"🌱 안녕하세요, {plant_nickname}({plant_species})의 상태를 확인했어요!")

    # 1순위
    top1_label, _ = preds[0]
    lines.append(f"🔎 가장 가능성이 높은 증상은 **{top1_label}** 로 의심됩니다.")

    info = disease_info.get(top1_label, {})
    cause       = _first_available(info, ["원인", "이유", "발생원인"])
    management  = _first_available(info, ["관리", "치료", "대처", "방제"])

    if cause:
        lines.append(f"\n 원인: { _to_line(cause) }")
    if management:
        lines.append(f"💡 관리: { _to_line(management) }")

    # 2·3순위 (의심 문구 제거)
    if len(preds) > 1:
        lines.append("\n📌 함께 고려해볼 다른 가능성:")
        for rank, (label, _) in enumerate(preds[1:], start=2):
            lines.append(f"  {rank}순위: {label}")

    # 랜덤 엔딩 멘트
    lines.append("\n" + random.choice(ENDING_MESSAGES))

    return "\n".join(lines)
