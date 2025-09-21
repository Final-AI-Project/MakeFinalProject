import os
import uuid
from datetime import datetime
from typing import Optional, Tuple
from pathlib import Path
import shutil

# 이미지 저장 경로 설정
BASE_STATIC_PATH = Path(__file__).parent.parent.parent / "static"
IMAGES_PATH = BASE_STATIC_PATH / "images"

# 이미지 타입별 경로
PLANT_IMAGES_PATH = IMAGES_PATH / "plants"
DIARY_IMAGES_PATH = IMAGES_PATH / "diaries"
USER_IMAGES_PATH = IMAGES_PATH / "users"
MEDICAL_IMAGES_PATH = IMAGES_PATH / "medical"
TEMP_IMAGES_PATH = IMAGES_PATH / "temp"

# 허용된 이미지 확장자
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

# 최대 파일 크기 (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024

def ensure_directories():
    """필요한 디렉토리들을 생성합니다."""
    for path in [PLANT_IMAGES_PATH, DIARY_IMAGES_PATH, USER_IMAGES_PATH, MEDICAL_IMAGES_PATH, TEMP_IMAGES_PATH]:
        path.mkdir(parents=True, exist_ok=True)

def is_allowed_file(filename: str) -> bool:
    """파일 확장자가 허용된 형식인지 확인합니다."""
    if not filename:
        return False
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """고유한 파일명을 생성합니다."""
    if not original_filename:
        return f"{prefix}_{uuid.uuid4().hex}.jpg"
    
    file_ext = Path(original_filename).suffix.lower()
    if not file_ext:
        file_ext = ".jpg"
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    
    if prefix:
        return f"{prefix}_{timestamp}_{unique_id}{file_ext}"
    else:
        return f"{timestamp}_{unique_id}{file_ext}"

def get_image_path(image_type: str, filename: str) -> Path:
    """이미지 타입에 따른 경로를 반환합니다."""
    type_mapping = {
        "plant": PLANT_IMAGES_PATH,
        "plants": PLANT_IMAGES_PATH,  # 복수형도 추가
        "diary": DIARY_IMAGES_PATH,
        "diaries": DIARY_IMAGES_PATH,  # 복수형도 추가
        "user": USER_IMAGES_PATH,
        "users": USER_IMAGES_PATH,  # 복수형도 추가
        "medical": MEDICAL_IMAGES_PATH,  # 의료 진단 이미지
        "temp": TEMP_IMAGES_PATH,
        "disease_diagnosis": MEDICAL_IMAGES_PATH  # 진단 이미지는 medical 폴더에
    }
    
    base_path = type_mapping.get(image_type, TEMP_IMAGES_PATH)
    return base_path / filename

def save_image(file_content: bytes, image_type: str, original_filename: str = None, prefix: str = "") -> Tuple[str, str]:
    """
    이미지를 저장하고 파일명과 URL을 반환합니다.
    
    Args:
        file_content: 파일 내용 (bytes)
        image_type: 이미지 타입 ("plant", "diary", "user", "temp")
        original_filename: 원본 파일명
        prefix: 파일명 접두사
    
    Returns:
        Tuple[str, str]: (저장된 파일명, 접근 가능한 URL)
    """
    ensure_directories()
    
    # 파일 크기 확인
    if len(file_content) > MAX_FILE_SIZE:
        raise ValueError(f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB까지 허용됩니다.")
    
    # 파일명 생성
    filename = generate_unique_filename(original_filename, prefix)
    
    # 파일 경로
    file_path = get_image_path(image_type, filename)
    
    # 파일 저장
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    # URL 생성 (프론트엔드에서 접근할 수 있는 경로)
    url = f"/static/images/{image_type}/{filename}"
    
    return filename, url

def delete_image(image_type: str, filename: str) -> bool:
    """
    이미지 파일을 삭제합니다.
    
    Args:
        image_type: 이미지 타입
        filename: 파일명
    
    Returns:
        bool: 삭제 성공 여부
    """
    try:
        file_path = get_image_path(image_type, filename)
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except Exception as e:
        print(f"이미지 삭제 중 오류 발생: {e}")
        return False

def move_temp_image(temp_filename: str, target_type: str, prefix: str = "") -> Tuple[str, str]:
    """
    임시 이미지를 실제 저장 위치로 이동합니다.
    
    Args:
        temp_filename: 임시 파일명
        target_type: 대상 이미지 타입
        prefix: 새 파일명 접두사
    
    Returns:
        Tuple[str, str]: (새 파일명, 새 URL)
    """
    temp_path = get_image_path("temp", temp_filename)
    
    if not temp_path.exists():
        raise FileNotFoundError(f"임시 파일을 찾을 수 없습니다: {temp_filename}")
    
    # 새 파일명 생성
    new_filename = generate_unique_filename(temp_filename, prefix)
    new_path = get_image_path(target_type, new_filename)
    
    # 파일 이동
    shutil.move(str(temp_path), str(new_path))
    
    # 새 URL 생성
    new_url = f"/static/images/{target_type}/{new_filename}"
    
    return new_filename, new_url

def get_image_url(image_type: str, filename: str) -> str:
    """이미지 URL을 생성합니다."""
    return f"/static/images/{image_type}/{filename}"

def list_images(image_type: str, limit: int = 50) -> list:
    """특정 타입의 이미지 목록을 반환합니다."""
    try:
        path = get_image_path(image_type, "")
        if not path.exists():
            return []
        
        images = []
        for file_path in path.iterdir():
            if file_path.is_file() and is_allowed_file(file_path.name):
                images.append({
                    "filename": file_path.name,
                    "url": get_image_url(image_type, file_path.name),
                    "size": file_path.stat().st_size,
                    "created": datetime.fromtimestamp(file_path.stat().st_ctime)
                })
        
        # 생성일 기준으로 정렬 (최신순)
        images.sort(key=lambda x: x["created"], reverse=True)
        return images[:limit]
    
    except Exception as e:
        print(f"이미지 목록 조회 중 오류 발생: {e}")
        return []

def cleanup_temp_images(max_age_hours: int = 24) -> int:
    """오래된 임시 이미지들을 정리합니다."""
    try:
        temp_path = TEMP_IMAGES_PATH
        if not temp_path.exists():
            return 0
        
        current_time = datetime.now()
        deleted_count = 0
        
        for file_path in temp_path.iterdir():
            if file_path.is_file():
                file_age = current_time - datetime.fromtimestamp(file_path.stat().st_ctime)
                if file_age.total_seconds() > max_age_hours * 3600:
                    file_path.unlink()
                    deleted_count += 1
        
        return deleted_count
    
    except Exception as e:
        print(f"임시 이미지 정리 중 오류 발생: {e}")
        return 0
