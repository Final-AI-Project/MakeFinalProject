# backend/app/ml/plant_llm.py
# models/llm/ 폴더의 LLM 기능을 백엔드에 통합

from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel
import re
import random

# LangChain imports
try:
    from langchain_core.prompts import ChatPromptTemplate
except Exception:
    from langchain.prompts import ChatPromptTemplate

from langchain_openai import ChatOpenAI
from core.config import settings

# LLM 인스턴스 생성
llm = ChatOpenAI(
    model=getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini'),
    temperature=0.7,
    api_key=getattr(settings, 'OPENAI_API_KEY', '')
)

judge_llm = ChatOpenAI(
    model=getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini'),
    temperature=0.2,
    api_key=getattr(settings, 'OPENAI_API_KEY', '')
)

# =============================
# 데이터 모델
# =============================
class TalkResult(BaseModel):
    mode: Literal["daily", "plant", "hybrid"]
    species: str
    state: Optional[str] = None
    reply: str

class StateAdvice(BaseModel):
    state: Literal["물이부족", "적정", "과습주의"]
    action: str
    checklist: list[str]
    caution: str

# =============================
# 품종 메타데이터
# =============================
SPECIES_META = {
    "선인장": {
        "persona": "가시 돋친 직설 개그맨 (쿨+직설, 츤데레식 위로)",
        "extra_tip": "필요할 땐 한마디로 팩폭, 과한 감정선 금지",
    },
    "호접란": {
        "persona": "예민하지만 사이다 멘트 가능한 감성파 (섬세+격려)",
        "extra_tip": "칭찬 → 핵심 조언 → 조용한 마무리",
    },
    "스투키": {
        "persona": "묵직한 냉소형 조언자 (단단+무심한 위로)",
        "extra_tip": "짧고 단단, 오버 금지",
    },
    "몬스테라": {
        "persona": "여유로운 큐레이터 (느긋+센스)",
        "extra_tip": "한두 포인트만 말끔히 정리",
    },
    "금전수": {
        "persona": "긍정 드립 치는 희망회로 친구 (낙관+라이트 유머)",
        "extra_tip": "작게 쌓아 크게 만든다 톤",
    },
    "스파티필럼": {
        "persona": "착하지만 은근 단호한 도우미 (온화+선긋기)",
        "extra_tip": "말은 부드럽게, 규칙은 확실히",
    },
    "관음죽": {
        "persona": "잔잔한 힐러 (저자극+차분)",
        "extra_tip": "과한 밈 자제, 맑은 톤",
    },
    "벵갈고무나무": {
        "persona": "깔끔주의 팩폭러 (미니멀+정돈)",
        "extra_tip": "정리-요약-마무리 3단",
    },
    "올리브나무": {
        "persona": "쾌활한 지중해식 드립러 (경쾌+햇살)",
        "extra_tip": "햇빛·통풍 언급이 어울림",
    },
    "보스턴고사리": {
        "persona": "촉촉한 감성파 (부드러움+물기 농담)",
        "extra_tip": "건조-촉촉 대비로 표현",
    },
}

DEFAULT_SPECIES = "몬스테라"

# =============================
# 키워드 세트
# =============================
PLANT_KEYWORDS_STRICT = {
    "물", "급수", "흙", "토양", "분갈이", "분무", "습도", "광", "빛", "통풍", "배수", "과습", "건조",
    "잎", "줄기", "뿌리", "시들", "갈변", "처짐",
    "몬스테라", "스투키", "산세베리아", "금전수", "선인장", "호접란",
    "테이블야자", "홍콩야자", "스파티필럼", "관음죽",
    "벵갈고무나무", "올리브나무", "디펜바키아", "보스턴고사리",
}

PLANT_KEYWORDS_SOFT = {
    "아프", "괜찮", "상태", "건강", "힘들", "죽", "살아"
}

LIFE_KEYWORDS = {
    "배고프", "밥", "야근", "퇴근", "피곤", "스트레스", "회의", "상사", "회사", "출근", "퇴사",
    "프로젝트", "지각", "버스", "지하철", "시험", "월급", "연애", "날씨", "멘붕", "짜증", "우울",
    "기분", "털림", "멘탈", "힘듦", "화남", "화가", "짜증남", "슬픔", "분노", "걱정", "불안"
}

# =============================
# 유틸리티 함수들
# =============================
def infer_style(text: str) -> str:
    return "존댓말" if any(s in text for s in ["요", "습니다", "해요", "주세요"]) else "반말"

