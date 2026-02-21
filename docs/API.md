# API 명세서

## 엔드포인트

### 1. URL을 이용한 객체 탐지

객체 탐지를 위해 이미지 URL과 고유 `request_id`를 제출합니다. 서버는 이미지를 다운로드하고, 탐지를 수행한 후, 결과 이미지와 JSON 데이터를 저장합니다.

- **URL**: `/detect`
- **메서드**: `POST`
- **설명**: URL의 이미지를 기반으로 탐지를 실행합니다.

#### 요청 본문 (Request Body)

- **Content-Type**: `application/json`


| 필드명       | 타입   | 필수 여부 | 설명                                                     |
| :----------- | :----- | :-------- | :------------------------------------------------------- |
| `request_id` | string | 예        | 이 요청에 대한 고유 식별자입니다.                        |
| `file_url`   | string | 예        | 원본 이미지의 유효한 URL 주소입니다 (예: Presigned URL). |

**요청 예시:**

```json
{
  "request_id": "client-request-abc-123",
  "file_url": "https://ultralytics.com/images/bus.jpg"
}
```

#### 성공 응답 (200 OK)

- **Content-Type**: `application/json`

탐지 결과와 저장된 결과물을 조회할 수 있는 URL이 포함된 JSON 객체를 반환합니다.


| 필드명                | 타입   | 설명                                                                                         |
| :-------------------- | :----- | :------------------------------------------------------------------------------------------- |
| `request_id`          | string | 요청 시 전달된 고유 식별자입니다.                                                            |
| `detected_objects`    | array  | 탐지된 객체 목록입니다. 각 객체는`box_coordinates`, `class_name`, `confidence`를 포함합니다. |
| `processed_image_b64` | string | 처리된 이미지(바운딩 박스 포함)를 Base64로 인코딩한 문자열입니다.                            |
| `saved_filename`      | string | 저장된 이미지의 파일 이름입니다 (예:`{request_id}.jpg`).                                     |
| `image_url`           | string | 처리된 이미지를 조회할 수 있는 상대 경로 URL입니다.                                          |
| `result_url`          | string | 탐지 결과를 JSON 파일로 조회할 수 있는 상대 경로 URL입니다.                                  |

**응답 예시:**

```json
{
    "request_id": "client-request-abc-123",
    "detected_objects": [
        {
            "box_coordinates": [
                [145, 220],
                [140, 235],
                [160, 240],
                [165, 225]
            ],
            "class_name": "small vehicle",
            "confidence": 0.8521
        }
    ],
    "processed_image_b64": "iVBORw0KGgoAAAANSUhEUg...",
    "saved_filename": "client-request-abc-123.jpg",
    "image_url": "/images/client-request-abc-123",
    "result_url": "/results/client-request-abc-123"
}
```

#### 오류 응답

- `400 Bad Request`: `file_url`이 유효하지 않거나, 이미지를 다운로드할 수 없거나, 이미지 데이터가 손상된 경우.
- `422 Unprocessable Entity`: 요청 본문에 필수 필드가 누락되었거나 데이터 타입이 잘못된 경우.

---

### 2. 처리된 이미지 조회

`request_id`에 해당하는 처리된 이미지 파일(바운딩 박스가 그려진)을 조회합니다.

- **URL**: `/images/{request_id}`
- **메서드**: `GET`
- **설명**: `request_id`를 사용하여 처리된 이미지를 조회합니다.

#### 경로 파라미터 (Path Parameters)


| 파라미터     | 타입   | 필수 여부 | 설명                           |
| :----------- | :----- | :-------- | :----------------------------- |
| `request_id` | string | 예        | 요청에 대한 고유 식별자입니다. |

#### 성공 응답 (200 OK)

- **Content-Type**: `image/jpeg`

이미지 원본 데이터를 반환합니다.

#### 오류 응답

- `404 Not Found`: 주어진 `request_id`에 해당하는 이미지가 존재하지 않는 경우.

---

### 3. 탐지 결과 조회

주어진 `request_id`에 대해 저장된 탐지 결과(JSON 파일)를 조회합니다.

- **URL**: `/results/{request_id}`
- **메서드**: `GET`
- **설명**: `request_id`를 사용하여 탐지 결과를 조회합니다.

#### 경로 파라미터 (Path Parameters)


| 파라미터     | 타입   | 필수 여부 | 설명                           |
| :----------- | :----- | :-------- | :----------------------------- |
| `request_id` | string | 예        | 요청에 대한 고유 식별자입니다. |

#### 성공 응답 (200 OK)

- **Content-Type**: `application/json`

최초 `/detect` 호출 시 생성되었던 전체 JSON 응답 내용을 반환합니다.

#### 오류 응답

- `404 Not Found`: 주어진 `request_id`에 해당하는 결과 파일이 존재하지 않는 경우.
