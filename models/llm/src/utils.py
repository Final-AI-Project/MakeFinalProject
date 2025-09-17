# src/utils.py
import re
import random
from typing import List, Optional

# ─────────────────────────────────────────────────────────────────────────────
# 밈 카탈로그: 의미/트리거/회피 조건
#  - 퉁퉁퉁… 사후르: 브레인롯(Brainrot) 계열의 무의미/난장/템포업 훅.
#    (인도네시아 새벽식사 'sahur'와 북소리 의성어 'tung' 기원 해석이 있으나,
#     실제 사용은 '의미 없음+뇌절 감성'에 가깝게 소비됨)
#  - 섹시푸드: 비주얼/맛/식감/무드까지 "너무 맛있어 보이는" 음식에 감탄할 때.
#  - 허거덩거덩스: 놀람/양이 많음/혜택 큼/과장된 빅데일 같은 상황을 유쾌하게 강조.
#  - 퀸 네버 크라이: ‘침착해/기품 있게 버티자’는 자기다짐식 유행어(웹툰 ‘기자매’ 발).
#
# 참고 출처(개요):
#  - 퉁퉁퉁 사후르: 이탈리안/브레인롯 밈 설명 및 유통 맥락, 인니 ‘sahur’ 연관 해석. 
#  - 섹시푸드: Z세대 관용어로 ‘비주얼까지 완벽한 음식’ 의미. 
#  - 허거덩거덩스: 놀라움/규모 과장에 쓰이는 신조어 사례.
#  - 퀸 네버 크라이: 네이버웹툰 ‘기자매’ 장면에서 유래, ‘침착 모드’ 상징.
# ─────────────────────────────────────────────────────────────────────────────

MEME_SEEDS = [
    "킹받네","현타 온다","치킨각","갓생","텐션 올려","존버 각",
    "과몰입 금지","힐링타임","에너지충전 각","드립 실패",
    "퉁퉁퉁퉁퉁퉁퉁 사후르","섹시푸드","허거덩거덩스","퀸 네버 크라이"
]

BANNED = ["병신","ㅄ","ㅂㅅ","씨발","ㅆㅂ","좆","지랄","멍청","루저"]

# 상황별 트리거 키워드(정규식 일부 포함 가능)
FOOD_WORDS = r"(먹|맛|배고프|밥|야식|점심|저녁|간식|치킨|피자|라면|카페|디저트|떡볶이|맛집|비주얼|사진|음식)"
CRY_WORDS  = r"(울|눈물|펑펑|멘탈|버티|괜찮|힘들|위로|다독|침착|진정)"
WOW_WORDS  = r"(헉|헐|대박|충격|와우|미쳤|엄청|어마어마|쏟아|폭발|신상|행사|혜택|할인|몰아|왕창)"
BRAINROT_WORDS = r"(멘붕|현타|뇌절|멍|지루|집중안|아무말|정신없|혼돈|카혼란|카오스)"

# 민감/엄숙 토픽: 밈 전면 회피
SERIOUS_WORDS = r"(장례|상중|사망|부고|병원|중환자|수술|우울증|공황|상처|폭력|학대)"


class MemeRule:
    def __init__(self,
                 name: str,
                 meaning: str,
                 triggers: List[str],
                 avoid_patterns: List[str],
                 modes_allow: Optional[List[str]] = None,
                 base: float = 0.0):
        self.name = name
        self.meaning = meaning
        self.triggers = [re.compile(p, re.I) for p in triggers]
        self.avoid = [re.compile(p, re.I) for p in avoid_patterns]
        self.modes_allow = set(modes_allow) if modes_allow else None
        self.base = base

    def score(self, text: str, mode: Optional[str]) -> float:
        # 모드 제한
        if self.modes_allow and (mode not in self.modes_allow):
            return -1e9
        # 회피 조건
        for pat in self.avoid:
            if pat.search(text):
                return -1e9
        # 트리거 득점
        s = self.base
        for pat in self.triggers:
            if pat.search(text):
                s += 1.0
        return s


