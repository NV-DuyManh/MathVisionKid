"""
Forwarding alias: Qwen2VL has been upgraded to Qwen 3 VL Plus (qwen-vl-plus).
"""
from labeling.qwen3vl_backend import (
    Qwen3VLPlusPrelabeler,
    QwenVLPlusPrelabeler,
    Qwen2VLPrelabeler,
    get_qwen_api_key,
)

__all__ = [
    "Qwen3VLPlusPrelabeler",
    "QwenVLPlusPrelabeler",
    "Qwen2VLPrelabeler",
    "get_qwen_api_key",
]
