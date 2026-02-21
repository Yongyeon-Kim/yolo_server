from fastapi import FastAPI
from src.api.routes import router

app = FastAPI(
    title="YOLO Vehicle Detection API",
    description="이미지 업로드를 통해 차량을 인식하고, 그 결과를 백그라운드에서 처리하여 조회할 수 있는 API입니다.",
    version="1.4.0",
)

app.include_router(router)
