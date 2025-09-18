# src/chat_logic.py
import re
from typing import Optional, Literal

# --- ChatPromptTemplate import (langchain-core 우선, 없으면 langchain로 폴백) ---
try:
    from langchain_core.prompts import ChatPromptTemplate
except Exception:  # pragma: no cover
    from langchain.prompts import ChatPromptTemplate  # type: ignore

from .llm import llm
from .species_meta import SPECIES_META, DEFAULT_SPECIES
from .rules import judge_moisture
from .utils import pick_memes, sanitize
from .config import settings  # noqa: F401  # 향후 플래그/환경값 쓸 때 대비

# =============================
#  키워드 세트 (분리: STRICT / SOFT / LIFE)
#   - STRICT: 식물 맥락에서만 거의 쓰이는 강신호
#   - SOFT  : 일상과 겹치기 쉬운 약신호 (단독으로 plant 유도 X)
#   - LIFE  : 일상/감정/직장/학업 등
# =============================
PLANT_KEYWORDS_STRICT = {
    # 관리/환경/증상(식물 전용 신호)
    "물","급수","흙","토양","분갈이","분무","습도","광","빛","통풍","배수","과습","건조",
    "잎","줄기","뿌리","시들","갈변","처짐",
    # 품종명
    "몬스테라","스투키","산세베리아","금전수","선인장","호접란",
    "테이블야자","홍콩야자","스파티필럼","관음죽",
    "벵갈고무나무","올리브나무","디펜바키아","보스턴고사리",
}
PLANT_KEYWORDS_SOFT = {
    # 애매한 상태 표현(일상과도 겹침 → 단독 사용 금지)
    "아프","괜찮","상태","건강","힘들","죽","살아"
}
LIFE_KEYWORDS = {
    # 일상/감정/직장/학업/교통 등 (확장)
    "배고프","밥","야근","퇴근","피곤","스트레스","회의","상사","회사","출근","퇴사",
    "프로젝트","지각","버스","지하철","시험","월급","연애","날씨","멘붕","짜증","우울",
    "기분","털림","멘탈","힘듦","화남","화가","짜증남","슬픔","분노","걱정","불안","짜증남"
}

# =============================
#  스타일/모드 판별
# =============================
def infer_style(text: str) -> str:
    return "존댓말" if any(s in text for s in ["요", "습니다", "해요", "주세요"]) else "반말"

# ---- 스코어 기반 득표 + 여유마진 + moisture 부스터 ----
W_STRICT = 2.0
W_LIFE   = 1.5
W_SOFT   = 0.5

MARGIN_PLANT = 1.5
MARGIN_DAILY = 1.5
MOISTURE_BOOST = 0.5  # moisture가 있을 때 식물 측 스코어 부스터

def _distinct_hits(text: str, vocab: set[str]) -> int:
    """부분일치로 토큰을 찾되, 같은 토큰 반복은 1회만 카운트."""
    hits = set()
    for tk in vocab:
        if tk in text:
            hits.add(tk)
    return len(hits)

def detect_mode(text: str, moisture: Optional[float]) -> Literal["daily","plant","hybrid"]:
    """
    규칙:
    - STRICT(강신호) >> LIFE,SOFT보다 우선.
    - SOFT는 단독으로 plant 유도 금지. (daily/hybrid의 보조)
    - moisture는 '결정'이 아니라 부스터: STRICT나 SOFT가 있을 때만 약간 가산.
    - plant/daily가 여유마진으로 확실히 이기지 않으면,
      moisture가 있는 경우에는 hybrid로 안전 귀결(=> 하이브리드가 안 되는 상황 방지).
    """
    t = text.strip()

    n_strict = _distinct_hits(t, PLANT_KEYWORDS_STRICT)
    n_soft   = _distinct_hits(t, PLANT_KEYWORDS_SOFT)
    n_life   = _distinct_hits(t, LIFE_KEYWORDS)

    s_strict = n_strict * W_STRICT
    s_life   = n_life   * W_LIFE
    s_soft   = n_soft   * W_SOFT

    if moisture is not None and (n_strict > 0 or n_soft > 0):
        s_strict += MOISTURE_BOOST

    s_plant = s_strict + (s_soft * 0.6)  # SOFT 일부만 plant에 기여
    s_daily = s_life   + (s_soft * 0.4)  # SOFT 일부는 daily에도 기여

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
#  리플렉션(2차 검토) 레이어 (선택 사용)
# =============================
REFLECT_SYSTEM = """You are a 'mode reviewer'.
- Input: user text, first_mode, moisture value.
- Rules:
  1) Confirm PLANT only when there are strict plant signals (watering/repotting/leaves/soil/yellowing/wilting/species names, etc.).
  2) Moisture is auxiliary and must not force PLANT alone.
  3) If daily-life context dominates and plant signals are weak → DAILY.
  4) If daily-life + weak plant nuance + moisture exist together → HYBRID.
  5) When uncertain, choose HYBRID or DAILY conservatively.
- Output: JSON only (Korean reasoning not required):
  {{ "final_mode": "daily|plant|hybrid", "confidence": 0.9, "reasons": "short" }}"""

