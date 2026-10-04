"""Install the pinned optional detector; never train or install dependencies."""
import hashlib
from pathlib import Path
import shutil
import sys
import urllib.request

RUNTIME = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RUNTIME))
from app.recognition.text_detector import MODEL_PATH, MODEL_SHA256

URL = "https://huggingface.co/opencv/opencv_zoo/resolve/d4938dfc9d4ec5d098bfa33e98b3f3345a236586/models/text_detection_ppocr/text_detection_cn_ppocrv3_2023may.onnx"


def main():
    MODEL_PATH.parent.mkdir(parents=True,exist_ok=True)
    if MODEL_PATH.is_file() and hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest() == MODEL_SHA256:
        print("Verified local text detector already installed")
        return
    temporary = MODEL_PATH.with_suffix(".download")
    try:
        with urllib.request.urlopen(URL,timeout=60) as response, temporary.open("wb") as target:
            shutil.copyfileobj(response,target)
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != MODEL_SHA256:
            raise ValueError("Downloaded model checksum mismatch")
        temporary.replace(MODEL_PATH)
    finally:
        temporary.unlink(missing_ok=True)
    print("Installed and verified local text detector")


if __name__ == "__main__":
    main()
