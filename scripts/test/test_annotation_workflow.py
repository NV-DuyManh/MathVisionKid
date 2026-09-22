import os
import json
import subprocess
import shutil

DATA_DIR = "E:/MathVisionKid/data/hwtext_v1"
QUEUE_FILE = os.path.join(DATA_DIR, "annotation_queue.tsv")
PROGRESS_FILE = os.path.join(DATA_DIR, "annotation_progress.json")
MASTER_STATE = os.path.join(DATA_DIR, "annotation_review_state.json")
MERGE_SCRIPT = "E:/MathVisionKid/scripts/merge_hwtext_annotations.py"
QA_SCRIPT = "E:/MathVisionKid/scripts/qa_hwtext_verified_labels.py"

def test():
    print("Testing annotation workflow...")
    # Read the queue to get 3 items
    import csv
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        queue = list(csv.DictReader(f, delimiter="\t"))
        
    item1 = dict(queue[0])
    item2 = dict(queue[1])
    item3 = dict(queue[2])
    
    # Mock user actions
    item1["label_status"] = "VERIFIED"
    item1["verified_text"] = "This is a test edit"
    
    item2["label_status"] = "REJECTED"
    item2["verified_text"] = ""
    item2["review_notes"] = "MATH_DOMINANT_MISCLASSIFIED"
    
    item3["label_status"] = "VERIFIED"
    item3["verified_text"] = item3["raw_prelabel"]
    
    export_mock = {
        "type": "export",
        "timestamp": "test",
        "data": [item1, item2, item3]
    }
    
    export_file = os.path.join(DATA_DIR, "mock_export.json")
    with open(export_file, "w", encoding="utf-8") as f:
        json.dump(export_mock, f)
        
    # Test Merge
    subprocess.run(["python", MERGE_SCRIPT, "--export_file", export_file])
    
    with open(PROGRESS_FILE, "r") as f:
        prog = json.load(f)
        
    print(f"Progress verified: {prog['verified']}")
    print(f"Progress rejected: {prog['rejected']}")
    print(f"Math reclassified: {prog['math_reclassified']}")
    
    assert prog["verified"] == 2
    assert prog["rejected"] == 1
    assert prog["math_reclassified"] == 1
    assert prog["remaining"] == len(queue) - 3
    
    # Restore state
    if os.path.exists(MASTER_STATE):
        os.remove(MASTER_STATE)
    
    # Reset progress
    with open(PROGRESS_FILE, "w") as f:
        prog["verified"] = 0
        prog["rejected"] = 0
        prog["remaining"] = len(queue)
        json.dump(prog, f)
        
    print("All tests passed! Restored state.")
    
if __name__ == "__main__":
    test()
