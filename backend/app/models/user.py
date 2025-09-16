from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class User:
    """aiomysql용 User 모델"""
    idx: Optional[int] = None
    user_id: str = ""
    user_pw: str = ""
    email: str = ""
    hp: str = ""
    nickname: str = ""
    regdate: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """딕셔너리에서 User 객체 생성"""
        return cls(
            idx=data.get("idx"),
            user_id=data.get("user_id", ""),
            user_pw=data.get("user_pw", ""),
            email=data.get("email", ""),
            hp=data.get("hp", ""),
            nickname=data.get("nickname", ""),
            regdate=data.get("regdate"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """User 객체를 딕셔너리로 변환"""
        return {
            "idx": self.idx,
            "user_id": self.user_id,
            "user_pw": self.user_pw,
            "email": self.email,
            "hp": self.hp,
            "nickname": self.nickname,
            "regdate": self.regdate,
        }
