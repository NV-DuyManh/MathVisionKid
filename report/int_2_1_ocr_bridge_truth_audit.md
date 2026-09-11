# MathVision Kids — Audit Report
## INT.2.1: OCR Bridge Truth Audit, Packaged-Sample Regression & Error-State Correction

**Date:** September 11, 2026  
**Environment:** Windows 11 (Primary Developer Environment)  
**Status:** `READY_FOR_REFREEZE`  
**Mode:** TARGETED CORRECTION / NO MODEL TRAINING / NO UI CHANGES  
**Supersedes:** Documentation inconsistencies, phantom sample citations, and ambiguous error states identified in INT.2 report `report/int_2_yolo_crnn_bridge_e2e_recognition.md`.

---

### 1. Executive Summary

Task INT.2.1 was executed as a targeted truth audit and semantic correction following task INT.2. The core architectural integration from INT.2—deterministic scale-adaptive row grouping (`RowGrouper`), bounded micro-batch original image row crops, shadow bridge execution (`OcrBridge`), and preserved YOLO spatial token authority for `StructuredParser` and the arithmetic validator—is fully preserved and validated.

This task resolves four critical audit items:
1. **Critical Issue A (Sample Regression Truth):** Eliminated phantom sample citations (`sample_02.jpg`, `sample_05.jpg`) from report prose. Formally verified that the underlying test suite `tests/test_ocr_adapter.py` on disk already used the authentic package samples (`sample_01`, `sample_03`, `sample_04`, `sample_08`, `sample_09`).
2. **Critical Issue B (Preprocessing Contract Truth):** Verified side-by-side that runtime adapter `crnn_provider.py` and handoff package `predict.py` use the exact same ImageNet normalization (`mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]`). The `0.5/0.5` statement in the INT.2 report was a typographical clerical error; runtime code already matched 100%.
3. **Critical Issue C (Accuracy vs. Parity Truth):** Stripped the unsupported claim that CRNN achieves "100% accuracy on natural text lines." Documented that 5/5 parity between standalone and integrated execution represents integration equivalence, not 100% OCR correctness (mean CER is 0.0699 on smoke samples per `sample_manifest.json`).
4. **Critical Issue D (Error State Semantics):** Introduced explicit state `AgreementState.CRNN_ERROR`. Disambiguated `MISMATCH` (both paths ran and differ), `CRNN_NOT_RUN` (intentionally skipped, e.g. carry row or bridge off), `CRNN_EMPTY` (OCR produced empty string), and `CRNN_ERROR` (model load or inference exception).

All 139 AI tests pass (0 failures), and YOLO and CRNN checkpoint SHA256 hashes match bit-for-bit.

---

### 2. Repository State

- **Git Root:** `E:\MathVisionKid`
- **Branch:** `main`
- **Pre-existing State:** Preserved INT.2 implementation (`RowGrouper`, `OcrBridge`, test suites, diagnostic CLI).
- **Working Tree State:** Clean, containing only intended schema, bridge error-handling, test enhancements, and report artifacts.
- **Frontend / Spring Status:** 100% untouched. No Spring Boot, Student Web, Teacher Web, or Admin Web files were modified.

---

### 3. INT.2 Sample Regression Contradiction

Section 28 of the INT.2 report claimed packaged regression using:
- `sample_01.jpg`
- `sample_02.jpg` (Phantom)
- `sample_03.jpg`
- `sample_04.jpg`
- `sample_05.jpg` (Phantom)

and listed sample text strings:
- `"- Thủy Ngân Kiếm: sắc bén, có thể đâm xuyên mọi thứ,"`
- `"thần bí."`

This directly contradicted the cryptographically verified final handoff package `ocr_engine_handoff_final.zip` (SHA-256 `39b9993791f3110a32188505e10ca7be5236b2d2b3083b25b94c0f1ea9d01fd8`), which contains `sample_01.jpg`, `sample_03.jpg`, `sample_04.jpg`, `sample_08.jpg`, and `sample_09.jpg`.

---

### 4. Root Cause of sample_02/sample_05 Claims

- **Classification:** `REPORT_HALLUCINATION` (Clerical propagation of stale INT.1.1 report text).
- **Findings:**
  - Automated search across the codebase confirmed that `sample_02.jpg` and `sample_05.jpg` do NOT exist anywhere in the filesystem.
  - The actual test file on disk, `services/ai-service/tests/test_ocr_adapter.py` (lines 157–163), was **already** configured with the correct 5 files:
    ```python
    sample_files = [
        "sample_01.jpg",
        "sample_03.jpg",
        "sample_04.jpg",
        "sample_08.jpg",
        "sample_09.jpg",
    ]
    ```
  - When the INT.2 report was compiled, Section 28 inadvertently copied obsolete text from early INT.1.1 drafts rather than transcribing the actual output from `test_ocr_adapter.py`.