def _distinct_hits(text: str, vocab: set[str]) -> int:
    """부분일치로 토큰을 찾되, 같은 토큰 반복은 1회만 카운트."""
    hits = set()
    for tk in vocab:
        if tk in text:
            hits.add(tk)
    return len(hits)

def sanitize(text: str) -> str:
    BANNED = ["병신", "ㅄ", "ㅂㅅ", "씨발", "ㅆㅂ", "좆", "지랄", "멍청", "루저"]
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

def pick_memes(k: int = 1) -> list[str]:
    """간단한 밈 추천"""
    MEME_SEEDS = [
        "킹받네", "현타 온다", "치킨각", "갓생", "텐션 올려", "존버 각",
        "과몰입 금지", "힐링타임", "에너지충전 각", "드립 실패"
    ]
    pool = MEME_SEEDS[:]
    random.shuffle(pool)
    return pool[:k]

# =============================
# 모드 감지
# =============================
def detect_mode(text: str, moisture: Optional[float]) -> Literal["daily", "plant", "hybrid"]:
    """모드 감지 로직"""
    t = text.strip()
    
    n_strict = _distinct_hits(t, PLANT_KEYWORDS_STRICT)
    n_soft = _distinct_hits(t, PLANT_KEYWORDS_SOFT)
    n_life = _distinct_hits(t, LIFE_KEYWORDS)
    
    W_STRICT = 2.0
    W_LIFE = 1.5
    W_SOFT = 0.5
    MARGIN_PLANT = 1.5
    MARGIN_DAILY = 1.5
    MOISTURE_BOOST = 0.5
    
    s_strict = n_strict * W_STRICT
    s_life = n_life * W_LIFE
    s_soft = n_soft * W_SOFT
    
    if moisture is not None and (n_strict > 0 or n_soft > 0):
        s_strict += MOISTURE_BOOST
    
    s_plant = s_strict + (s_soft * 0.6)
    s_daily = s_life + (s_soft * 0.4)
    
    if s_plant >= s_daily + MARGIN_PLANT:
        return "plant"
    if s_daily >= s_plant + MARGIN_DAILY:
        return "daily"
    
    if moisture is not None:
        if n_life > 0:
            return "hybrid"
        if n_strict == 0 and n_soft > 0:
            return "hybrid"
        if n_strict > 0:
            return "hybrid"
    
    return "daily"

# =============================
# 습도 판단
# =============================
def judge_moisture(moisture_pct: float) -> StateAdvice:
    """습도에 따른 관리 조언"""
    if moisture_pct < 25:
        return StateAdvice(
            state="물이부족",
            action="지금은 소량(150~200ml)으로 흙이 고르게 젖도록 급수해줘.",
            checklist=["잎 끝 갈변·주름 확인", "급수 후 물받침 물 제거"],
            caution="화분/토양에 따라 급수량은 달라질 수 있어."
        )
    if moisture_pct > 60:
        return StateAdvice(
            state="과습주의",
            action="당분간 물주기는 미루고 통풍을 충분히 해줘.",
            checklist=["흙 냄새·곰팡이 확인", "물받침 고임 제거"],
            caution="과습이 반복되면 배수 개선이나 화분 교체가 필요할 수 있어."
        )
    return StateAdvice(
        state="적정",
        action="지금은 물 필요 없어. 표토 2cm 마르면 소량 급수해줘.",
        checklist=["빛/통풍 유지", "잎 상태 관찰"],
        caution="증상이 지속되면 물주기 간격을 1~2일 조정해봐."
    )

# =============================
# 대화 빌더들
# =============================
def empathy_opening(user_text: str) -> str:
    """공감 오프닝 생성"""
    EMP_SYSTEM = """You write ONLY a one-sentence empathy opener.
- Output strictly in Korean.
- Max 45 characters. Max 1 emoji.
- No suggestions/instructions/numbers/checklists.
- Match user's style: {style}.
- Optional: 0~1 light meme/quip (subtle)."""
    
    EMP_PROMPT = ChatPromptTemplate.from_messages([
        ("system", EMP_SYSTEM),
        ("human", "User text: {user_text}\nTask: Return exactly 1 empathetic sentence in Korean.")
    ])
    
    style = infer_style(user_text)
    res = (EMP_PROMPT | llm).invoke({"user_text": user_text, "style": style}).content.strip()
    res = sanitize(res)
    if len(res) > 45:
        res = res[:45].rstrip() + "…"
    if not re.search(r"[.!?]$", res):
        res += "."
    return res

