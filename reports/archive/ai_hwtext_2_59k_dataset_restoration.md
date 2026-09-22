# AI.HWTEXT.2 Dataset Restoration & Search

**STATUS: BLOCKED_DATASET_NOT_PRESENT**

## 1. Owner 173 Dataset Parked
The 173-image owner dataset (and its derived 510 crops and annotation UI) has been successfully removed from active paths and parked under `ai-training/parking/owner_173_untrained/`. It will not contaminate any training or evaluation pipelines. 

## 2. 59k Raw Data Search
Extensive search was conducted for the historical 59,462 Vietnamese handwriting train samples and 500 frozen validation samples.
- **`D:\nhom6\train thử\external\Viet-Handwriting-OCR-v2\extracted`**: The entire `D:\nhom6` path does not exist on this machine.
- **`E:\MathVisionKid\ai-training\`**: Only contains directories but no 59k dataset.
- **Repo-wide Search**: A recursive search across the entire `E:\MathVisionKid` workspace only found 909 `.jpg` files total, which includes web assets, test fixtures, and the parked 510 crops. 

## 3. Official Checkpoint Verification
The production checkpoint `services/ai-service/models/ocr/crnn_vi_handwriting_v1/best_cer.pth` exists.
- **Expected SHA256**: `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`
- **Actual SHA256**: `A807EAA763A4471BC057B9545A3521612423214858D50B1EF42B7BAF28DE0941` (PASS)

## 4. Conclusion & Hard Stop
While the legacy model checkpoint exists, the RAW 59k images and authoritative text labels are missing from this machine. Without the raw data, it is impossible to rebuild the data manifests, perform text-only cleanup, or run Candidate B (aspect-aware batching) because we cannot load the images.

**Per instruction #3: HARD STOP IF RAW 59K DATA IS ABSENT.**
Training is blocked. We will NOT reconstruct data from predictions, nor download an unverified dataset from the internet. Owner must provide the 59k raw data to proceed.