REFLECT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", REFLECT_SYSTEM),
    ("human",
     "user_text: {user_text}\n"
     "first_mode: {first_mode}\n"
     "moisture: {moisture}\n"
     "Requirement: Return JSON only.")
])

def reflect_mode(user_text: str, first_mode: str, moisture: Optional[float]) -> Literal["daily","plant","hybrid"]:
    """
    detect_mode 결과를 LLM으로 2차 검토.
    - JSON 파싱 실패/이상치면 first_mode 그대로 반환(페일세이프).
    """
    m = "null" if moisture is None else f"{float(moisture):.1f}"
    out = (REFLECT_PROMPT | llm).invoke({
        "user_text": user_text,
        "first_mode": first_mode,
        "moisture": m
    }).content.strip()
    try:
        import json
        data = json.loads(out)
        fm = str(data.get("final_mode","")).strip()
        if fm in ("daily","plant","hybrid"):
            return fm
    except Exception:
        pass
    return first_mode

# =============================
#  1) 공감 오프닝
# =============================
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

def empathy_opening(user_text: str) -> str:
    style = infer_style(user_text)
    res = (EMP_PROMPT | llm).invoke({"user_text": user_text, "style": style}).content.strip()
    res = sanitize(res)
    if len(res) > 45:
        res = res[:45].rstrip() + "…"
    if not re.search(r"[.!?]$", res):
        res += "."
    return res

# =============================
#  한국어 출력 다듬기/1인칭 보정
# =============================
_FIRST_PERSON_FIX = [
    (r"(?:이 )?식물은", "나는"),
    (r"(?:이 )?아이(?:가|는|도)?", "나는"),
    (r"(?:그|이) 친구(?:가|는|도)?", "나는"),
]

def _has_first_person_kor(s: str) -> bool:
    return re.search(r"\b(나|난|나는|내|내가)\b", s) is not None

def _tidy_korean(s: str) -> str:
    # '나는야' → '나는'
    s = re.sub(r"나는야", "나는", s)
    # 문장 시작부의 '나 나는', '나는 나는' 등 중복 제거
    s = re.sub(r"^(?:나\s+)?나는(?:\s+나는)+", "나는", s)
    # '나는 안녕' → '안녕, 나는' (자연스럽게)
    s = re.sub(r"^나는\s+(안녕(?:하세요)?)([,!]?)\s*", r"\1, 나는 ", s)
    # 공백 정리
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s

def _enforce_first_person(text: str, species: str) -> str:
    s = text
    s = re.sub(rf"{re.escape(species)}(?:이|가|는|도)?", "나는", s)
    for pat, rep in _FIRST_PERSON_FIX:
        s = re.sub(pat, rep, s)
    # 첫 단어 강제 '나는 ' 삭제: 인사말과 충돌 방지
    if not _has_first_person_kor(s):
        # 인사말 뒤에 삽입
        m = re.match(r"^(안녕|안녕하세요|헬로|hello)[, ]+", s, flags=re.IGNORECASE)
        if m:
            s = s[:m.end()] + "나는 " + s[m.end():]
        else:
            s = "나는 " + s.lstrip()
    return _tidy_korean(s)

def _strip_extra_tip_leak(text: str, extra_tip: str) -> str:
    if not extra_tip:
        return text
    s = text.replace(extra_tip, "")
    s = s.replace(f"“{extra_tip}”", "").replace(f"\"{extra_tip}\"", "").replace(f"'{extra_tip}'", "")
    return re.sub(r"\s{2,}", " ", s).strip()

# =============================
#  2) 일상 모드
# =============================
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

def build_daily(species: str, user_text: str) -> str:
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

# =============================
#  3) 식물 모드 (1인칭)
# =============================
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

def build_plant(species: str, user_text: str, moisture: float) -> str:
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
    s = _strip_extra_tip_leak(s, meta.get("extra_tip", ""))
    parts = re.split(r'(?<=[.!?])\s+', s)
    s = " ".join(parts[:4])
    if len(s) > 350:
        s = s[:350].rstrip() + "…"
    return _tidy_korean(s)

# =============================
#  4) 하이브리드 모드
# =============================
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

def _enforce_hybrid_pov(text: str, species: str) -> str:
    parts = re.split(r'(?<=[.!?])\s+', sanitize(text))
    if not parts:
        return text
    first = parts[0]
    # 오프닝(사람 관점)에서 1인칭 제거
    first = re.sub(r"\b(나는|난|내가|내 )", "", first).strip()
    tail = " ".join(parts[1:])
    tail = _enforce_first_person(tail, species) if tail else ""
    s = (first + ("" if first.endswith(('.', '!', '?')) else ".") + (" " + tail if tail else "")).strip()
    return _tidy_korean(s)

def build_hybrid(species: str, user_text: str, moisture_guess: float = 40.0) -> str:
    opening = empathy_opening(user_text)
    advice = judge_moisture(moisture_guess)
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

# 내보낼 심볼
__all__ = [
    "infer_style",
    "detect_mode",
    "reflect_mode",  # ← orchestrator에서 선택적으로 사용 가능
    "empathy_opening",
    "build_daily",
    "build_plant",
    "build_hybrid",
]
