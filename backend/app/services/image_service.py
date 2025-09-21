# 이미지 서비스
from typing import Optional
from fastapi import UploadFile
from datetime import datetime, timezone
from utils.image_storage import save_image

async def save_uploaded_image(upload: UploadFile, folder: str = "diaries") -> str:
    """
    업로드된 이미지를 저장하고 URL을 반환
    """
    try:
        # 파일 내용 읽기
        file_content = await upload.read()
        
        # 이미지 저장
        filename, url = save_image(
            file_content=file_content,
            image_type=folder,
            original_filename=upload.filename,
            prefix=f"{folder}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        return url
        
    except Exception as e:
        # 에러 발생 시 더미 URL 반환 (기존 동작 유지)
        print(f"이미지 저장 실패: {e}")
        return f"/static/images/{folder}/dummy_image.jpg"