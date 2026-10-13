"""Run real CPU inference without providers; this checks compatibility, not OCR accuracy.

Run inside the AI image with models mounted read-only and networking disabled.
"""
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import platform
import secrets

from check_production import check_models


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, default=Path("/app/models"))
    args = parser.parse_args()
    errors = check_models(args.models)
    if errors:
        raise RuntimeError("; ".join(errors))
    # No real credentials or external calls are needed for local inference.
    os.environ.update(GROQ_ENABLED="false", GEMINI_ENABLED="false",
                      INTERNAL_API_KEY=secrets.token_hex(32), MINIO_ACCESS_KEY="model-smoke",
                      MINIO_SECRET_KEY=secrets.token_hex(32))

    import cv2
    import numpy as np
    import torch
    from PIL import Image
    from app.ocr.crnn_provider import CrnnOcrProvider
    from app.recognition.manifest import ModelManifestLoader
    from app.recognition.model_engine import ModelRecognitionEngine
    from app.recognition import text_detector

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    bgr = np.full((128, 320, 3), 255, np.uint8)
    cv2.putText(bgr, "12 + 34", (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
    image = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    provider = CrnnOcrProvider(args.models / "ocr/crnn_vi_handwriting_v1", device="cpu")
    text, confidence = provider.recognize_line_with_confidence(image)
    if not isinstance(text, str) or not math.isfinite(confidence) or provider.model_forward_call_count != 1:
        raise RuntimeError("CRNN did not perform a valid real inference.")
    print("PASS: CRNN checkpoint loaded; one CPU forward pass and finite confidence.", flush=True)

    artifact = args.models / "yolov8n_mathvision_det_v1.pt"
    manifest = ModelManifestLoader(str(args.models / "model_manifest.json")).load_and_verify_artifact(str(artifact))
    engine = ModelRecognitionEngine(manifest=manifest, artifact_path=str(artifact))
    if not engine.is_ready or len(engine._yolo_model(image, imgsz=320, device="cpu", verbose=False)) != 1:
        raise RuntimeError("YOLO did not perform a valid real inference.")
    print("PASS: YOLO checkpoint and CPU forward pass.", flush=True)

    text_detector.MODEL_PATH = args.models / "ocr/text_detection_cn_ppocrv3_2023may.onnx"
    if text_detector._infer_regions(bgr) is None:
        raise RuntimeError("The ONNX detector fell back instead of running its real model.")
    print("PASS: OpenCV ONNX text detector inference.", flush=True)
    print(f"PASS: {platform.machine()} runtime and four checksums; no accuracy percentage or end-to-end cloud claim.")


if __name__ == "__main__":
    main()
