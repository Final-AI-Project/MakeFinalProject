# src/orchestrator.py
from typing import Optional, Literal
from pydantic import BaseModel

# detect_mode + reflect_mode(리플렉션) 모두 사용
from .chat_logic import detect_mode, reflect_mode, build_daily, build_plant, build_hybrid
from .rules import judge_moisture
from .species_meta import DEFAULT_SPECIES
from .utils import sanitize


class TalkResult(BaseModel):
    mode: Literal["daily", "plant", "hybrid"]
    species: str
    state: Optional[str] = None
    reply: str


def plant_talk(species: str, user_text: str, moisture: Optional[float] = None) -> TalkResult:
    """
    대화 오케스트레이션:
    1) 1차 분류(detect_mode)
    2) 리플렉션으로 2차 감수(reflect_mode)
    3) 최종 모드에 맞는 빌더 호출
    """
    species = species or DEFAULT_SPECIES

    # 1차 분류 → 2차 리플렉션(보수적 수정; 파싱 실패 시 원래 모드 유지)
    first_mode = detect_mode(user_text, moisture)
    mode = reflect_mode(user_text, first_mode, moisture)

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
    user_id: str,
    plant_id: int,
    plant_name: str,
    species: str,
    user_content: str,
    user_title: str,  # 사용자가 입력한 제목 (필수)
    moisture: Optional[float] = None,
    hashtag: Optional[str] = None,
    weather: Optional[str] = None,
):
    """
    DB 저장용 필드만 반환하는 헬퍼.
    ERD의 diary 테이블 구조에 맞춰 데이터를 반환합니다.
    """
    result = plant_talk(species, user_content, moisture)
    
    return {
        "user_id": user_id,
        "user_title": user_title,  # 사용자가 입력한 제목 그대로 사용
        "user_content": user_content,
        "hashtag": hashtag or "",
        "plant_content": result.reply,
        "weather": weather or "",
        "mode": result.mode,
        "species": result.species,
        "state": result.state,
        "plant_id": plant_id,
        "plant_name": plant_name,
    }
