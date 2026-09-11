# MathVision Kids
## INT.1.1.2 — OCR Provenance Report Errata & Refreeze Confirmation

**Date:** September 11, 2026  
**Environment:** Windows 11 (Primary Developer Environment)  
**Status:** READY_FOR_FINAL_REFREEZE  
**Mode:** REPORT-ONLY CORRECTION / NO SOURCE CHANGES  
**Supersedes:** Documentation inconsistencies in INT.1.1.1 Section 7, Section 8, and Section 19 regarding `sample_manifest.json` byte size, Git working tree description, and commit chronology.

---

### 1. Executive Summary

Task INT.1.1.2 was executed strictly as a report-only errata correction to reconcile remaining documentation nuances from INT.1.1.1 without altering any underlying codebase, models, weights, or verified integration behavior.

**Preserved Accepted Technical Findings:**
- External ZIP (`E:\ocr_engine_handoff_final.zip`): `22,555,507` bytes, SHA-256 `39b9993791f3110a32188505e10ca7be5236b2d2b3083b25b94c0f1ea9d01fd8`.
- Incoming ZIP (`ai-training/handoff/incoming/ocr_engine_handoff_final.zip`): 100% byte-identical to external ZIP.
- Checkpoint `best_cer.pth`: `23,856,925` bytes, SHA-256 `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`.
- Runtime Checkpoint (`services/ai-service/models/ocr/crnn_vi_handwriting_v1/best_cer.pth`): Exact cryptographic match.
- Actual Archive Sample Directory: `ocr_engine/samples/`.
- Actual Packaged Sample Files: `sample_01.jpg`, `sample_03.jpg`, `sample_04.jpg`, `sample_08.jpg`, `sample_09.jpg`.
- Directory `sample_lines`: Formally verified as non-existent (prior report hallucination).
- Standalone vs Integrated Parity: 5/5 identical character-for-character across single and batch runs.
- Default OCR Provider: `noop` (explicit opt-in required for CRNN).
- Silent Fallback: Formally verified as absent (invalid provider raises `ValueError`).
- Source Code & Model Weights: 100% untouched across INT.1.1.1 and INT.1.1.2.

---

### 2. `sample_manifest` Size Correction

In the INT.1.1.1 audit report, Section 7 previously displayed:
- Expected bytes: `2,810 (est)`
- Measured bytes: `2,887`
- SHA-256: `cc4fb35d3e4547c3baa7b4889f0ec0a9c69f1c013473dd9e643fb0e5f5a8f338`
- Status: `EXACT MATCH`

**Resolution & Formal Errata:**
- Claiming an exact byte-size match between `2,810` and `2,887` was internally inconsistent.
- The physical uncompressed byte length of `ocr_engine/samples/sample_manifest.json` inside the verified archive is and has always been **`2,887` bytes**.
- The pre-audit figure `2,810` was a stale clerical estimate / typographical error (`REPORT_ERROR`).
- **Cryptographic Content Status:** **PASS** (100% identical SHA-256 hash `cc4fb35d3e4547c3baa7b4889f0ec0a9c69f1c013473dd9e643fb0e5f5a8f338`).
- **Authoritative Expected Byte Size:** Officially corrected to **`2,887` bytes**.

---

### 3. Corrected Archive Expectation

The overarching package integrity statement is refined to eliminate contradiction:

> "All directly measured archive member SHA256 values match the accepted final package. All accepted byte sizes match after correcting the historical sample_manifest.json size typo from 2,810 to 2,887 bytes."

#### Comprehensive Corrected Archive Inventory:

