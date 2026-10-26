"""Small Colab probe; it does not mount Drive, install packages or train."""
import importlib.metadata
import json
import platform
from pathlib import Path

import torch

result = {
    "stage": "math_thinking_preflight",
    "python": platform.python_version(),
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "drive_mounted": Path("/content/drive/MyDrive").is_dir(),
}
if torch.cuda.is_available():
    result["gpu"] = torch.cuda.get_device_name(0)
    result["gpu_memory_gib"] = round(torch.cuda.get_device_properties(0).total_memory / 2**30, 2)
for package in ("transformers", "peft", "accelerate", "bitsandbytes"):
    try:
        result[package] = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        result[package] = None
print("MVK_PREFLIGHT=" + json.dumps(result, ensure_ascii=False))
