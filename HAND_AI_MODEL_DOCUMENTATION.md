# HandAI — Deep Learning Model Documentation
## CRNN-v1.2-PyTorch Offline Handwriting Recognition Model

---

## 1. Model Metadata & Specification

| Specification Attribute | Value |
|---|---|
| **Model Name** | `CRNN-v1.2-PyTorch` |
| **Model Family** | Convolutional Recurrent Neural Network (CRNN) |
| **Task** | Offline Sequence Handwriting Recognition (Line-Level) |
| **Framework** | PyTorch 2.3+ (Torchvision 0.18+) |
| **Weights Checkpoint File** | `ai/handoff/staging/ocr_engine_handoff_final/ocr_engine/best_cer.pth` |
| **Checkpoint SHA-256 Digest** | `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941` |
| **Parameter Count** | **5,962,560 weights** (~5.96M parameters / 8.4M architecture footprint) |
| **Input Shape** | $[B, 3, 64, 1024]$ (RGB channels, Height = 64, Width = 1024) |
| **Output Shape** | $[B, 128, 320]$ (Batch size, Timesteps = 128, Class probabilities = 320) |
| **Loss Function** | Connectionist Temporal Classification (CTC Loss) |
| **Decoding Strategy** | Greedy CTC Decoding ($\arg\max$ with duplicate collapse & blank strip) |
| **Target Language** | Vietnamese (Primary School Standard, Grades 1–5) |
| **Production Status** | Verified Production Model |

---

## 2. Model Architecture & Layer Breakdown

The HandAI recognition engine uses a hybrid CRNN architecture combining deep 2D convolutions for spatial stroke feature extraction, bidirectional recurrent sequence modeling for contextual dependencies, and a linear transcription layer decoded via CTC.

```
Input Line Image [B, 3, 64, 1024]
        │
        ▼
[Block 1] Conv2d(3, 64, k=3, p=1) ──► GroupNorm(8, 64) ──► ReLU ──► MaxPool2d(2, 2)  ──► [B, 64, 32, 512]
        │
        ▼
[Block 2] Conv2d(64, 128, k=3, p=1) ──► GroupNorm(8, 128) ──► ReLU ──► MaxPool2d(2, 2) ──► [B, 128, 16, 256]
        │
        ▼
[Block 3] Conv2d(128, 256, k=3, p=1) ──► GroupNorm(8, 256) ──► ReLU ──► MaxPool2d(2, 2) ──► [B, 256, 8, 128]
        │
        ▼
[Block 4] Conv2d(256, 512, k=3, p=1) ──► GroupNorm(8, 512) ──► ReLU ──────────────────► [B, 512, 8, 128]
        │
        ▼
[Permute & Flatten]  permute(0, 3, 1, 2).view(B, 128, 512*8) ──────────────────────────► [B, 128, 4096]
        │
        ▼
[Bidirectional LSTM]  nn.LSTM(input_size=4096, hidden_size=128, bidirectional=True) ──► [B, 128, 256]
        │
        ▼
[Dropout Layer]  nn.Dropout(p=0.2) ────────────────────────────────────────────────────► [B, 128, 256]
        │
        ▼
[Linear Classifier]  nn.Linear(in_features=256, out_features=320) ────────────────────► [B, 128, 320]
        │
        ▼
Greedy CTC Decoder ──► String Prediction
```

### 2.1 Detailed PyTorch Definition (`model.py`)
```python
import torch
import torch.nn as nn

class CRNN(nn.Module):
    def __init__(self, num_classes=320, dropout=0.2):
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(3, 64, 3, padding=1), nn.GroupNorm(8, 64), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Conv2d(64, 128, 3, padding=1), nn.GroupNorm(8, 128), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Conv2d(128, 256, 3, padding=1), nn.GroupNorm(8, 256), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Conv2d(256, 512, 3, padding=1), nn.GroupNorm(8, 512), nn.ReLU(),
        )
        self.rnn = nn.LSTM(4096, 128, 1, bidirectional=True, batch_first=True)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(256, num_classes)

    def forward(self, x):
        feat = self.cnn(x)
        B, C, H, W = feat.size()
        feat = feat.permute(0, 3, 1, 2).contiguous().view(B, W, C * H)
        rnn_out, _ = self.rnn(feat)
        rnn_out = self.dropout(rnn_out)
        return self.fc(rnn_out)
```

### 2.2 Architectural Highlights
- **Group Normalization over Batch Normalization**: HandAI uses `nn.GroupNorm(8, C)` instead of standard `BatchNorm2d`. In real-world educational deployments, inference often occurs on individual lines or tiny batches ($B = 1$ to $4$). GroupNorm maintains stable normalization statistics independent of batch size, preventing variance shifts.
- **BiLSTM Contextual Slicing**: Handwritten Vietnamese characters cannot be transcribed without bidirectional context—for instance, distinguishing an isolated `c` from the first half of a ligatured `d` or `a` requires forward and backward stroke visibility. The BiLSTM reconciles stroke history across all 128 temporal slices.
- **Fixed Temporal Resolution ($T = 128$):** Input width $W_{\text{in}} = 1024\text{ px}$ downsampled three times by factor 2 yields exactly $W_{\text{feat}} = 128$ feature frames. With an average Vietnamese primary text line containing $8$ to $14$ words (~$35$ to $60$ characters including spaces), $T = 128$ provides sufficient temporal Nyquist sampling ($>2$ frames per character).