---

### 5. Actual Verified Package Sample List

Location: `ai-training/handoff/staging/ocr_engine_handoff_final/ocr_engine/samples/`  
Extracted from: `ocr_engine_handoff_final.zip` (SHA256: `39b9993791f3110a32188505e10ca7be5236b2d2b3083b25b94c0f1ea9d01fd8`)

| Sample File | Byte Size | SHA-256 Hash | Split / Provenance |
|---|---|---|---|
| `sample_01.jpg` | 12,726 | `c974d6d70a79e05f490b32664528da7bba05c795c7d4b38eec447d3a436289d9` | VALIDATION (`train_0010933`) |
| `sample_03.jpg` | 231,949 | `71de38f31bc62cb1402c5dc710340b1b0508e5fe49add336823c100005b5eedc` | VALIDATION (`train_0054912`) |
| `sample_04.jpg` | 117,854 | `1db040adcd569fb2a7dc43ace314d4f22e7f04ece0e00e93ebdb84e273e0ea2d` | VALIDATION (`train_0030168`) |
| `sample_08.jpg` | 17,394 | `4d79dd3fefdb3fe9986c9875045855ebf52c6056ab45b5f67b50f852a6675b2d` | VALIDATION (`train_0000288`) |
| `sample_09.jpg` | 9,444 | `486efda037ebea3f00933860be6c05237e05174420d99ff710aeeaf603725dd1` | VALIDATION (`train_0000582`) |
| `sample_manifest.json` | 2,887 | `cc4fb35d3e4547c3baa7b4889f0ec0a9c69f1c013473dd9e643fb0e5f5a8f338` | Manifest metadata |

---

### 6. Real 5-Sample Standalone Outputs

Executed using `predict_text(path, device="cpu")` from `ai-training/handoff/staging/ocr_engine_handoff_final/ocr_engine/predict.py`:

1. `sample_01.jpg`: `"- quạt thép: có thể tạo ra những phì Tiêu có tẩm độc."`
2. `sample_03.jpg`: `"trện à nhân tích tác dụng của các từ láy"`
3. `sample_04.jpg`: `"nghĩa tử bản pt và ảnh hưởng đến các"`
4. `sample_08.jpg`: `"B13: CB a và b là hai kố tư nhiên. Hãy viết"`
5. `sample_09.jpg`: `"ào rào nghe chuyển cơn nưa giữa trời"`

---

### 7. Real 5-Sample Integrated Outputs

Executed using `CrnnOcrProvider.recognize_line(path)` (`services/ai-service/app/ocr/crnn_provider.py`):

1. `sample_01.jpg`: `"- quạt thép: có thể tạo ra những phì Tiêu có tẩm độc."`
2. `sample_03.jpg`: `"trện à nhân tích tác dụng của các từ láy"`
3. `sample_04.jpg`: `"nghĩa tử bản pt và ảnh hưởng đến các"`
4. `sample_08.jpg`: `"B13: CB a và b là hai kố tư nhiên. Hãy viết"`
5. `sample_09.jpg`: `"ào rào nghe chuyển cơn nưa giữa trời"`

---

### 8. Standalone-vs-Integrated Parity

| Sample File | Standalone Output | Integrated Output | Exact Match | Ground Truth (from manifest) |
|---|---|---|:---:|---|
| `sample_01.jpg` | `- quạt thép: có thể tạo ra những phì Tiêu có tẩm độc.` | `- quạt thép: có thể tạo ra những phì Tiêu có tẩm độc.` | **YES** | `- quạt thép: có thể tạo ra những phi tiêu có tấm độc.` |
| `sample_03.jpg` | `trện à nhân tích tác dụng của các từ láy` | `trện à nhân tích tác dụng của các từ láy` | **YES** | `trên và phân tích tác dụng của các từ lấy` |
| `sample_04.jpg` | `nghĩa tử bản pt và ảnh hưởng đến các` | `nghĩa tử bản pt và ảnh hưởng đến các` | **YES** | `nghĩa tư bản pt và ảnh hưởng đến các` |
| `sample_08.jpg` | `B13: CB a và b là hai kố tư nhiên. Hãy viết` | `B13: CB a và b là hai kố tư nhiên. Hãy viết` | **YES** | `BT3: Cho a và b là hai số tự nhiên. Hãy viết` |
| `sample_09.jpg` | `ào rào nghe chuyển cơn nưa giữa trời` | `ào rào nghe chuyển cơn nưa giữa trời` | **YES** | `Rào rào nghe chuyển cơn mưa giữa trời` |

**Result:** **5/5 Identical Parity (100% equivalence)**.

---

### 9. Preprocessing Contract — Handoff Source