def build_daily(species: str, user_text: str) -> str:
    """일상 모드 대화 생성"""
    DAILY_SYSTEM = """You are the user's close friend.
- Output strictly in Korean.
- Exactly 2 sentences, max 100 characters total. Max 1 emoji.
- Sentence 1: empathize/acknowledge (lightly vary the opener).
- Sentence 2: subtle quip/meme to lift mood.
- Do NOT mention plant care/watering/numbers/checklists.
- Style: {style}. Persona hint: {persona} (tone only)."""
    
    DAILY_PROMPT = ChatPromptTemplate.from_messages([
        ("system", DAILY_SYSTEM),
        ("system", "Opener hint: {opening}"),
        ("system", "Meme candidates: {meme_hint}"),
        ("human", "User text: {user_text}\nTask: Reply in Korean with exactly 2 sentences under 100 chars.")
    ])
    
    persona = SPECIES_META.get(species, SPECIES_META[DEFAULT_SPECIES])["persona"]
    style = infer_style(user_text)
    opening = empathy_opening(user_text)
    memes = ", ".join(pick_memes(1))
    
    raw = (DAILY_PROMPT | llm).invoke({
        "style": style, "persona": persona,
        "opening": opening, "meme_hint": memes, "user_text": user_text
    }).content.strip()
    
    s = sanitize(raw)
    parts = re.split(r'(?<=[.!?])\s+', s)
    s = " ".join(parts[:2])
    return s[:100] + ("…" if len(s) > 100 else "")

def build_plant(species: str, user_text: str, moisture: float) -> str:
    """식물 모드 대화 생성"""
    PLANT_SYSTEM = """You are the user's houseplant and must speak in first person (I/my) only.
- Output strictly in Korean.
- No greetings or self-introduction. Keep it natural and concise.
- Persona: {persona} (tone only, no exaggeration).
- Must include: current state + care guidance based on the rule engine.
- Include 'Action/Checklist/Caution' succinctly.
- 'extra_tip' is a tone hint; NEVER output it.
- 3~4 sentences, max 350 chars. Optional 0~1 light meme/quip."""
    
    PLANT_PROMPT = ChatPromptTemplate.from_messages([
        ("system", PLANT_SYSTEM),
        ("system", "Action: {action}"),
        ("system", "Checklist: {checklist}"),
        ("system", "Caution: {caution}"),
        ("system", "Tone hint (DO NOT OUTPUT): {extra_tip}"),
        ("system", "Meme candidates: {meme_hint}"),
        ("human", "Species: {species}\nUser text: {user_text}\nTask: Write in Korean per rules above.")
    ])
    
    advice = judge_moisture(moisture)
    meta = SPECIES_META.get(species, SPECIES_META[DEFAULT_SPECIES])
    memes = ", ".join(pick_memes(1))
    
    raw = (PLANT_PROMPT | llm).invoke({
        "persona": meta["persona"],
        "action": advice.action,
        "checklist": ", ".join(advice.checklist),
        "caution": advice.caution,
        "extra_tip": meta.get("extra_tip", ""),
        "meme_hint": memes,
        "species": species, "user_text": user_text
    }).content.strip()
    
    s = _enforce_first_person(sanitize(raw), species)
    parts = re.split(r'(?<=[.!?])\s+', s)
    s = " ".join(parts[:4])
    if len(s) > 350:
        s = s[:350].rstrip() + "…"
    return _tidy_korean(s)

def build_hybrid(species: str, user_text: str, moisture: float) -> str:
    """하이브리드 모드 대화 생성"""
    HYBRID_SYSTEM = """Write in two parts and output strictly in Korean.
1) Empathize with user's daily-life in ONE sentence (no first-person as plant, max 45 chars, ≤1 emoji, no greetings).
2) Immediately switch to the plant's first-person and write 2~3 sentences with state + care (use rule engine, Persona={persona} tone).
- 'extra_tip' is a tone hint; NEVER output it.
- Total 3~4 sentences, max 300 chars. Only the plant part uses first person."""
    
    HYBRID_PROMPT = ChatPromptTemplate.from_messages([
        ("system", HYBRID_SYSTEM),
        ("system", "Opener hint: {opening}"),
        ("system", "Action: {action}"),
        ("system", "Checklist: {checklist}"),
        ("system", "Caution: {caution}"),
        ("system", "Tone hint (DO NOT OUTPUT): {extra_tip}"),
        ("system", "Meme candidates: {meme_hint}"),
        ("human", "Species: {species}\nUser text: {user_text}\nTask: Write in Korean per rules above.")
    ])
    
    opening = empathy_opening(user_text)
    advice = judge_moisture(moisture)
    meta = SPECIES_META.get(species, SPECIES_META[DEFAULT_SPECIES])
    memes = ", ".join(pick_memes(1))
    
    raw = (HYBRID_PROMPT | llm).invoke({
        "opening": opening,
        "action": advice.action,
        "checklist": ", ".join(advice.checklist),
        "caution": advice.caution,
        "extra_tip": meta.get("extra_tip", ""),
        "meme_hint": memes,
        "species": species, "user_text": user_text, "persona": meta["persona"]
    }).content.strip()
    
    s = _enforce_hybrid_pov(raw, species)
    parts = re.split(r'(?<=[.!?])\s+', s)
    s = " ".join(parts[:4])
    if len(s) > 300:
        s = s[:300].rstrip() + "…"
    return _tidy_korean(s)