MEME_CATALOG = [
    MemeRule(
        name="퉁퉁퉁퉁퉁퉁퉁 사후르",
        meaning="의미 없이 텐션 올리는 브레인롯 훅(난장/멍/지루함 깨기).",
        triggers=[BRAINROT_WORDS, r"(반복|중독|퉁|둥둥|북소리)"],
        avoid_patterns=[SERIOUS_WORDS, r"(사과|정중|사실관계|고충접수)"],
        modes_allow=["daily","hybrid"],
        base=0.2,
    ),
    MemeRule(
        name="섹시푸드",
        meaning="비주얼/맛/식감/무드가 압도적인 음식에 감탄할 때.",
        triggers=[FOOD_WORDS, r"(비주얼|탐난다|먹음직|군침)"],
        avoid_patterns=[SERIOUS_WORDS],
        modes_allow=["daily","hybrid"],  # 순수 plant 문맥에선 어색하므로 제한
        base=0.3,
    ),
    MemeRule(
        name="허거덩거덩스",
        meaning="놀라움/규모·양이 많음/혜택 큼을 과장해 유쾌하게 표현.",
        triggers=[WOW_WORDS, r"(넘친|한가득|산더미|빽빽|우수수|쇄도)"],
        avoid_patterns=[SERIOUS_WORDS],
        modes_allow=["daily","hybrid","plant"],
        base=0.1,
    ),
    MemeRule(
        name="퀸 네버 크라이",
        meaning="‘침착/품위 유지’ 다짐. 울컥/멘탈 흔들릴 때 다독임.",
        triggers=[CRY_WORDS, r"(기품|우아|퀸|여왕|품위)"],
        avoid_patterns=[SERIOUS_WORDS, r"(타인비하|가스라이팅)"],
        modes_allow=["daily","hybrid"],
        base=0.5,
    ),
]

# 이름→룰 빠른 접근
MEME_BY_NAME = {m.name: m for m in MEME_CATALOG}


def _serious(text: str) -> bool:
    return re.search(SERIOUS_WORDS, text, flags=re.I) is not None


def pick_memes(k: int = 1, text: Optional[str] = None, mode: Optional[str] = None) -> List[str]:
    """
    컨텍스트 기반 밈 추천.
    - text, mode가 주어지면: MEME_CATALOG 점수화 → 상위 k개.
    - 없으면: 기존처럼 랜덤 샘플.
    - 항상 금칙어는 sanitize가 처리.
    """
    if not text:
        pool = MEME_SEEDS[:]
        random.shuffle(pool)
        return pool[:k]

    # 엄숙/민감 이슈면 밈 비사용(빈 목록) → 호출측에서 선택적으로 무시
    if _serious(text):
        return []

    scored = []
    for m in MEME_CATALOG:
        s = m.score(text, mode)
        scored.append((s, m.name))

    # 점수 0.5 이상만 “맥락 적합”으로 간주
    scored = [x for x in scored if x[0] >= 0.5]
    scored.sort(reverse=True, key=lambda x: x[0])

    if not scored:
        # 맥락 적합 후보 없음 → 가벼운 기본 시드 중 안전한 것만
        safe_fallback = ["힐링타임", "에너지충전 각", "과몰입 금지"]
        random.shuffle(safe_fallback)
        return safe_fallback[:k]

    names = [name for _, name in scored[:k]]

    # k가 더 큰 경우는 무작위로 보충
    if len(names) < k:
        rest = [n for n in MEME_SEEDS if n not in names]
        random.shuffle(rest)
        names += rest[: k - len(names)]

    return names


def sanitize(text: str) -> str:
    s = text
    for bad in BANNED:
        s = s.replace(bad, "")
    # 이모지 1개만 남기기
    emojis = re.findall(r"[\u2600-\u27BF\U0001F300-\U0001FAFF]", s)
    if len(emojis) > 1:
        keep, out = 1, []
        for ch in s:
            if re.match(r"[\u2600-\u27BF\U0001F300-\U0001FAFF]", ch):
                if keep:
                    out.append(ch)
                    keep -= 1
            else:
                out.append(ch)
        s = "".join(out)
    # 공백 정리
    return " ".join(s.split())
