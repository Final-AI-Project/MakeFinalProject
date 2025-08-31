"""
I/O Utilities
파일 입출력 관련 유틸리티
"""

import os
import aiofiles
from fastapi import UploadFile
from typing import List
import logging

logger = logging.getLogger(__name__)


async def save_uploaded_file(file: UploadFile, filename: str, upload_dir: str) -> str:
    """
    업로드된 파일 저장
    
    Args:
        file: 업로드된 파일
        filename: 저장할 파일명
        upload_dir: 업로드 디렉토리
        
    Returns:
        저장된 파일 경로
    """
    try:
        # 업로드 디렉토리 생성
        os.makedirs(upload_dir, exist_ok=True)
        
        # 파일 경로 생성
        file_path = os.path.join(upload_dir, filename)
        
        # 파일 저장
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(f"파일 저장 완료: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"파일 저장 실패: {str(e)}")
        raise


def validate_image_file(file: UploadFile, allowed_extensions: List[str]) -> bool:
    """
    이미지 파일 검증
    
    Args:
        file: 업로드된 파일
        allowed_extensions: 허용된 확장자 목록
        
    Returns:
        검증 결과
    """
    try:
        # 파일명에서 확장자 추출
        filename = file.filename
        if not filename:
            return False
        
        # 확장자 추출 (소문자로 변환)
        extension = filename.split('.')[-1].lower()
        
        # 허용된 확장자인지 확인
        if extension not in allowed_extensions:
            return False
        
        # MIME 타입 확인 (선택적)
        if file.content_type:
            valid_mime_types = [
                'image/jpeg',
                'image/jpg',
                'image/png',
                'image/webp'
            ]
            if file.content_type not in valid_mime_types:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"파일 검증 실패: {str(e)}")
        return False


def get_file_size_mb(file_path: str) -> float:
    """
    파일 크기 반환 (MB)
    
    Args:
        file_path: 파일 경로
        
    Returns:
        파일 크기 (MB)
    """
    try:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    except Exception as e:
        logger.error(f"파일 크기 확인 실패: {str(e)}")
        return 0.0


def cleanup_old_files(directory: str, max_age_hours: int = 24):
    """
    오래된 파일 정리
    
    Args:
        directory: 정리할 디렉토리
        max_age_hours: 최대 보관 시간 (시간)
    """
    try:
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        if not os.path.exists(directory):
            return
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            # 파일인지 확인
            if not os.path.isfile(file_path):
                continue
            
            # 파일 수정 시간 확인
            file_mtime = os.path.getmtime(file_path)
            if current_time - file_mtime > max_age_seconds:
                try:
                    os.remove(file_path)
                    logger.info(f"오래된 파일 삭제: {file_path}")
                except Exception as e:
                    logger.error(f"파일 삭제 실패: {file_path}, {str(e)}")
                    
    except Exception as e:
        logger.error(f"파일 정리 실패: {str(e)}")


def ensure_directory_exists(directory: str):
    """
    디렉토리 존재 확인 및 생성
    
    Args:
        directory: 확인할 디렉토리 경로
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"디렉토리 생성: {directory}")
    except Exception as e:
        logger.error(f"디렉토리 생성 실패: {directory}, {str(e)}")


def get_safe_filename(filename: str) -> str:
    """
    안전한 파일명 생성
    
    Args:
        filename: 원본 파일명
        
    Returns:
        안전한 파일명
    """
    import re
    import uuid
    
    # 특수문자 제거 및 공백을 언더스코어로 변경
    safe_name = re.sub(r'[^\w\-_.]', '_', filename)
    
    # 파일명이 너무 길면 자르기
    if len(safe_name) > 100:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:90] + ext
    
    # 고유성 보장
    unique_id = str(uuid.uuid4())[:8]
    name, ext = os.path.splitext(safe_name)
    safe_name = f"{name}_{unique_id}{ext}"
    
    return safe_name


def list_files_in_directory(directory: str, extensions: List[str] = None) -> List[str]:
    """
    디렉토리 내 파일 목록 반환
    
    Args:
        directory: 디렉토리 경로
        extensions: 필터링할 확장자 목록
        
    Returns:
        파일 경로 목록
    """
    try:
        if not os.path.exists(directory):
            return []
        
        files = []
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            if not os.path.isfile(file_path):
                continue
            
            if extensions:
                file_ext = filename.split('.')[-1].lower()
                if file_ext not in extensions:
                    continue
            
            files.append(file_path)
        
        return files
        
    except Exception as e:
        logger.error(f"파일 목록 조회 실패: {str(e)}")
        return []