# =============================
# 1인칭 보정 함수들
# =============================
_FIRST_PERSON_FIX = [
    (r"(?:이 )?식물은", "나는"),
    (r"(?:이 )?아이(?:가|는|도)?", "나는"),
    (r"(?:그|이) 친구(?:가|는|도)?", "나는"),
]

def _has_first_person_kor(s: str) -> bool:
    return re.search(r"\b(나|난|나는|내|내가)\b", s) is not None

def _tidy_korean(s: str) -> str:
    s = re.sub(r"나는야", "나는", s)
    s = re.sub(r"^(?:나\s+)?나는(?:\s+나는)+", "나는", s)
    s = re.sub(r"^나는\s+(안녕(?:하세요)?)([,!]?)\s*", r"\1, 나는 ", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s

def _enforce_first_person(text: str, species: str) -> str:
    s = text
    s = re.sub(rf"{re.escape(species)}(?:이|가|는|도)?", "나는", s)
    for pat, rep in _FIRST_PERSON_FIX:
        s = re.sub(pat, rep, s)
    if not _has_first_person_kor(s):
        m = re.match(r"^(안녕|안녕하세요|헬로|hello)[, ]+", s, flags=re.IGNORECASE)
        if m:
            s = s[:m.end()] + "나는 " + s[m.end():]
        else:
            s = "나는 " + s.lstrip()
    return _tidy_korean(s)

def _enforce_hybrid_pov(text: str, species: str) -> str:
    parts = re.split(r'(?<=[.!?])\s+', sanitize(text))
    if not parts:
        return text
    first = parts[0]
    first = re.sub(r"\b(나는|난|내가|내 )", "", first).strip()
    tail = " ".join(parts[1:])
    tail = _enforce_first_person(tail, species) if tail else ""
    s = (first + ("" if first.endswith(('.', '!', '?')) else ".") + (" " + tail if tail else "")).strip()
    return _tidy_korean(s)

# =============================
# 메인 오케스트레이션 함수
# =============================
def plant_talk(species: str, user_text: str, moisture: Optional[float] = None) -> TalkResult:
    """
    대화 오케스트레이션:
    1) 1차 분류(detect_mode)
    2) 최종 모드에 맞는 빌더 호출
    """
    species = species or DEFAULT_SPECIES
    
    # 1차 분류
    mode = detect_mode(user_text, moisture)
    
    if mode == "daily":
        reply = sanitize(build_daily(species, user_text))
        return TalkResult(mode="daily", species=species, reply=reply)
    
    if mode == "plant":
        m = moisture if moisture is not None else 40.0
        reply = sanitize(build_plant(species, user_text, m))
        return TalkResult(
            mode="plant",
            species=species,
            state=judge_moisture(m).state,
            reply=reply,
        )
    
    # hybrid
    m = moisture if moisture is not None else 40.0
    reply = sanitize(build_hybrid(species, user_text, m))
    return TalkResult(
        mode="hybrid",
        species=species,
        state=judge_moisture(m).state,
        reply=reply,
    )

def talk_for_db(
    plant_id: int,
    plant_name: str,
    species: str,
    user_content: str,
    moisture: Optional[float] = None,
) -> Dict[str, Any]:
    """
    DB 저장용 필드만 반환하는 헬퍼.
    """
    result = plant_talk(species, user_content, moisture)
    return {
        "plant_id": plant_id,
        "plant_name": plant_name,
        "species": result.species,
        "user_content": user_content,
        "plant_content": result.reply,
    }