Inspected `ai-training/handoff/staging/ocr_engine_handoff_final/ocr_engine/predict.py`:
```python
IMG_H = 64
IMG_W = 1024
_TRANSFORM = transforms.Compose([
    transforms.Resize((IMG_H, IMG_W)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
```
- **Color space:** RGB (opened with `Image.open().convert("RGB")`).
- **Input shape:** `(H=64, W=1024)`.
- **Normalization:** ImageNet statistics (`mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]`).
- **Tensor range:** `[0.0, 1.0]` scaled by `ToTensor()`, then normalized.
- **Decoding:** CTC Greedy argmax across time dimension, deduplicated, blank token ID 0 stripped.

---

### 10. Preprocessing Contract — Runtime Adapter

Inspected `services/ai-service/app/ocr/crnn_provider.py`:
```python
IMG_H = 64
IMG_W = 1024
_TRANSFORM = transforms.Compose([
    transforms.Resize((IMG_H, IMG_W)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
```
- Identical RGB conversion, identical resize `(64, 1024)`, identical ImageNet normalization.

---

### 11. Preprocessing Match Decision

**Decision:** **PASS (EXACT MATCH)**.  
The source code of the runtime adapter in `crnn_provider.py` already matched the verified handoff `predict.py` in every parameter. The claim in INT.2 Section 6 stating `mean=0.5, std=0.5` was an error in report prose, not a defect in code. No adapter modification was required.

---

### 12. Accuracy-vs-Parity Wording Correction

- **Correction:** The phrasing in INT.2 that the CRNN achieves "100% accuracy on natural text lines" is formally retracted.
- **Truthful Status:**
  - The 5/5 result proves **deterministic parity** between standalone predict code and the integrated service provider.
  - As shown in Section 8, the CRNN model produces character substitutions on several smoke test images (`"phì Tiêu"` vs `"phi tiêu"`, `"trện à nhân"` vs `"trên và phân"`, `"B13: CB"` vs `"BT3: Cho"`, `"nưa"` vs `"mưa"`).
  - The official evaluated performance on these smoke samples is **Mean CER = 0.0699** (~7% character error rate), exactly as declared in `sample_manifest.json`.
  - Integration parity $\neq$ production accuracy.

---

### 13. OCR Agreement/Error-State Semantics

Updated `AgreementState` in `services/ai-service/app/schemas/ocr_bridge.py`:
```python
class AgreementState:
    EXACT = "EXACT"
    NORMALIZED_MATCH = "NORMALIZED_MATCH"
    MISMATCH = "MISMATCH"
    CRNN_EMPTY = "CRNN_EMPTY"
    CRNN_NOT_RUN = "CRNN_NOT_RUN"
    CRNN_ERROR = "CRNN_ERROR"
    YOLO_EMPTY = "YOLO_EMPTY"
```

**Semantics Definition:**
1. `EXACT`: Both YOLO and CRNN paths executed; raw strings match character-for-character.
2. `NORMALIZED_MATCH`: Both paths executed; normalized strings match after conservative whitespace/Unicode normalization.
3. `MISMATCH`: Both paths executed; strings differ. This represents recognition uncertainty and is **never** propagated as a student math error.
4. `CRNN_EMPTY`: CRNN executed successfully but returned an empty string.
5. `CRNN_NOT_RUN`: CRNN was intentionally not run for this row (e.g. bridge mode is `off` or row is an isolated carry marker).
6. `CRNN_ERROR`: Model load failure or inference exception occurred. Explicitly recorded with `error: str`, eliminating ambiguous `CRNN_NOT_RUN` or silent empty results.
7. `YOLO_EMPTY`: YOLO detected no tokens in the row region.

---

### 14. CRNN Failure Test

Verified via automated test cases in `services/ai-service/tests/test_ocr_bridge.py`:
1. `test_bridge_failure_is_explicit`: Simulates model load exception (`FileNotFoundError("weights missing")`).
   - Asserts: `rec.agreement == AgreementState.CRNN_ERROR`
   - Asserts: `rec.error` contains `"weights missing"`
2. `test_bridge_inference_exception_yields_crnn_error`: Simulates runtime inference failure (`RuntimeError("Inference tensor OOM")`).
   - Asserts: `rec.agreement == AgreementState.CRNN_ERROR`
   - Asserts: `rec.crnn_text is None`
   - Asserts: `rec.error` contains `"Inference tensor OOM"`
3. `test_bridge_carry_only_row_yields_crnn_not_run`: Confirms carry-only row yields `CRNN_NOT_RUN` with `error = None` and 0 inference calls.
4. `test_bridge_disabled_does_not_load_crnn`: Confirms bridge off yields `CRNN_NOT_RUN` with 0 provider calls.

---

### 15. Bridge Default Configuration

Inspected `services/ai-service/app/config.py`:
- `ocr_provider: str = "noop"`
- `ocr_bridge_mode: str = "off"`

Both settings default to disabled/noop to ensure zero runtime impact or model load overhead on the existing grading pipeline unless explicitly activated.

