import os
import csv
import json
import unicodedata

DATA_DIR = "E:/MathVisionKid/data/hwtext_v1"
VERIFIED_TSV = os.path.join(DATA_DIR, "verified_text_lines.tsv")
PROGRESS_FILE = os.path.join(DATA_DIR, "annotation_progress.json")
QA_REPORT = os.path.join(DATA_DIR, "verified_label_qa.json")
VOCAB_REPORT = os.path.join(DATA_DIR, "vocab_coverage_report.txt")
VOCAB_FILE = "E:/MathVisionKid/services/ai-service/app/ocr/vocab.json"

def main():
    if not os.path.exists(PROGRESS_FILE):
        print("Progress file missing.")
        return
        
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        prog = json.load(f)
        
    if prog.get("remaining", -1) > 0:
        print("ANNOTATION_INCOMPLETE: Cannot QA until all lines are reviewed.")
        return
        
    if not os.path.exists(VERIFIED_TSV):
        print("VERIFIED_TSV missing. Did merge script complete?")
        return
        
    with open(VERIFIED_TSV, "r", encoding="utf-8") as f:
        verified_lines = list(csv.DictReader(f, delimiter="\t"))
        
    errors = []
    seen_ids = set()
    all_chars = set()
    
    for row in verified_lines:
        lid = row["line_id"]
        text = row["verified_text"]
        cat = row["category"]
        
        if lid in seen_ids:
            errors.append(f"Duplicate line_id: {lid}")
        seen_ids.add(lid)
        
        if not text.strip():
            errors.append(f"Empty text for VERIFIED line: {lid}")
            
        if text != unicodedata.normalize("NFC", text):
            errors.append(f"Text not NFC normalized: {lid}")
            
        if cat == "MATH_DOMINANT":
            errors.append(f"MATH_DOMINANT contamination in text dataset: {lid}")
            
        # check file exists
        crop_path = os.path.join("E:/MathVisionKid", row["crop_path"])
        if not os.path.exists(crop_path):
            errors.append(f"Crop image missing: {row['crop_path']}")
            
        for c in text:
            all_chars.add(c)
            
    # Vocab coverage
    with open(VOCAB_FILE, "r", encoding="utf-8") as f:
        vocab = json.load(f)
    
    vocab_set = set(vocab.keys())
    oov_chars = all_chars - vocab_set
    
    with open(VOCAB_REPORT, "w", encoding="utf-8") as f:
        f.write(f"Total Unique Characters: {len(all_chars)}\n")
        f.write(f"Covered Characters: {len(all_chars) - len(oov_chars)}\n")
        f.write(f"OOV Characters: {len(oov_chars)}\n")
        if oov_chars:
            f.write(f"OOV List: {list(oov_chars)}\n")
            
    qa_result = {
        "status": "PASS" if not errors and not oov_chars else "FAIL",
        "errors": errors,
        "oov_chars": list(oov_chars),
        "total_verified": len(verified_lines)
    }
    
    with open(QA_REPORT, "w", encoding="utf-8") as f:
        json.dump(qa_result, f, indent=2)
        
    if qa_result["status"] == "PASS":
        print("READY_FOR_TRAINING")
    elif oov_chars:
        print("BLOCKED_VOCAB")
    else:
        print("QA_FAIL")
        
if __name__ == "__main__":
    main()
