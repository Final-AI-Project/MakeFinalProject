# backend/app/ml/plant_llm.py
# 모델 서버(포트 5000)의 LLM API를 호출하는 클라이언트

import httpx
from typing import Optional, Literal
from pydantic import BaseModel
from core.config import settings

# 모델 서버 설정
MODEL_SERVER_URL = settings.MODEL_SERVER_URL

class TalkResult(BaseModel):
    mode: Literal["daily", "plant", "hybrid"]
    species: str
    state: Optional[str] = None
    reply: str

async def plant_talk(species: str, user_text: str, moisture: Optional[float] = None) -> TalkResult:
    """
    모델 서버의 LLM API를 호출하여 식물 대화 처리
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{MODEL_SERVER_URL}/llm",
                json={
                    "species": species,
                    "user_text": user_text,
                    "moisture": moisture
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return TalkResult(
                        mode=data["mode"],
                        species=data["species"],
                        state=data.get("state"),
                        reply=data["reply"]
                    )
                else:
                    # 모델 서버에서 에러가 발생한 경우 더미 답변 반환
                    return _get_dummy_response(species, user_text, moisture)
            else:
                # HTTP 에러가 발생한 경우 더미 답변 반환
                return _get_dummy_response(species, user_text, moisture)
                
    except Exception as e:
        print(f"모델 서버 호출 실패: {e}")
        # 네트워크 에러 등이 발생한 경우 더미 답변 반환
        return _get_dummy_response(species, user_text, moisture)

def _get_dummy_response(species: str, user_text: str, moisture: Optional[float] = None) -> TalkResult:
    """
    모델 서버가 사용 불가능할 때 사용하는 더미 답변
    """
    # 간단한 키워드 기반 모드 판단
    plant_keywords = ["잎", "물", "시들", "갈변", "병", "해충", "성장", "꽃", "뿌리"]
    daily_keywords = ["직장", "회사", "스트레스", "피곤", "기분", "일", "친구", "가족"]
    
    has_plant_keywords = any(keyword in user_text for keyword in plant_keywords)
    has_daily_keywords = any(keyword in user_text for keyword in daily_keywords)
    
    if has_plant_keywords and has_daily_keywords:
        mode = "hybrid"
        reply = "직장 스트레스 힘들겠어. 나도 물이 부족하면 시들거려."
    elif has_plant_keywords:
        mode = "plant"
        reply = "나는 너의 피로를 이해해. 물을 조금 더 주면 좋을 것 같아."
    else:
        mode = "daily"
        reply = "힘들었구나. 그래도 잘 버텨내고 있어!"
    
    return TalkResult(
        mode=mode,
        species=species,
        state="dummy_response",
        reply=reply
    )

# 기존 함수들과의 호환성을 위한 래퍼 함수들
async def get_plant_reply(species: str, user_text: str, moisture: Optional[float] = None) -> str:
    """
    식물 답변만 반환하는 간단한 함수
    """
    result = await plant_talk(species, user_text, moisture)
    return result.reply