from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
import os
from ...utils.image_storage import (
    save_image, 
    delete_image, 
    move_temp_image, 
    get_image_url,
    list_images,
    is_allowed_file,
    cleanup_temp_images
)

router = APIRouter(prefix="/plant-detail", tags=["plant-detail-images"])

@router.post("/{plant_idx}/upload-image")
async def upload_plant_image(
    plant_idx: int,
    user_id: str,
    file: UploadFile = File(...),
    image_type: str = Form("plant"),  # "plant", "diary", "temp"
    prefix: str = Form("")
):
    """
    식물 관련 이미지를 업로드합니다.
    """
    try:
        # 파일 유효성 검사
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail="지원하지 않는 파일 형식입니다. JPG, PNG, GIF, BMP, WEBP만 허용됩니다."
            )
        
        # 파일 내용 읽기
        file_content = await file.read()
        
        # 이미지 저장
        filename, url = save_image(
            file_content=file_content,
            image_type=image_type,
            original_filename=file.filename,
            prefix=f"{prefix}_{plant_idx}_{user_id}" if prefix else f"{plant_idx}_{user_id}"
        )
        
        return {
            "success": True,
            "message": "이미지가 성공적으로 업로드되었습니다.",
            "filename": filename,
            "url": url,
            "image_type": image_type,
            "plant_idx": plant_idx,
            "user_id": user_id,
            "file_size": len(file_content)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이미지 업로드 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/{plant_idx}/upload-diary-image")
async def upload_diary_image(
    plant_idx: int,
    user_id: str,
    file: UploadFile = File(...),
    diary_id: Optional[int] = Form(None)
):
    """
    일기 이미지를 업로드합니다.
    """
    try:
        # 파일 유효성 검사
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail="지원하지 않는 파일 형식입니다."
            )
        
        # 파일 내용 읽기
        file_content = await file.read()
        
        # 일기 이미지로 저장
        prefix = f"diary_{diary_id}" if diary_id else f"diary_{plant_idx}_{user_id}"
        filename, url = save_image(
            file_content=file_content,
            image_type="diary",
            original_filename=file.filename,
            prefix=prefix
        )
        
        return {
            "success": True,
            "message": "일기 이미지가 성공적으로 업로드되었습니다.",
            "filename": filename,
            "url": url,
            "diary_id": diary_id,
            "plant_idx": plant_idx,
            "user_id": user_id
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 이미지 업로드 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/{plant_idx}/upload-temp-image")
async def upload_temp_image(
    plant_idx: int,
    user_id: str,
    file: UploadFile = File(...)
):
    """
    임시 이미지를 업로드합니다. (나중에 실제 위치로 이동)
    """
    try:
        # 파일 유효성 검사
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail="지원하지 않는 파일 형식입니다."
            )
        
        # 파일 내용 읽기
        file_content = await file.read()
        
        # 임시 이미지로 저장
        filename, url = save_image(
            file_content=file_content,
            image_type="temp",
            original_filename=file.filename,
            prefix=f"temp_{plant_idx}_{user_id}"
        )
        
        return {
            "success": True,
            "message": "임시 이미지가 성공적으로 업로드되었습니다.",
            "filename": filename,
            "url": url,
            "plant_idx": plant_idx,
            "user_id": user_id
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"임시 이미지 업로드 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/{plant_idx}/move-temp-image")
async def move_temp_to_permanent(
    plant_idx: int,
    user_id: str,
    temp_filename: str = Form(...),
    target_type: str = Form("plant"),  # "plant", "diary"
    prefix: str = Form("")
):
    """
    임시 이미지를 실제 저장 위치로 이동합니다.
    """
    try:
        # 임시 이미지를 실제 위치로 이동
        new_filename, new_url = move_temp_image(
            temp_filename=temp_filename,
            target_type=target_type,
            prefix=f"{prefix}_{plant_idx}_{user_id}" if prefix else f"{plant_idx}_{user_id}"
        )
        
        return {
            "success": True,
            "message": "이미지가 성공적으로 이동되었습니다.",
            "old_filename": temp_filename,
            "new_filename": new_filename,
            "new_url": new_url,
            "target_type": target_type,
            "plant_idx": plant_idx,
            "user_id": user_id
        }
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이미지 이동 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/{plant_idx}/delete-image")
async def delete_plant_image(
    plant_idx: int,
    user_id: str,
    filename: str,
    image_type: str = "plant"
):
    """
    식물 이미지를 삭제합니다.
    """
    try:
        success = delete_image(image_type, filename)
        
        if success:
            return {
                "success": True,
                "message": "이미지가 성공적으로 삭제되었습니다.",
                "filename": filename,
                "image_type": image_type,
                "plant_idx": plant_idx,
                "user_id": user_id
            }
        else:
            raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이미지 삭제 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}/images")
async def get_plant_images(
    plant_idx: int,
    user_id: str,
    image_type: str = "plant",
    limit: int = 20
):
    """
    식물의 이미지 목록을 조회합니다.
    """
    try:
        images = list_images(image_type, limit)
        
        # 사용자별 필터링 (파일명에 user_id가 포함된 것만)
        filtered_images = [
            img for img in images 
            if user_id in img["filename"] or f"_{plant_idx}_" in img["filename"]
        ]
        
        return {
            "success": True,
            "plant_idx": plant_idx,
            "user_id": user_id,
            "image_type": image_type,
            "count": len(filtered_images),
            "images": filtered_images
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이미지 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/cleanup-temp-images")
async def cleanup_temp_images_endpoint(max_age_hours: int = 24):
    """
    오래된 임시 이미지들을 정리합니다.
    """
    try:
        deleted_count = cleanup_temp_images(max_age_hours)
        
        return {
            "success": True,
            "message": f"{deleted_count}개의 임시 이미지가 정리되었습니다.",
            "deleted_count": deleted_count,
            "max_age_hours": max_age_hours
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"임시 이미지 정리 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}/image-info")
async def get_image_info(
    plant_idx: int,
    user_id: str,
    filename: str,
    image_type: str = "plant"
):
    """
    특정 이미지의 정보를 조회합니다.
    """
    try:
        from ...utils.image_storage import get_image_path
        from pathlib import Path
        
        file_path = get_image_path(image_type, filename)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")
        
        stat = file_path.stat()
        url = get_image_url(image_type, filename)
        
        return {
            "success": True,
            "filename": filename,
            "url": url,
            "image_type": image_type,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "plant_idx": plant_idx,
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이미지 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )
