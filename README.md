# YOLO OBB 차량 탐지 API

이 프로젝트는 YOLOv11 OBB(Oriented Bounding Box) 모델을 사용하는 FastAPI 기반 객체 탐지 API 게이트웨이입니다. 이미지 URL과 고유 `request_id`를 입력받아 이미지를 처리하여 차량('large vehicle', 'small vehicle')을 탐지하고, 결과 이미지와 탐지 데이터를 저장하도록 설계되었습니다. 저장된 결과는 나중에 `request_id`를 사용하여 조회할 수 있습니다.

## 주요 기능

- **회전된 바운딩 박스(OBB) 탐지**: YOLOv11 OBB 모델을 활용하여 회전된 객체를 정확하게 탐지합니다.
- **URL 기반 이미지 처리**: Presigned URL과 같은 이미지 주소를 받아 이미지를 다운로드하고 처리하므로 S3와 같은 서비스와 쉽게 연동할 수 있습니다.
- **요청 ID 추적**: 모든 처리 결과물(이미지, JSON 결과)은 클라이언트가 제공하는 `request_id`를 사용하여 추적되므로 나중에 쉽게 조회할 수 있습니다.

## 기술 스택

- **백엔드**: Python 3.10, FastAPI
- **객체 탐지**: PyTorch, Ultralytics YOLO
- **이미지 처리**: OpenCV
- **HTTP 클라이언트**: HTTPX
- **컨테이너화**: Docker, Docker Compose
- **패키지 설치**: uv

## 프로젝트 구조

```
yolo_gateway/
├── .git/
├── models/
│   └── yolo11x-obb.pt      # YOLO OBB 모델 파일
├── workspace/
│   ├── api.py              # 메인 FastAPI 애플리케이션
│   └── outputs/            # 이미지 및 결과 저장 디렉토리
├── .gitignore
├── docker-compose.yml      # Docker Compose 설정 파일
├── Dockerfile              # Docker 빌드 스크립트
├── requirements.txt        # 파이썬 의존성 목록
└── README.md               # 본 파일
```

## 설치 및 실행 방법

### 사전 요구사항

- Docker
- Docker Compose

### 서비스 실행하기

1. **리포지토리 클론:**

   ```bash
   git clone <your-repository-url>
   cd yolo_gateway
   ```
2. **컨테이너 빌드 및 실행:**
   Docker Compose를 사용 이미지를 빌드하고 서비스를 시작합니다. API는 8000번 포트에서 실행됩니다.

   ```bash
   docker-compose up --build -d
   ```
3. **서비스 확인:**
   웹 브라우저에서 `http://localhost:8000/docs` 주소로 접속하면 API 자동 문서(Swagger UI)를 확인할 수 있습니다.

## API 사용법

API는 이미지 처리를 요청하고 그 결과를 조회하는 엔드포인트를 제공합니다. 자세한 내용은 [API.md](API.md) 명세서를 참고하세요.

- `POST /detect`: 이미지 URL과 `request_id`를 전송하여 처리를 요청합니다.
- `GET /images/{request_id}`: 처리된 결과 이미지를 조회합니다.
- `GET /results/{request_id}`: 탐지 결과를 JSON 형식으로 조회합니다.
