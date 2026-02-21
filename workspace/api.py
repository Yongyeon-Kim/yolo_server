import base64
import io
import json
import os

import cv2
import httpx
import numpy as np
import torch
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image
from pydantic import BaseModel, HttpUrl
from ultralytics import YOLO

# 환경 변수 로드
load_dotenv()

# --- Configuration ---
device_env = os.getenv("DEVICE")
device = device_env if device_env else ("cuda" if torch.cuda.is_available() else "cpu")

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/outputs")

target_classes_env = os.getenv("TARGET_CLASSES", "large vehicle,small vehicle")
TARGET_CLASSES = {cls.strip() for cls in target_classes_env.split(",") if cls.strip()}

MODEL_PATH = os.getenv("MODEL_PATH", "models/yolo11x-obb.pt")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.3"))

# --- FastAPI App Initialization ---
app = FastAPI(
    title="YOLO Vehicle Detection API",
    description="이미지 URL과 요청 ID를 받아 YOLO 모델로 차량을 인식하고, 그 결과를 추적 및 조회할 수 있는 API입니다.",
    version="1.4.0",
)

# --- Model Loading ---
try:
    model = YOLO(MODEL_PATH)
    model.to(device)
    print(f"Using device: {device}")
    print("Model loaded successfully. Class names:")
    print(model.names)
except Exception as e:
    raise RuntimeError(f"Error loading YOLO model: {e}")

# --- Directory Setup ---
os.makedirs(OUTPUT_DIR, exist_ok=True)


# --- Pydantic Models ---
class ImageUrlRequest(BaseModel):
    file_url: HttpUrl
    request_id: str


# --- Helper Functions ---
def save_detection_results(request_id, content):
    """Saves detection results to a JSON file named after the request_id."""
    json_filepath = os.path.join(OUTPUT_DIR, f"{request_id}.json")
    try:
        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Error saving JSON result for request_id {request_id}: {e}")
        return False


# --- API Endpoints ---
@app.post(
    "/detect",
    summary="이미지 파일을 이용한 차량 객체 인식",
    description="""
업로드된 이미지 파일에서 차량(large/small vehicle)을 인식합니다.

**요청 형식 (multipart/form-data):**
- `file`: 분석할 이미지 파일 (예: jpg, png 등)
- `request_id`: 요청을 식별하기 위한 고유 문자열

**응답 Body (JSON):**
- `request_id`: 입력받은 요청 고유 ID
- `detected_objects`: 인식된 객체 리스트
    - `box_coordinates`: 객체의 4개 꼭짓점 좌표 [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    - `class_name`: 인식된 클래스명 (large vehicle 또는 small vehicle)
    - `confidence`: 인식 신뢰도 (0~1)
- `processed_image_b64`: 바운딩 박스가 그려진 결과 이미지의 Base64 인코딩 문자열
- `saved_filename`: 서버에 저장된 이미지 파일명
- `image_url`: 저장된 이미지를 다운로드할 수 있는 경로
- `result_url`: 저장된 분석 결과 JSON을 다운로드할 수 있는 경로
""",
    response_description="인식 결과와 저장된 아티팩트를 조회할 수 있는 URL이 포함된 JSON 응답.",
)
async def detect_objects_from_file(
    file: UploadFile = File(...),
    request_id: str = Form(...)
):
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read uploaded file for request_id {request_id}: {e}",
        )

    try:
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
        cv_image = np.array(pil_image)
        cv_image = cv_image[:, :, ::-1].copy()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read image data for request_id {request_id}.",
        )

    results = model(cv_image, device=device)

    detected_objects = []
    for result in results:
        obbs = result.obb
        if obbs is None:
            continue
        for box in obbs:
            try:
                corners = box.xyxyxyxy[0].cpu().numpy()
                box_points = np.int32(corners).reshape((-1, 1, 2))
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())
                class_name = model.names[class_id]

                if class_name in TARGET_CLASSES and confidence > CONFIDENCE_THRESHOLD:
                    detected_objects.append(
                        {
                            "box_coordinates": box_points.reshape((4, 2)).tolist(),
                            "class_name": class_name,
                            "confidence": round(confidence, 4),
                        }
                    )
                    cv2.polylines(
                        cv_image,
                        [box_points],
                        isClosed=True,
                        color=(0, 255, 0),
                        thickness=5,
                    )
                    label = f"{class_name}: {confidence:.2f}"
                    text_origin = tuple(box_points[0][0])
                    cv2.putText(
                        cv_image,
                        label,
                        (text_origin[0], text_origin[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )
            except Exception as e:
                print(
                    f"Error processing a detection for request_id {request_id}: {e}"
                )
                continue

    output_image_filename = f"{request_id}.jpg"
    output_filepath = os.path.join(OUTPUT_DIR, output_image_filename)

    save_success = cv2.imwrite(output_filepath, cv_image)
    if not save_success:
        print(f"Could not write image to {output_filepath}")
        output_image_filename = None

    is_success, buffer = cv2.imencode(".jpg", cv_image)
    if not is_success:
        raise HTTPException(status_code=500, detail="Failed to encode processed image.")
    image_base64 = base64.b64encode(buffer).decode("utf-8")

    response_content = {
        "request_id": request_id,
        "detected_objects": detected_objects,
        "processed_image_b64": image_base64,
        "saved_filename": output_image_filename,
        "image_url": f"/images/{request_id}" if output_image_filename else None,
        "result_url": f"/results/{request_id}"
        if output_image_filename
        else None,
    }

    if output_image_filename:
        save_detection_results(request_id, response_content)

    return JSONResponse(content=response_content)


@app.get(
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


@app.get(
    "/results/{request_id}",
    summary="요청 ID로 객체 인식 결과 조회",
    description="""
특정 요청 ID에 대해 저장된 분석 결과 JSON 파일을 반환합니다.

**경로 파라미터:**
- `request_id`: 이전에 `/detect` 요청 시 사용했던 고유 ID

**반환값:**
- 분석 결과가 담긴 JSON 파일 (application/json)
- 파일 내용은 `/detect` 엔드포인트의 응답 Body와 동일합니다.
""",
    response_description="요청 ID에 해당하는 객체 인식 결과 JSON 파일.",
)
async def get_results(request_id: str):
    json_path = os.path.join(OUTPUT_DIR, f"{request_id}.json")
    if not os.path.isfile(json_path):
        raise HTTPException(
            status_code=404,
            detail=f"Result JSON for request_id '{request_id}' not found",
        )

    return FileResponse(json_path, media_type="application/json")
