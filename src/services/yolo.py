import base64
import io
import os
import cv2
import numpy as np
from PIL import Image
from fastapi import HTTPException
from ultralytics import YOLO
from src.core.config import DEVICE, OUTPUT_DIR, TARGET_CLASSES, MODEL_PATH, CONFIDENCE_THRESHOLD

try:
    model = YOLO(MODEL_PATH)
    model.to(DEVICE)
    print(f"Using device: {DEVICE}")
    print("Model loaded successfully. Class names:")
    print(model.names)
except Exception as e:
    raise RuntimeError(f"Error loading YOLO model: {e}")

# --- Directory Setup ---
os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_image_sync(contents: bytes, request_id: str):
    try:
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
        cv_image = np.array(pil_image)
        cv_image = cv_image[:, :, ::-1].copy()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read image data for request_id {request_id}.",
        )

    results = model(cv_image, device=DEVICE)

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
    }

    return response_content
