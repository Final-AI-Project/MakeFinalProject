from dataclasses import dataclass
from typing import List, Literal

@dataclass
class StateAdvice:
    state: Literal["물이부족","적정","과습주의"]
    action: str
    checklist: List[str]
    caution: str

def judge_moisture(moisture_pct: float) -> StateAdvice:
    if moisture_pct < 25:
        return StateAdvice(
            "물이부족",
            "지금은 소량(150~200ml)으로 흙이 고르게 젖도록 급수해줘.",
            ["잎 끝 갈변·주름 확인","급수 후 물받침 물 제거"],
            "화분/토양에 따라 급수량은 달라질 수 있어."
        )
    if moisture_pct > 60:
        return StateAdvice(
            "과습주의",
            "당분간 물주기는 미루고 통풍을 충분히 해줘.",
            ["흙 냄새·곰팡이 확인","물받침 고임 제거"],
            "과습이 반복되면 배수 개선이나 화분 교체가 필요할 수 있어."
        )
    return StateAdvice(
        "적정",
        "지금은 물 필요 없어. 표토 2cm 마르면 소량 급수해줘.",
        ["빛/통풍 유지","잎 상태 관찰"],
        "증상이 지속되면 물주기 간격을 1~2일 조정해봐."
    )