| Member Name | Authoritative Bytes | Measured Bytes | Authoritative SHA-256 | Measured SHA-256 | Verification Status |
|---|---|---|---|---|---|
| `ocr_engine/best_cer.pth` | 23,856,925 | 23,856,925 | `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941` | `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941` | **MATCH (100%)** |
| `ocr_engine/model.py` | 989 | 989 | `8abd87a912d120bbe1e1538f01c71b439dc01e519f36457c1c42da6c7c79e5ed` | `8abd87a912d120bbe1e1538f01c71b439dc01e519f36457c1c42da6c7c79e5ed` | **MATCH (100%)** |
| `ocr_engine/vocab.json` | 4,448 | 4,448 | `6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d` | `6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d` | **MATCH (100%)** |
| `ocr_engine/predict.py` | 6,137 | 6,137 | `7b458889a9b7274dfbde67824a86b5a47a6ec06a7309531c3a59e9b1d6dc84cc` | `7b458889a9b7274dfbde67824a86b5a47a6ec06a7309531c3a59e9b1d6dc84cc` | **MATCH (100%)** |
| `ocr_engine/model_manifest.json` | 4,992 | 4,992 | `f3e8035e5bcaafd48c0af19eebfd73075c48684c68a39c2f0558e5d6efabdf63` | `f3e8035e5bcaafd48c0af19eebfd73075c48684c68a39c2f0558e5d6efabdf63` | **MATCH (100%)** |
| `ocr_engine/MODEL_CARD.md` | 10,504 | 10,504 | `ac84192c068e05c6ae0c9c73b4d3e8f3d42eba650313ea9a28301d0150bb5ef2` | `ac84192c068e05c6ae0c9c73b4d3e8f3d42eba650313ea9a28301d0150bb5ef2` | **MATCH (100%)** |
| `ocr_engine/README.md` | 8,698 | 8,698 | `a7d84a007a48f6ab7fb34428b22580ad235bb7339b81909b9853e830bfe6f768` | `a7d84a007a48f6ab7fb34428b22580ad235bb7339b81909b9853e830bfe6f768` | **MATCH (100%)** |
| `ocr_engine/test_predict.py` | 7,096 | 7,096 | `0fc743e76de731857fd2083ace8971e5afb33291a6656e823c59b1b7769b58f2` | `0fc743e76de731857fd2083ace8971e5afb33291a6656e823c59b1b7769b58f2` | **MATCH (100%)** |
| `ocr_engine/requirements.txt` | 314 | 314 | `8841aa8b574b3d582f6130e6016264f0715eacbb17c489c603aa068e555a991e` | `8841aa8b574b3d582f6130e6016264f0715eacbb17c489c603aa068e555a991e` | **MATCH (100%)** |
| `ocr_engine/requirements-verified.txt` | 493 | 493 | `8c486026d84d6d7b02816638e757f78961be62b670bef77c01129bc547289517` | `8c486026d84d6d7b02816638e757f78961be62b670bef77c01129bc547289517` | **MATCH (100%)** |
| `ocr_engine/__init__.py` | 125 | 125 | `89bbf35150afd25b7aa82113865af93f03f91d61ed38f63d1637063ecf2a46c3` | `89bbf35150afd25b7aa82113865af93f03f91d61ed38f63d1637063ecf2a46c3` | **MATCH (100%)** |
| `ocr_engine/samples/sample_manifest.json` | 2,887 | 2,887 | `cc4fb35d3e4547c3baa7b4889f0ec0a9c69f1c013473dd9e643fb0e5f5a8f338` | `cc4fb35d3e4547c3baa7b4889f0ec0a9c69f1c013473dd9e643fb0e5f5a8f338` | **MATCH (100%)** |
| `ocr_engine/samples/sample_01.jpg` | 12,726 | 12,726 | `c974d6d70a79e05f490b32664528da7bba05c795c7d4b38eec447d3a436289d9` | `c974d6d70a79e05f490b32664528da7bba05c795c7d4b38eec447d3a436289d9` | **MATCH (100%)** |
| `ocr_engine/samples/sample_03.jpg` | 231,949 | 231,949 | `71de38f31bc62cb1402c5dc710340b1b0508e5fe49add336823c100005b5eedc` | `71de38f31bc62cb1402c5dc710340b1b0508e5fe49add336823c100005b5eedc` | **MATCH (100%)** |
| `ocr_engine/samples/sample_04.jpg` | 117,854 | 117,854 | `1db040adcd569fb2a7dc43ace314d4f22e7f04ece0e00e93ebdb84e273e0ea2d` | `1db040adcd569fb2a7dc43ace314d4f22e7f04ece0e00e93ebdb84e273e0ea2d` | **MATCH (100%)** |
| `ocr_engine/samples/sample_08.jpg` | 17,394 | 17,394 | `4d79dd3fefdb3fe9986c9875045855ebf52c6056ab45b5f67b50f852a6675b2d` | `4d79dd3fefdb3fe9986c9875045855ebf52c6056ab45b5f67b50f852a6675b2d` | **MATCH (100%)** |
| `ocr_engine/samples/sample_09.jpg` | 9,444 | 9,444 | `486efda037ebea3f00933860be6c05237e05174420d99ff710aeeaf603725dd1` | `486efda037ebea3f00933860be6c05237e05174420d99ff710aeeaf603725dd1` | **MATCH (100%)** |

