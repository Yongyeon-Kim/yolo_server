import os
import torch
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# --- Configuration ---
device_env = os.getenv("DEVICE")
DEVICE = device_env if device_env else ("cuda" if torch.cuda.is_available() else "cpu")

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/outputs")

target_classes_env = os.getenv("TARGET_CLASSES", "large vehicle,small vehicle")
TARGET_CLASSES = {cls.strip() for cls in target_classes_env.split(",") if cls.strip()}

MODEL_PATH = os.getenv("MODEL_PATH", "models/yolo11x-obb.pt")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.3"))
