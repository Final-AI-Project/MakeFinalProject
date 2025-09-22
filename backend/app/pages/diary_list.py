from fastapi import APIRouter, HTTPException, Query, Depends, Form, File, UploadFile
from typing import Optional, List, Dict, Any
import os
import uuid
from schemas.diary import (
    DiaryListResponse,
    DiarySearchRequest,
    DiaryStatsResponse,
    DiaryListItemResponse,
    DiaryWriteRequest,
    DiaryWriteResponse
)
from repositories.diary_list import (
    get_user_diary_list,
    search_user_diaries,
    get_diary_stats,
    get_plant_diary_summary,
    get_recent_diaries
)
from repositories.diary import create as create_diary, get_by_diary_id, patch as update_diary, delete_by_diary_id
from db.pool import get_db_connection
from services.auth_service import get_current_user
from clients.plant_llm import get_plant_reply

async def get_latest_humidity_for_plant(conn, plant_id: int) -> Optional[int]:
    """특정 식물의 가장 최근 습도 정보를 가져옵니다."""
    try:
        async with conn.cursor() as cursor:
            # device_info를 통해 plant_id로 device_id를 찾고, 
            # humid_info에서 가장 최근 습도 정보를 가져옵니다
            await cursor.execute("""
                SELECT hi.humidity 
                FROM device_info di 
                JOIN humid_info hi ON di.device_id = hi.device_id 
                WHERE di.plant_id = %s 
                ORDER BY hi.humid_date DESC 
                LIMIT 1
            """, (plant_id,))
            
            result = await cursor.fetchone()
            if result:
                print(f"[DEBUG] 식물 {plant_id}의 최근 습도: {result[0]}%")
                return result[0]
            else:
                print(f"[DEBUG] 식물 {plant_id}의 습도 정보 없음")
                return None
    except Exception as e:
        print(f"[DEBUG] 습도 정보 조회 실패: {e}")
        return None

router = APIRouter(prefix="/diary-list", tags=["diary-list"])

