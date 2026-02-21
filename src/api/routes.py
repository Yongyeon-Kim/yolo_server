import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from src.services.yolo import process_image_sync
from src.core.config import OUTPUT_DIR

router = APIRouter()

@router.post(
    "/detect",
    summary="이미지 파일을 이용한 차량 객체 인식 (비동기)",
    description="""
업로드된 이미지 파일에서 차량(large/small vehicle)을 인식하는 작업을 백그라운드에서 시작합니다.

**요청 형식 (multipart/form-data):**
- `file`: 분석할 이미지 파일 (예: jpg, png 등)

**응답 Body (JSON):**
- `request_id`: 서버에서 자동 생성한 요청 고유 ID (UUID)
- `filename`: 결과 이미지가 저장될 파일명
- `message`: 작업 상태 메시지
""",
    response_description="작업이 시작되었음을 알리는 응답.",
)
async def detect_objects_from_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    request_id = str(uuid.uuid4())
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read uploaded file for request_id {request_id}: {e}",
        )

    # 백그라운드 태스크로 무거운 작업(YOLO 추론 및 이미지 생성) 예약
    background_tasks.add_task(process_image_sync, contents, request_id)

    return JSONResponse(
        content={
            "request_id": request_id,
            "filename": file.filename,
            "message": "차량 인식 작업이 백그라운드에서 시작되었습니다. 잠시 후 /images/ 엔드포인트를 통해 결과를 확인하세요."
        },
        status_code=202
    )

@router.get(
    "/images/{request_id}",
    summary="요청 ID로 처리된 이미지 조회",
    description="""
특정 요청 ID에 대해 처리된 이미지 파일을 반환합니다.

**경로 파라미터:**
- `request_id`: 이전에 `/detect` 요청 시 사용했던 고유 ID

**반환값:**
- 바운딩 박스가 그려진 결과 이미지 파일 (image/jpeg)
""",
    response_description="요청 ID에 해당하는 결과 이미지 파일.",
)
async def get_image(request_id: str):
    image_path = os.path.join(OUTPUT_DIR, f"{request_id}.jpg")
    if not os.path.isfile(image_path):
        raise HTTPException(
            status_code=404, detail=f"Image for request_id '{request_id}' not found"
        )
    return FileResponse(image_path)