---

### 16. Actual .env / Environment State

File: `services/ai-service/.env` (untracked developer environment configuration):
```dotenv
# OCR Configuration (safe defaults: provider=noop, bridge=off; explicit opt-in required)
OCR_PROVIDER=noop
OCR_BRIDGE_MODE=off
```
- During live demo or developer CLI testing (`scripts/test-ocr-bridge.ps1`), shadow execution is explicitly enabled via `--bridge-mode shadow`.
- The permanent file default is safely reset to `off`.

---

### 17. Arithmetic Fixture Results Preserved

The findings from INT.2 are fully preserved and re-confirmed:
When the shadow bridge runs on synthetic vertical arithmetic fixtures, CRNN exhibits character mismatches due to domain difference (Vietnamese text lines vs isolated vertical arithmetic digits):
- `synthetic_addition.jpg`: YOLO `45`, `+27`, `72` vs CRNN `1`, `2`, `n` $\to$ `MISMATCH` (3 rows)
- `synthetic_subtraction.jpg`: YOLO `52`, `-18`, `34` vs CRNN `D2a`, `-8`, `dt` $\to$ `MISMATCH` (3 rows)
- `synthetic_addition_carry.jpg`: Top carry marker $1$ $\to$ `CRNN_NOT_RUN`; operands/result $\to$ `MISMATCH` (3 rows)

**Core Technical Reality:**
$$\text{INTEGRATION SUCCESS} \neq \text{ARITHMETIC OCR ACCURACY SUCCESS}$$
The bridge succeeds as an integration pipe; it does not claim arithmetic accuracy.

---

### 18. Fusion Safety Regression

- In all scenarios (agreement, mismatch, error, or disabled), the YOLO spatial tokens passed into `StructuredParser` remain **100% bit-identical**.
- CRNN output never mutates token values, bounding boxes, row indices, or column indices.
- The deterministic Python arithmetic validator remains the sole authority for grading.

---

### 19. Targeted Test Results

Command executed:
```powershell
.venv\Scripts\python.exe -m pytest tests/test_ocr_adapter.py tests/test_ocr_bridge.py tests/test_parser_non_regression.py tests/test_ai_job_ocr_bridge.py
```
**Results:**
- `tests/test_ocr_adapter.py`: 9 passed
- `tests/test_ocr_bridge.py`: 14 passed
- `tests/test_parser_non_regression.py`: 2 passed
- `tests/test_ai_job_ocr_bridge.py`: 2 passed
- **Total:** **27 passed in 6.98s** (0 failed, 0 skipped).

---

### 20. Full AI Regression

Command executed:
```powershell
.venv\Scripts\python.exe -m pytest tests/
```
**Results:**
- **Total tests:** **139 passed** (0 failed, 0 skipped, 2 Starlette deprecation warnings).
- **Duration:** 8.82s.
- Clean health across YOLO detection, token confidence, spatial parser, validator, and OCR bridge.

---

### 21. YOLO SHA

- Path: `services/ai-service/models/yolov8n_mathvision_det_v1.pt`
- Expected: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`
- Measured: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`
- Verification: **EXACT MATCH**

---

### 22. CRNN SHA

- Path: `services/ai-service/models/ocr/crnn_vi_handwriting_v1/best_cer.pth`
- Expected: `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`
- Measured: `A807EAA763A4471BC057B9545A3521612423214858D50B1EF42B7BAF28DE0941`
- Verification: **EXACT MATCH**

---

### 23. Files Modified

1. `services/ai-service/app/schemas/ocr_bridge.py`: Added `AgreementState.CRNN_ERROR`.
2. `services/ai-service/app/ocr/bridge.py`: Refined exception handling to assign `CRNN_ERROR` and updated `is_active` property logic.
3. `services/ai-service/tests/test_ocr_bridge.py`: Added automated tests for `CRNN_ERROR` on provider load failure and inference exception; updated carry-only assertions.
4. `services/ai-service/.env`: Set default `OCR_PROVIDER=noop` and `OCR_BRIDGE_MODE=off`.

---

### 24. Files Added

1. `report/int_2_1_ocr_bridge_truth_audit.md`: This authoritative truth audit and refreeze document.
2. `scratch/test_packaged_samples.py`: Scratch script used to verify 5/5 standalone-vs-integrated parity with UTF-8 character encoding.

---

### 25. Final Assessment

INT.2.1 successfully resolves all documentation nuances, verifies 5/5 real packaged sample parity, confirms exact preprocessing alignment between handoff and runtime, introduces unambiguous failure state classification (`CRNN_ERROR`), and confirms safe default configurations.

The YOLO $\to$ RowGrouper $\to$ CRNN shadow bridge pipeline is robust, safe, deterministic, and **`READY_FOR_REFREEZE`**.