@router.get("", response_model=DiaryListResponse)
async def get_diary_list(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    order_by: str = Query("created_at", description="정렬 기준 (created_at, updated_at, plant_nickname, plant_species, user_title)"),
    order_direction: str = Query("desc", description="정렬 방향 (asc, desc)"),
    plant_nickname: Optional[str] = Query(None, description="식물 별명으로 필터링"),
    plant_species: Optional[str] = Query(None, description="식물 종류로 필터링"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    hashtag: Optional[str] = Query(None, description="해시태그로 필터링"),
    user: dict = Depends(get_current_user)
):
    """
    사용자의 일기 목록을 조회합니다.
    
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **order_by**: 정렬 기준 (created_at, updated_at, plant_nickname, plant_species, user_title)
    - **order_direction**: 정렬 방향 (asc, desc)
    - **plant_nickname**: 식물 별명으로 필터링
    - **plant_species**: 식물 종류로 필터링
    - **start_date**: 시작 날짜 (YYYY-MM-DD 형식)
    - **end_date**: 종료 날짜 (YYYY-MM-DD 형식)
    - **hashtag**: 해시태그로 필터링
    """
    print(f"[DEBUG] get_diary_list API 호출됨 - user: {user}")
    try:
        # 날짜 파싱
        start_date_parsed = None
        end_date_parsed = None
        
        if start_date:
            try:
                from datetime import datetime
                start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="시작 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용해주세요."
                )
        
        if end_date:
            try:
                from datetime import datetime
                end_date_parsed = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="종료 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용해주세요."
                )
        
        # 검색 요청 구성
        search_request = DiarySearchRequest(
            plant_nickname=plant_nickname,
            plant_species=plant_species,
            start_date=start_date_parsed,
            end_date=end_date_parsed,
            hashtag=hashtag
        )
        
        result = await get_user_diary_list(
            user_id=user["user_id"],
            page=page,
            limit=limit,
            order_by=order_by,
            order_direction=order_direction,
            search_request=search_request
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] get_diary_list API 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"일기 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/search", response_model=DiaryListResponse)
async def search_diaries(
    q: str = Query(..., min_length=1, description="검색어"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    user: dict = Depends(get_current_user)
):
    """
    일기 내용을 검색합니다.
    
    - **q**: 검색어 (필수) - 제목과 내용에서 검색
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    """
    try:
        result = await search_user_diaries(
            user_id=user["user_id"],
            query=q,
            page=page,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 검색 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/stats", response_model=DiaryStatsResponse)
async def get_diary_statistics(
    user: dict = Depends(get_current_user)
):
    """
    사용자의 일기 통계 정보를 조회합니다.
    
    - 전체 일기 수
    - 전체 식물 수
    - 최근 7일 일기 수
    - 가장 활발한 식물
    - 식물당 평균 일기 수
    """
    try:
        result = await get_diary_stats(user["user_id"])
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/plants/summary")
async def get_plant_diary_summary_endpoint(
    user: dict = Depends(get_current_user)
):
    """
    식물별 일기 요약을 조회합니다.
    
    - 각 식물별 일기 수
    - 마지막 일기 작성일
    - 첫 일기 작성일
    """
    try:
        result = await get_plant_diary_summary(user["user_id"])
        return {
            "user_id": user["user_id"],
            "plant_summaries": result,
            "total_plants": len(result)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물별 일기 요약 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/recent", response_model=List[DiaryListItemResponse])
async def get_recent_diaries_endpoint(
    limit: int = Query(5, ge=1, le=20, description="조회할 일기 수"),
    user: dict = Depends(get_current_user)
):
    """
    사용자의 최근 일기를 조회합니다.
    
    - **limit**: 조회할 일기 수 (기본값: 5, 최대: 20)
    """
    try:
        result = await get_recent_diaries(user["user_id"], limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"최근 일기 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/export")
async def export_diaries(
    format: str = Query("json", description="내보내기 형식 (json, csv)"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    user: dict = Depends(get_current_user)
):
    """
    일기를 내보냅니다.
    
    - **format**: 내보내기 형식 (json, csv)
    - **start_date**: 시작 날짜 (선택사항)
    - **end_date**: 종료 날짜 (선택사항)
    """
    try:
        # 날짜 파싱
        start_date_parsed = None
        end_date_parsed = None
        
        if start_date:
            try:
                from datetime import datetime
                start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="시작 날짜 형식이 올바르지 않습니다."
                )
        
        if end_date:
            try:
                from datetime import datetime
                end_date_parsed = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="종료 날짜 형식이 올바르지 않습니다."
                )
        
        # 검색 요청 구성
        search_request = DiarySearchRequest(
            start_date=start_date_parsed,
            end_date=end_date_parsed
        )
        
        # 모든 일기 조회 (페이지네이션 없이)
        result = await get_user_diary_list(
            user_id=user["user_id"],
            page=1,
            limit=10000,  # 큰 수로 설정하여 모든 일기 조회
            search_request=search_request
        )
        
        if format.lower() == "csv":
            # CSV 형식으로 변환
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 헤더 작성
            writer.writerow([
                "제목", "내용", "식물별명", "식물종류", "날씨", "해시태그", 
                "작성일", "수정일"
            ])
            
            # 데이터 작성
            for diary in result.diaries:
                writer.writerow([
                    diary.user_title,
                    diary.user_content,
                    diary.plant_nickname or "",
                    diary.plant_species or "",
                    diary.weather or "",
                    diary.hashtag or "",
                    diary.created_at.strftime("%Y-%m-%d %H:%M:%S") if diary.created_at else "",
                    diary.updated_at.strftime("%Y-%m-%d %H:%M:%S") if diary.updated_at else ""
                ])
            
            return {
                "format": "csv",
                "data": output.getvalue(),
                "filename": f"diaries_{user['user_id']}_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        else:
            # JSON 형식
            return {
                "format": "json",
                "data": [diary.dict() for diary in result.diaries],
                "total_count": result.total_count,
                "exported_at": datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 내보내기 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/create", response_model=DiaryWriteResponse)
async def create_diary_entry(
    user_title: str = Form(...),
    user_content: str = Form(...),
    plant_id: Optional[str] = Form(None),
    plant_nickname: Optional[str] = Form(None),
    plant_species: Optional[str] = Form(None),
    hashtag: Optional[str] = Form(None),
    weather: Optional[str] = Form(None),
    hist_watered: Optional[str] = Form("0"),
    hist_repot: Optional[str] = Form("0"),
    hist_pruning: Optional[str] = Form("0"),
    hist_fertilize: Optional[str] = Form("0"),
    image: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
):
    """
    새 일기를 작성합니다.
    """
    try:
        print(f"[DEBUG] 일기 작성 요청 받음 - 사용자: {user.get('user_id', 'unknown')}")
        print(f"[DEBUG] user_title: {user_title}")
        print(f"[DEBUG] user_content: {user_content[:100]}...")
        print(f"[DEBUG] plant_id: {plant_id}")
        print(f"[DEBUG] 이미지 파일: {image.filename if image else 'None'}")
        
        # 이미지 저장
        image_url = None
        if image and image.filename:
            try:
                # 이미지 저장 디렉토리 생성
                upload_dir = "static/diaries"
                os.makedirs(upload_dir, exist_ok=True)
                
                # 고유한 파일명 생성
                file_extension = os.path.splitext(image.filename)[1] or ".jpg"
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                file_path = os.path.join(upload_dir, unique_filename)
                
                # 이미지 파일 저장
                with open(file_path, "wb") as buffer:
                    content = await image.read()
                    buffer.write(content)
                
                image_url = f"/static/diaries/{unique_filename}"
                print(f"[DEBUG] 이미지 저장 성공: {image_url}")
            except Exception as e:
                print(f"[DEBUG] 이미지 저장 실패: {e}")
                # 이미지 저장 실패해도 일기는 계속 진행
        
        async with get_db_connection() as (conn, cursor):
            print("[DEBUG] 데이터베이스 연결 성공")
            
            # AI 모델 호출하여 식물 답변 생성
            print("[DEBUG] AI 모델 호출하여 식물 답변 생성 중...")
            
            # 습도 정보 가져오기 (plant_id가 있는 경우에만)
            moisture = None
            if plant_id:
                moisture = await get_latest_humidity_for_plant(conn, int(plant_id))
                if moisture is not None:
                    print(f"[DEBUG] 습도 정보 전달: {moisture}%")
                else:
                    print("[DEBUG] 습도 정보 없음 - 습도 관련 정보 생략")
            
            try:
                plant_reply = await get_plant_reply(
                    species=plant_species or "식물",
                    user_text=user_content,
                    moisture=moisture  # DB에서 가져온 습도 정보 또는 None
                )
                print(f"[DEBUG] AI 답변 생성 성공: {plant_reply[:50]}...")
            except Exception as e:
                print(f"[DEBUG] AI 답변 생성 실패: {e}")
                plant_reply = "안녕! 오늘도 잘 지내고 있어? 나는 너의 일기를 들을 수 있어서 기뻐!"  # 기본 답변
            
            diary = await create_diary(
                conn,
                user_id=user["user_id"],
                user_title=user_title,
                user_content=user_content,
                hashtag=hashtag,
                plant_id=int(plant_id) if plant_id else None,
                plant_content=plant_reply,
                weather=weather,
                hist_watered=int(hist_watered) if hist_watered else 0,
                hist_repot=int(hist_repot) if hist_repot else 0,
                hist_pruning=int(hist_pruning) if hist_pruning else 0,
                hist_fertilize=int(hist_fertilize) if hist_fertilize else 0
            )
            
            print(f"[DEBUG] 일기 생성 성공: {diary}")
            
            # 이미지가 있으면 img_address 테이블에 저장
            if image_url and diary.diary_id:
                try:
                    await cursor.execute(
                        "INSERT INTO img_address (diary_id, img_url) VALUES (%s, %s)",
                        (diary.diary_id, image_url)
                    )
                    print(f"[DEBUG] 이미지 URL 저장 성공: {image_url}")
                except Exception as e:
                    print(f"[DEBUG] 이미지 URL 저장 실패: {e}")
            
            return DiaryWriteResponse(
                success=True,
                message="일기가 성공적으로 작성되었습니다.",
                diary=DiaryListItemResponse(
                    idx=diary.diary_id,
                    user_title=diary.user_title,
                    user_content=diary.user_content,
                    plant_id=diary.plant_id,
                    plant_nickname=plant_nickname,
                    plant_species=plant_species,
                    plant_reply=plant_reply,
                    weather=weather,
                    weather_icon=None,
                    img_url=image_url,
                    hashtag=hashtag,
                    created_at=diary.created_at,
                    updated_at=None,
                    hist_watered=int(hist_watered) if hist_watered else 0,
                    hist_repot=int(hist_repot) if hist_repot else 0,
                    hist_pruning=int(hist_pruning) if hist_pruning else 0,
                    hist_fertilize=int(hist_fertilize) if hist_fertilize else 0
                )
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 작성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{diary_id}", response_model=DiaryListItemResponse)
async def get_diary_detail(
    diary_id: int,
    user: dict = Depends(get_current_user)
):
    """
    특정 일기의 상세 정보를 조회합니다.
    """
    try:
        print(f"[DEBUG] 일기 조회 요청 - diary_id: {diary_id}, user: {user.get('user_id', 'unknown')}")
        
        async with get_db_connection() as (conn, cursor):
            diary = await get_by_diary_id(conn, diary_id)
            
            if not diary:
                raise HTTPException(
                    status_code=404,
                    detail="일기를 찾을 수 없습니다."
                )
            
            # 사용자 권한 확인
            if diary.user_id != user["user_id"]:
                raise HTTPException(
                    status_code=403,
                    detail="이 일기에 접근할 권한이 없습니다."
                )
            
            print(f"[DEBUG] 일기 조회 성공: {diary}")
            
            return DiaryListItemResponse(
                idx=diary.diary_id,
                user_title=diary.user_title,
                user_content=diary.user_content,
                plant_id=diary.plant_id,
                plant_nickname=getattr(diary, 'plant_nickname', None),
                plant_species=getattr(diary, 'plant_species', None),
                plant_reply=diary.plant_content,
                weather=diary.weather,
                weather_icon=getattr(diary, 'weather_icon', None),
                img_url=diary.img_url,
                hashtag=diary.hashtag,
                created_at=diary.created_at,
                updated_at=getattr(diary, 'updated_at', None),
                hist_watered=diary.hist_watered,
                hist_repot=diary.hist_repot,
                hist_pruning=diary.hist_pruning,
                hist_fertilize=diary.hist_fertilize
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] 일기 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"일기 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.put("/{diary_id}", response_model=DiaryWriteResponse)
async def update_diary_entry(
    diary_id: int,
    user_title: str = Form(...),
    user_content: str = Form(...),
    plant_id: Optional[str] = Form(None),
    plant_nickname: Optional[str] = Form(None),
    plant_species: Optional[str] = Form(None),
    hashtag: Optional[str] = Form(None),
    weather: Optional[str] = Form(None),
    hist_watered: Optional[str] = Form("0"),
    hist_repot: Optional[str] = Form("0"),
    hist_pruning: Optional[str] = Form("0"),
    hist_fertilize: Optional[str] = Form("0"),
    image: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
):
    """
    기존 일기를 수정합니다.
    """
    try:
        print(f"[DEBUG] 일기 수정 요청 - diary_id: {diary_id}, user: {user.get('user_id', 'unknown')}")
        print(f"[DEBUG] user_title: {user_title}")
        print(f"[DEBUG] user_content: {user_content[:100]}...")
        print(f"[DEBUG] plant_id: {plant_id}")
        print(f"[DEBUG] 이미지 파일: {image.filename if image else 'None'}")
        
        # 이미지 저장
        image_url = None
        if image and image.filename:
            try:
                # 이미지 저장 디렉토리 생성
                upload_dir = "static/diaries"
                os.makedirs(upload_dir, exist_ok=True)
                
                # 고유한 파일명 생성
                file_extension = os.path.splitext(image.filename)[1] or ".jpg"
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                file_path = os.path.join(upload_dir, unique_filename)
                
                # 이미지 파일 저장
                with open(file_path, "wb") as buffer:
                    content = await image.read()
                    buffer.write(content)
                
                image_url = f"/static/diaries/{unique_filename}"
                print(f"[DEBUG] 이미지 저장 성공: {image_url}")
            except Exception as e:
                print(f"[DEBUG] 이미지 저장 실패: {e}")
                # 이미지 저장 실패해도 일기는 계속 진행
        
        async with get_db_connection() as (conn, cursor):
            # 기존 일기 조회 및 권한 확인
            existing_diary = await get_by_diary_id(conn, diary_id)
            if not existing_diary:
                raise HTTPException(
                    status_code=404,
                    detail="일기를 찾을 수 없습니다."
                )
            
            if existing_diary.user_id != user["user_id"]:
                raise HTTPException(
                    status_code=403,
                    detail="이 일기를 수정할 권한이 없습니다."
                )
            
            # AI 모델 호출하여 새로운 식물 답변 생성
            print("[DEBUG] AI 모델 호출하여 새로운 식물 답변 생성 중...")
            
            # 습도 정보 가져오기 (plant_id가 있는 경우에만)
            moisture = None
            if plant_id:
                moisture = await get_latest_humidity_for_plant(conn, int(plant_id))
                if moisture is not None:
                    print(f"[DEBUG] 습도 정보 전달: {moisture}%")
                else:
                    print("[DEBUG] 습도 정보 없음 - 습도 관련 정보 생략")
            
            try:
                plant_reply = await get_plant_reply(
                    species=plant_species or "식물",
                    user_text=user_content,
                    moisture=moisture
                )
                print(f"[DEBUG] AI 답변 생성 성공: {plant_reply[:50]}...")
            except Exception as e:
                print(f"[DEBUG] AI 답변 생성 실패: {e}")
                plant_reply = "안녕! 수정된 일기를 잘 읽었어. 나는 너의 변화를 느낄 수 있어서 기뻐!"  # 기본 답변
            
            # 일기 수정
            updated_diary = await update_diary(
                conn,
                diary_id,
                user_title=user_title,
                user_content=user_content,
                hashtag=hashtag,
                plant_id=int(plant_id) if plant_id else None,
                plant_content=plant_reply,
                weather=weather,
                hist_watered=int(hist_watered) if hist_watered else 0,
                hist_repot=int(hist_repot) if hist_repot else 0,
                hist_pruning=int(hist_pruning) if hist_pruning else 0,
                hist_fertilize=int(hist_fertilize) if hist_fertilize else 0
            )
            
            print(f"[DEBUG] 일기 수정 성공: {updated_diary}")
            
            # 이미지가 있으면 img_address 테이블에 저장 (기존 이미지 삭제 후 새로 저장)
            if image_url:
                try:
                    # 기존 이미지 삭제
                    await cursor.execute(
                        "DELETE FROM img_address WHERE diary_id = %s",
                        (diary_id,)
                    )
                    # 새 이미지 저장
                    await cursor.execute(
                        "INSERT INTO img_address (diary_id, img_url) VALUES (%s, %s)",
                        (diary_id, image_url)
                    )
                    print(f"[DEBUG] 이미지 URL 업데이트 성공: {image_url}")
                except Exception as e:
                    print(f"[DEBUG] 이미지 URL 업데이트 실패: {e}")
            
            return DiaryWriteResponse(
                success=True,
                message="일기가 성공적으로 수정되었습니다.",
                diary=DiaryListItemResponse(
                    idx=updated_diary.diary_id,
                    user_title=updated_diary.user_title,
                    user_content=updated_diary.user_content,
                    plant_id=updated_diary.plant_id,
                    plant_nickname=plant_nickname,
                    plant_species=plant_species,
                    plant_reply=plant_reply,
                    weather=weather,
                    weather_icon=None,
                    img_url=image_url or getattr(updated_diary, 'img_url', None),
                    hashtag=hashtag,
                    created_at=updated_diary.created_at,
                    updated_at=None,
                    hist_watered=int(hist_watered) if hist_watered else 0,
                    hist_repot=int(hist_repot) if hist_repot else 0,
                    hist_pruning=int(hist_pruning) if hist_pruning else 0,
                    hist_fertilize=int(hist_fertilize) if hist_fertilize else 0
                )
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] 일기 수정 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"일기 수정 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/{diary_id}")
async def delete_diary_entry(
    diary_id: int,
    user: dict = Depends(get_current_user)
):
    """
    일기를 삭제합니다.
    """
    try:
        print(f"[DEBUG] 일기 삭제 요청 - diary_id: {diary_id}, user: {user.get('user_id', 'unknown')}")
        
        async with get_db_connection() as (conn, cursor):
            # 기존 일기 조회 및 권한 확인
            existing_diary = await get_by_diary_id(conn, diary_id)
            if not existing_diary:
                raise HTTPException(
                    status_code=404,
                    detail="일기를 찾을 수 없습니다."
                )
            
            if existing_diary.user_id != user["user_id"]:
                raise HTTPException(
                    status_code=403,
                    detail="이 일기를 삭제할 권한이 없습니다."
                )
            
            # 일기 삭제
            deleted_count = await delete_by_diary_id(conn, diary_id)
            
            if deleted_count == 0:
                raise HTTPException(
                    status_code=404,
                    detail="일기를 찾을 수 없습니다."
                )
            
            print(f"[DEBUG] 일기 삭제 성공 - diary_id: {diary_id}")
            
            return {
                "success": True,
                "message": "일기가 성공적으로 삭제되었습니다.",
                "deleted_id": diary_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] 일기 삭제 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"일기 삭제 중 오류가 발생했습니다: {str(e)}"
        )
