import os
import json
import csv
import argparse

DATA_DIR = "E:/MathVisionKid/data/hwtext_v1"
QUEUE_FILE = os.path.join(DATA_DIR, "annotation_queue.tsv")
MASTER_STATE_FILE = os.path.join(DATA_DIR, "annotation_review_state.json")
PROGRESS_FILE = os.path.join(DATA_DIR, "annotation_progress.json")
VERIFIED_TSV = os.path.join(DATA_DIR, "verified_text_lines.tsv")
MATH_QUEUE_TSV = os.path.join(DATA_DIR, "math_reclassification_queue.tsv")

def load_queue():
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def load_master_state():
    if os.path.exists(MASTER_STATE_FILE):
        with open(MASTER_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_master_state(state):
    with open(MASTER_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def update_progress(state, queue):
    total = len(queue)
    verified = 0
    rejected = 0
    math_reclassified = 0
    text_only_verified = 0
    text_with_contextual_numbers_verified = 0
    
    for row in queue:
        line_id = row["line_id"]
        if line_id in state:
            s = state[line_id]
            if s.get("label_status") == "VERIFIED":
                verified += 1
                if s.get("provisional_class") == "TEXT_ONLY":
                    text_only_verified += 1
                elif s.get("provisional_class") == "TEXT_WITH_CONTEXTUAL_NUMBERS":
                    text_with_contextual_numbers_verified += 1
            elif s.get("label_status") == "REJECTED":
                rejected += 1
                if s.get("review_notes") == "MATH_DOMINANT_MISCLASSIFIED":
                    math_reclassified += 1
                    
    remaining = total - verified - rejected
    
    # Load old progress to get batches info if possible
    batches = []
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            old_p = json.load(f)
            batches = old_p.get("batches", [])
            
    progress = {
        "total": total,
        "verified": verified,
        "rejected": rejected,
        "remaining": remaining,
        "text_only_verified": text_only_verified,
        "text_with_contextual_numbers_verified": text_with_contextual_numbers_verified,
        "math_reclassified": math_reclassified,
        "batches": batches
    }
    
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)
        
    return progress

def extract_verified(state, queue):
    verified_rows = []
    for row in queue:
        line_id = row["line_id"]
        if line_id in state and state[line_id].get("label_status") == "VERIFIED":
            s = state[line_id]
            verified_rows.append({
                "line_id": line_id,
                "crop_path": s.get("crop_path", row.get("crop_path")),
                "verified_text": s.get("verified_text", ""),
                "source_group": s.get("source_group", row.get("source_group")),
                "category": s.get("provisional_class", row.get("provisional_class"))
            })
    
    with open(VERIFIED_TSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["line_id", "crop_path", "verified_text", "source_group", "category"], delimiter="\t")
        writer.writeheader()
        writer.writerows(verified_rows)
        
def extract_math(state, queue):
    math_rows = []
    for row in queue:
        line_id = row["line_id"]
        if line_id in state and state[line_id].get("review_notes") == "MATH_DOMINANT_MISCLASSIFIED":
            s = state[line_id]
            math_rows.append(s)
            
    if math_rows:
        with open(MATH_QUEUE_TSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(math_rows[0].keys()), delimiter="\t")
            writer.writeheader()
            writer.writerows(math_rows)

def merge(export_file):
    queue = load_queue()
    valid_ids = set(row["line_id"] for row in queue)
    state = load_master_state()
    
    with open(export_file, "r", encoding="utf-8") as f:
        export_data = json.load(f)
        
    items = export_data.get("data", export_data) if isinstance(export_data, dict) else export_data
    
    for item in items:
        line_id = item.get("line_id")
        if not line_id or line_id not in valid_ids:
            print(f"Warning: Unknown or invalid line_id {line_id}")
            continue
            
        status = item.get("label_status")
        if status in ["VERIFIED", "REJECTED"]:
            if status == "VERIFIED" and not item.get("verified_text"):
                print(f"Error: {line_id} is VERIFIED but text is empty! Reverting to UNVERIFIED.")
                continue
            state[line_id] = item

    save_master_state(state)
    prog = update_progress(state, queue)
    
    if prog["remaining"] == 0:
        print("All items processed. Extracting verified lines...")
        extract_verified(state, queue)
        extract_math(state, queue)
        print("Dataset ready for QA.")
    else:
        print(f"Merged successfully. {prog['remaining']} items remaining.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--export_file", type=str, required=True, help="Path to the JSON export file from the UI")
    args = parser.parse_args()
    merge(args.export_file)
