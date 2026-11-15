"""Evaluate local Vietnamese OCR on generated text. Never accepts user images."""

import json
import re
import unicodedata

import numpy as np
from paddleocr import PaddleOCR
from PIL import Image, ImageDraw, ImageFont


def normalized(value):
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def classify_printed_probe(texts, scores):
    """Experimental policy for printed fixtures; never use as an upload verdict."""
    if not texts or len(texts) != len(scores) or min(scores) < 0.80:
        return "uncertain"
    for text in texts:
        line = normalized(text)
        if re.search(r"[^0-9\s+\-×÷*/=.,()−]", line):
            return "reject"
        if re.search(r"\d(?:[ .-]?\d){8,}", line):
            return "reject"
    return "allow"


def main():
    recognizer = PaddleOCR(
        text_detection_model_name="PP-OCRv5_mobile_det",
        text_recognition_model_name="latin_PP-OCRv5_mobile_rec",
        device="cpu",
        enable_mkldnn=False,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    cases = [
        ("printed-name", "Họ và tên: Nguyễn Văn Mẫu", "Nguyễn Văn Mẫu"),
        ("printed-address", "Địa chỉ: 12 đường Hoa Mẫu", "12 đường Hoa Mẫu"),
        ("printed-email", "Email: test@example.invalid", "test@example.invalid"),
        ("printed-phone", "Số điện thoại: 0900 000 000", "0900 000 000"),
        ("arithmetic", "12 + 34 = 46", "12 + 34 = 46"),
        ("unlabeled-phone", "0900 000 000", "0900 000 000"),
        ("unlabeled-name", "Nguyễn Văn Mẫu", "Nguyễn Văn Mẫu"),
        ("blank", "", ""),
    ]
    for category, text, expected in cases:
        image = Image.new("RGB", (900, 120), "white")
        ImageDraw.Draw(image).text((25, 30), text, font=font, fill="black")
        results = list(recognizer.predict(np.asarray(image)))
        texts = [line for result in results for line in result["rec_texts"]]
        scores = [score for result in results for score in result["rec_scores"]]
        observed = " ".join(texts)
        print(json.dumps({
            "category": category,
            "matched": normalized(expected) in normalized(observed),
            "syntheticTranscript": observed,
            "probeDecision": classify_printed_probe(texts, scores),
        }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
