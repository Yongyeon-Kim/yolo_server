# YOLO OBB 차량 탐지 API

이 프로젝트는 YOLOv11 OBB(Oriented Bounding Box) 모델을 사용하는 FastAPI 기반 객체 탐지 API 게이트웨이입니다. 이미지 파일을 직접 업로드받아 백그라운드에서 차량('large vehicle', 'small vehicle')을 탐지하고, 결과 이미지를 저장하도록 설계되었습니다. 처리된 결과물은 서버에서 자동 생성한 `request_id` (UUID)를 사용하여 나중에 조회할 수 있습니다.

## 주요 기능

- **회전된 바운딩 박스(OBB) 탐지**: YOLOv11 OBB 모델을 활용하여 회전된 객체를 정확하게 탐지합니다.
- **파일 업로드 기반 처리**: 사용자가 직접 이미지 파일을 업로드하여 분석을 의뢰할 수 있습니다.
- **비동기 백그라운드 작업**: 무거운 인공지능 추론 작업을 백그라운드 태스크로 처리하여, 클라이언트는 대기 없이 즉시 응답을 받습니다.
- **환경 변수 기반 설정**: 모델 경로, 탐지 대상, 신뢰도 임계값 등을 `.env` 파일을 통해 유연하게 설정할 수 있습니다.
- **실시간 코드 반영 (Live Reload)**: 개발 모드에서 코드 수정 시 컨테이너 재시작 없이 즉시 반영됩니다.

## 기술 스택

- **백엔드**: Python 3.10, FastAPI
- **객체 탐지**: PyTorch, Ultralytics YOLO
- **이미지 처리**: OpenCV, Pillow
- **컨테이너화**: Docker, Docker Compose
- **패키지 관리**: uv

## 프로젝트 구조

```
yolo_gateway/
├── src/                  # 메인 소스코드 디렉토리
│   ├── main.py           # FastAPI 앱 진입점
│   ├── api/
│   │   └── routes.py     # API 엔드포인트 정의
│   ├── core/
│   │   └── config.py     # 설정 및 환경 변수 로드
│   └── services/
│       └── yolo.py       # YOLO 모델 추론 및 이미지 처리
├── models/               # YOLO 모델 파일 저장소
├── .env                  # 환경 설정 파일
├── docker-compose.yml    # Docker Compose 설정
├── Dockerfile            # Docker 빌드 파일
└── requirements.txt      # 파이썬 의존성 목록
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

2. **환경 변수 설정:**
   `.env` 파일을 생성하고 필요한 값을 설정합니다. (기본값이 설정되어 있습니다.)

3. **컨테이너 실행:**
   Docker Compose를 사용하여 서비스를 시작합니다. API는 **8891**번 포트에서 실행됩니다.

   ```bash
   docker-compose up -d
   ```

4. **서비스 확인:**
   웹 브라우저에서 `http://localhost:8891/docs` 주소로 접속하면 Swagger UI를 통해 API를 테스트할 수 있습니다.

## API 사용법

- **`POST /detect`**: 이미지 파일을 업로드하여 분석 작업을 백그라운드에서 시작합니다. (UUID 반환)
- **`GET /images/{request_id}`**: 생성된 UUID를 통해 바운딩 박스가 그려진 결과 이미지를 조회합니다.

자세한 내용은 [docs/API.md](docs/API.md) 명세서를 참고하세요.
