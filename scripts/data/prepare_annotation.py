import os
import csv
import json
import shutil
import math
import numpy as np

def main():
    DATA_DIR = "E:/MathVisionKid/data/hwtext_v1"
    ANNOTATION_QUEUE = os.path.join(DATA_DIR, "annotation_queue.tsv")
    BATCHES_DIR = os.path.join(DATA_DIR, "annotation_batches")
    
    if not os.path.exists(ANNOTATION_QUEUE):
        print("Error: annotation_queue.tsv not found.")
        return
        
    with open(ANNOTATION_QUEUE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        lines = list(reader)
        
    print(f"Loaded {len(lines)} candidates for annotation.")
    
    # Verify counts (expected: 331 text lines total)
    counts = {"TEXT_ONLY": 0, "TEXT_WITH_CONTEXTUAL_NUMBERS": 0}
    for row in lines:
        c = row.get("provisional_class")
        if c in counts:
            counts[c] += 1
            
    print(f"TEXT_ONLY: {counts['TEXT_ONLY']}")
    print(f"TEXT_WITH_CONTEXTUAL_NUMBERS: {counts['TEXT_WITH_CONTEXTUAL_NUMBERS']}")
    
    # Priority sorting
    # A: clear text -> high quality_score (less blur), TEXT_ONLY
    # B: TEXT_WITH_CONTEXTUAL_NUMBERS with high quality
    # C/D: lower quality score
    def get_priority_score(row):
        score = float(row.get("quality_score", 0))
        if row.get("provisional_class") == "TEXT_WITH_CONTEXTUAL_NUMBERS":
            score -= 1000 # lower priority than TEXT_ONLY
        return score
        
    lines.sort(key=get_priority_score, reverse=True)
    
    # Build batches
    batch_size = 25
    num_batches = math.ceil(len(lines) / batch_size)
    
    os.makedirs(BATCHES_DIR, exist_ok=True)
    
    batch_metadata = []
    
    for i in range(num_batches):
        batch_id = f"batch_{i+1:03d}"
        batch_path = os.path.join(BATCHES_DIR, batch_id)
        os.makedirs(batch_path, exist_ok=True)
        
        batch_lines = lines[i*batch_size : (i+1)*batch_size]
        
        # Save batch TSV
        batch_tsv = os.path.join(batch_path, f"{batch_id}.tsv")
        with open(batch_tsv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=batch_lines[0].keys(), delimiter="\t")
            writer.writeheader()
            writer.writerows(batch_lines)
            
        # Save batch JSON for the UI
        batch_json = os.path.join(batch_path, f"{batch_id}.json")
        with open(batch_json, "w", encoding="utf-8") as f:
            json.dump(batch_lines, f, ensure_ascii=False, indent=2)
            
        batch_metadata.append({
            "batch_id": batch_id,
            "count": len(batch_lines),
            "status": "pending"
        })
        
    # Generate progress json
    progress = {
        "total": len(lines),
        "verified": 0,
        "rejected": 0,
        "remaining": len(lines),
        "TEXT_ONLY_verified": 0,
        "TEXT_WITH_CONTEXTUAL_NUMBERS_verified": 0,
        "batches": batch_metadata
    }
    
    with open(os.path.join(DATA_DIR, "annotation_progress.json"), "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)
        
    # Generate a lightweight local HTML UI
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MathVision Kids - Annotation UI</title>
    <style>
        body { font-family: sans-serif; background: #f4f4f9; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: #fff; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .crop-img { max-width: 100%; height: auto; border: 1px solid #ccc; margin-bottom: 10px; }
        .info { color: #666; font-size: 14px; margin-bottom: 20px; }
        .prelabel { background: #eef; padding: 10px; font-family: monospace; font-size: 18px; border-left: 4px solid #66f; margin-bottom: 20px; }
        input[type="text"] { width: 100%; padding: 10px; font-size: 18px; margin-bottom: 20px; box-sizing: border-box; }
        button { padding: 10px 20px; font-size: 16px; cursor: pointer; margin-right: 10px; border: none; border-radius: 4px; }
        .btn-accept { background: #4caf50; color: white; }
        .btn-reject { background: #f44336; color: white; }
        .btn-nav { background: #2196f3; color: white; }
        .status { margin-top: 20px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Local Annotation Tool</h2>
        <input type="file" id="fileInput" accept=".json" />
        <p class="info">Please load a batch JSON file (e.g. batch_001.json)</p>
        
        <div id="editor" style="display: none;">
            <h3 id="lineId"></h3>
            <p id="category" class="info"></p>
            <img id="cropImg" class="crop-img" src="" alt="crop image"/>
            
            <p><strong>Pre-label (Suggestion):</strong></p>
            <div id="prelabel" class="prelabel"></div>
            
            <p><strong>Verified Text:</strong></p>
            <input type="text" id="verifiedText" />
            
            <div>
                <button class="btn-accept" id="btnAccept">Accept & Next (Enter)</button>
                <button class="btn-reject" id="btnReject">Reject (Del)</button>
                <button class="btn-nav" id="btnPrev">Prev (Left)</button>
                <button class="btn-nav" id="btnExport">Export Batch JSON</button>
            </div>
            
            <p class="status" id="statusText"></p>
        </div>
    </div>

    <script>
        let batchData = [];
        let currentIndex = 0;
        
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    batchData = JSON.parse(e.target.result);
                    currentIndex = 0;
                    document.getElementById('editor').style.display = 'block';
                    renderCurrent();
                } catch(err) {
                    alert("Error parsing JSON!");
                }
            };
            reader.readAsText(file);
        });
        
        function renderCurrent() {
            if (currentIndex < 0 || currentIndex >= batchData.length) {
                document.getElementById('statusText').innerText = "Batch complete! Please Export.";
                return;
            }
            const item = batchData[currentIndex];
            document.getElementById('lineId').innerText = `Item ${currentIndex+1} / ${batchData.length} — ${item.line_id}`;
            document.getElementById('category').innerText = `Category: ${item.provisional_class} | Score: ${parseFloat(item.quality_score).toFixed(1)}`;
            // Path relative mapping
            document.getElementById('cropImg').src = "../../" + item.crop_path;
            
            document.getElementById('prelabel').innerText = item.raw_prelabel || "(empty)";
            document.getElementById('verifiedText').value = item.verified_text || item.raw_prelabel || "";
            document.getElementById('verifiedText').focus();
            
            const statusColor = item.label_status === 'VERIFIED' ? 'green' : (item.label_status === 'REJECTED' ? 'red' : 'black');
            document.getElementById('statusText').innerHTML = `Current Status: <span style="color:${statusColor}">${item.label_status}</span>`;
        }
        
        function saveCurrent(status) {
            if (currentIndex >= 0 && currentIndex < batchData.length) {
                const item = batchData[currentIndex];
                item.verified_text = status === 'REJECTED' ? '' : document.getElementById('verifiedText').value;
                item.label_status = status;
                
                // Advance
                currentIndex++;
                renderCurrent();
            }
        }
        
        document.getElementById('btnAccept').addEventListener('click', () => saveCurrent('VERIFIED'));
        document.getElementById('btnReject').addEventListener('click', () => saveCurrent('REJECTED'));
        document.getElementById('btnPrev').addEventListener('click', () => {
            if (currentIndex > 0) { currentIndex--; renderCurrent(); }
        });
        
        document.getElementById('btnExport').addEventListener('click', () => {
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(batchData, null, 2));
            const dlAnchorElem = document.createElement('a');
            dlAnchorElem.setAttribute("href", dataStr);
            dlAnchorElem.setAttribute("download", "reviewed_batch.json");
            dlAnchorElem.click();
        });
        
        window.addEventListener('keydown', (e) => {
            if (document.getElementById('editor').style.display === 'none') return;
            if (e.key === 'Enter') {
                document.getElementById('btnAccept').click();
            }
            if (e.key === 'Delete' && e.ctrlKey) {
                document.getElementById('btnReject').click();
            }
            if (e.key === 'ArrowLeft' && e.ctrlKey) {
                document.getElementById('btnPrev').click();
            }
        });
    </script>
</body>
</html>"""

    with open(os.path.join(DATA_DIR, "annotation_tool.html"), "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Created {num_batches} batches.")
    print("Annotation preparation complete.")

if __name__ == "__main__":
    main()
