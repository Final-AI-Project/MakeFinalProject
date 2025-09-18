# 간단한 이미지 서비스 (더미 구현)
from typing import Optional
from fastapi import UploadFile
from datetime import datetime, timezone

async def save_uploaded_image(upload: UploadFile, folder: str = "diaries") -> str:
    """
    업로드된 이미지를 저장하고 URL을 반환
    일기용 간단한 이미지 저장 함수
    """
    # 더미 구현 - 실제로는 파일을 저장하고 URL을 반환해야 함
    return f"/static/images/{folder}/dummy_image.jpg"