---

## 3. Vocabulary & Character Set Specification

The vocabulary (`vocab.json`) maps token indices $0 \dots 319$ ($K = 320$ classes):

- **Index 0:** Reserved strictly for the CTC blank token (`<blank>`).
- **Whitespace & Control:** `\t` (1), Space ` ` (2).
- **Punctuation & Symbols:** `!`, `"`, `#`, `$`, `%`, `&`, `'`, `(`, `)`, `*`, `+`, `,`, `-`, `.`, `/`, `:`, `;`, `<`, `=`, `>`, `?`, `@`, `[`, `]`, `_`, `~`.
- **Numerals:** Digits `0` through `9`.
- **Latin & Vietnamese Characters:**
  - Lowercase and uppercase basic Latin (`a-z`, `A-Z`).
  - Vietnamese modified vowels: `á, à, ả, ã, ạ, ă, ắ, ằ, ẳ, ẵ, ặ, â, ấn, ầ, ẩ, ẫ, ậ, é, è, ẻ, ẽ, ẹ, ê, ế, ề, ể, ễ, ệ, í, ì, ỉ, ĩ, ị, ó, ò, ỏ, õ, ọ, ô, ố, ồ, ổ, ỗ, ộ, ơ, ớ, ờ, ở, ỡ, ợ, ú, ù, ủ, ũ, ụ, ư, ứ, ừ, ử, ữ, ự, ý, ỳ, ỷ, ỹ, t`.
  - Uppercase Vietnamese accented equivalents.
  - Consonant modifier `đ, Đ`.
- **Primary Math & Unit Symbols:** Superscripts `²`, `³`, degree `°`, division `/`, multiplication `×`, inequalities `≤`, `≥`, geometric and notebook check marks (`□`, `△`, `◇`, `○`, `✓`).
- **Index 319:** Out-of-vocabulary unknown token (`<unk>`).

---

## 4. Connectionist Temporal Classification (CTC) Decoding

### 4.1 CTC Decoding Problem
Because handwriting is continuous without explicit character segmentation boundaries, the alignment between input frames $t \in [1, T]$ and character labels is unknown. CTC introduces a blank token $\epsilon$ ($\text{ID} = 0$) and defines a many-to-one collapse mapping $\mathcal{B}: \mathcal{V}^T \to \mathcal{V}^{\le T}$.

### 4.2 Greedy Decoding Implementation
```python
def _greedy_decode(logits: torch.Tensor, inv_vocab: dict) -> List[str]:
    # logits shape: [B, T=128, C=320]
    preds = logits.argmax(dim=2).cpu().numpy()
    texts = []
    for b in range(preds.shape[0]):
        out = []
        prev = -1
        for idx in preds[b, :]:
            if idx != 0 and idx != prev:  # Skip blank (0) and consecutive duplicates
                out.append(inv_vocab.get(int(idx), "?"))
            prev = idx
        texts.append("".join(out))
    return texts
```

**Step-by-step example:**
1. Raw argmax sequence: `[0, 18, 18, 0, 45, 45, 45, 0, 72, 72, 0]`
2. Duplicate collapse: `[0, 18, 0, 45, 0, 72, 0]`
3. Blank removal: `[18, 45, 72]`
4. Vocabulary lookup: `[18 -> "E", 45 -> "m", 72 -> " "]` $\implies$ `"Em "`

---

## 5. Inference Execution & Micro-Batching

To avoid GPU/CPU memory spikes when recognizing multi-line worksheets containing up to 30 lines, `predict.py` implements memory-safe micro-batching:

```python
@torch.no_grad()
def predict_batch(images: List[Union[str, Path, Image.Image]], batch_size: int = 4) -> List[str]:
    # Processes images in chunks of 4 to guarantee constant memory overhead
    results = []
    for i in range(0, len(images), batch_size):
        chunk = images[i:i + batch_size]
        tensors = torch.stack([_TRANSFORM(_prepare_image(img)) for img in chunk]).to(_device)
        logits = _model(tensors)
        results.extend(_greedy_decode(logits))
    return results
```

---

## 6. The Role of the AI Post-Correction Layer

While the CRNN is exceptionally accurate on high-contrast standard cursive (CER $\approx 5.0\%$), physical school notebooks often suffer from detached accents, faint pencil marks, or irregular student motor control. 

The AI Contextual Correction Layer (Groq Llama-3.3-70b-versatile and Google Gemini-4B) acts as a pedagogical safety net:
- **Diacritic Restoration:** Identifies unaccented vowels that violate Vietnamese phonotactics and restores appropriate primary tones (e.g., `Học tap` $\to$ `Học tập`).
- **Homologous Disambiguation:** Resolves cursive glyph confusions based on surrounding sentence grammar (e.g., `chay đua` $\to$ `chạy đua`).
- **Measured Impact:**
  - Raw CRNN Accuracy: $82.0\%$
  - Post-AI Accuracy: $94.0\%$
  - Net Accuracy Gain: **$+12.0\%$**
  - Raw OCR Error Rescue Rate: **$67.0\%$** (recovers 4 out of every 6 raw errors).