---

### 4. Git Working Tree Truth

Direct execution of `git status --short`:
```
 M services/ai-service/app/config.py
 M services/ai-service/app/ocr/factory.py
 M services/ai-service/app/ocr/noop_provider.py
 M services/ai-service/tests/test_ocr_adapter.py
 M services/business-api/src/test/java/com/mathvisionkids/api/submission/SubmissionControllerTest.java
?? ai-training/handoff/staging/ocr_engine_handoff_final_verified/
?? report/int_1_1_1_ocr_artifact_provenance_reconciliation.md
?? report/int_1_1_2_ocr_refreeze_errata.md
?? report/int_1_1_teacher_serialization_ocr_final_closure.md
```

**Precise Working Tree State:**
1. **Tracked Source Modifications:** Exactly 5 files, all intentionally retained from the accepted INT.1.1 closure (safe default `noop`, explicit CRNN opt-in, reject invalid provider, and Spring Boot score override test).
2. **Unexpected Tracked Source Modifications:** Exactly **0** (zero unexpected tracked modifications).
3. **Untracked Elements:** Strictly new audit reports (`report/int_1_1_*.md`) and the temporary verification extraction directory (`ai-training/handoff/staging/ocr_engine_handoff_final_verified/`).
4. **Git Artifact Policy Compliance:** Large binaries (`best_cer.pth`, `*.pt`), incoming archives (`*.zip`), virtual environments (`.venv`), and compiler caches are strictly ignored per `.gitignore`.
5. **Leak Assessment:** Zero binary model weight leaks, zero credential leaks, zero unwanted commits.

---

### 5. `b87a028` Commit Chronology

- **Commit ID:** `b87a028fb3b398b6ea9ef97e43c2dbd31c400cea`
- **Author Date:** `Thu Sep 10 22:51:51 2026 +0700`
- **Commit Message:** `"feat: complete Teacher UI refreeze, backend closure and handwritten OCR staging (UI.2, UI.2.2, INT.1)"`
- **Chronology Classification:** **`PRE_EXISTING`**
- **Audit Verification:**
  - Commit `b87a028` was committed during task INT.1 on September 10, 2026.
  - It pre-existed before INT.1.1, INT.1.1.1, and INT.1.1.2.
  - **Neither INT.1.1, INT.1.1.1, nor INT.1.1.2 created any git commits.**
  - Zero git commits or pushes have been performed in accordance with explicit constraints.

---

### 6. Verified Extraction Retention Note

- **Path:** `ai-training/handoff/staging/ocr_engine_handoff_final_verified/`
- **Classification:** **`TEMP_AUDIT_EVIDENCE`**
- **Necessity Assessment:**
  - The primary handoff staging directory `ai-training/handoff/staging/ocr_engine_handoff_final/` is verified 100% byte-identical to the incoming ZIP.
  - Its non-binary member files are already tracked in commit `b87a028`.
  - Therefore, `ocr_engine_handoff_final_verified/` is not strictly necessary for production or runtime operation.
  - It was generated as isolated cryptographic evidence for the INT.1.1.1 audit.
  - **Retention Policy:** Kept in place for owner audit review; safe to remove in subsequent hygiene/cleanup passes if desired.

---

### 7. Source Changes

- **Source Code Changes in INT.1.1.1 / INT.1.1.2:** Exactly **0** (zero source code modifications).
- Frontend UI (Student Mobile, Teacher Web, Admin Web): Untouched.
- Backend API (Spring Boot): Untouched.
- AI Services (FastAPI, YOLO, Parser): Untouched.

---

### 8. Artifact Changes

- Weights & Checkpoints (`best_cer.pth`, `yolov8n_mathvision_det_v1.pt`, `crnn_mathvision_ocr_v1.pth`): Untouched.
- Cryptographic hash of `best_cer.pth` (`a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`): Completely preserved.

---

### 9. Final Refreeze Decision

All documentation errata, file size inconsistencies, working tree terminology ambiguities, and commit chronology questions have been fully clarified and resolved with cryptographic accuracy.

**Decision:** **READY_FOR_FINAL_REFREEZE**
