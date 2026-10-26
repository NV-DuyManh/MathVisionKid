"""Mount the owner's Drive and create a dedicated thinking run directory."""
import json
from pathlib import Path
from google.colab import drive

drive.mount("/content/drive")
my_drive = Path("/content/drive/MyDrive")
candidates = [p for p in my_drive.iterdir() if p.is_dir() and p.name.strip() == "MathVisionKidAI"]
if len(candidates) != 1:
    raise FileNotFoundError(f"Cần đúng một MathVisionKidAI trong MyDrive; tìm được {len(candidates)}. Không tự chọn hoặc tạo root khác.")
MVK_HOME = candidates[0]
MVK_THINKING_ROOT = MVK_HOME / "ai-training" / "thinking" / "math_text_pilot_v1"
MVK_THINKING_ROOT.mkdir(parents=True, exist_ok=True)
print("MVK_THINKING_ROOT=" + str(MVK_THINKING_ROOT))
# Inspect metadata only, no corpus-wide image/API job.
roots = [MVK_HOME / "datasets" / "gemini_auto_v2", MVK_HOME / "ai-training" / "data" / "manifests"]
summary = []
for root in roots:
    if not root.exists():
        summary.append({"root": str(root), "exists": False}); continue
    manifests = list(root.glob("**/manifest.jsonl"))[:10] if root.name == "gemini_auto_v2" else list(root.glob("*.jsonl"))[:10]
    for manifest in manifests:
        inspected = 0; text_rows = 0; solution_rows = 0
        with manifest.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip(): continue
                row = json.loads(line); inspected += 1
                text_rows += bool(row.get("text") or row.get("transcription_verbatim"))
                solution_rows += bool(row.get("problem") and row.get("solution") and row.get("expected_answer") is not None)
                if inspected >= 100: break
        summary.append({"manifest": str(manifest), "inspected_first_rows": inspected, "ocr_text_rows": text_rows, "explicit_problem_solution_answer_rows": solution_rows})
report = {"stage": "thinking_source_inspection", "mode": "metadata_sample_only", "manifests": summary,
          "decision": "Use separate exact-arithmetic synthetic pilot; do not promote OCR/student work to correct solutions."}
(MVK_THINKING_ROOT / "source_inspection.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
