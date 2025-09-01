#!/usr/bin/env python3
"""
SQLModel Enum TypeError 재현 예제
"""
import sys
from enum import Enum
from typing import Annotated, Optional, List, Union
from sqlalchemy import Enum as SAEnum, Column

try:
    from sqlmodel import SQLModel, Field
    print("✅ SQLModel import 성공")
except ImportError as e:
    print(f"❌ SQLModel import 실패: {e}")
    sys.exit(1)

# 정상 예제
print("\n=== 정상 예제 ===")
class Status(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: Status = Field(default=Status.ACTIVE)

print("✅ 정상 예제 클래스 정의 성공")

# 오류 유발 패턴들
print("\n=== 오류 유발 패턴 테스트 ===")

# 1) Annotated 래퍼를 해제하지 않은 경우
print("1. Annotated 패턴 테스트...")
try:
    class M1(SQLModel, table=True):
        id: int | None = Field(default=None, primary_key=True)
        status: Annotated[Status, Field(default=Status.ACTIVE)]
    print("✅ M1 클래스 정의 성공")
except Exception as e:
    print(f"❌ M1 오류: {e}")

# 2) Optional/Union 래퍼가 직접 전달되는 경우
print("2. Optional 패턴 테스트...")
try:
    class M2(SQLModel, table=True):
        id: int | None = Field(default=None, primary_key=True)
        status: Optional[Status] = Field(default=None)
    print("✅ M2 클래스 정의 성공")
except Exception as e:
    print(f"❌ M2 오류: {e}")

# 3) List 래퍼
print("3. List 패턴 테스트...")
try:
    class M3(SQLModel, table=True):
        id: int | None = Field(default=None, primary_key=True)
        statuses: List[Status] = Field(default_factory=list)
    print("✅ M3 클래스 정의 성공")
except Exception as e:
    print(f"❌ M3 오류: {e}")

# 4) SQLAlchemy Enum 인스턴스 (정상 사용)
print("4. SQLAlchemy Enum 패턴 테스트...")
try:
    class M4(SQLModel, table=True):
        id: int | None = Field(default=None, primary_key=True)
        status: Status = Field(sa_column=Column(SAEnum(Status)))
    print("✅ M4 클래스 정의 성공")
except Exception as e:
    print(f"❌ M4 오류: {e}")

print("\n=== 테스트 완료 ===")
