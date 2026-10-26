# HandAI — Analytics & Big Data Architecture
## Metrics, Evaluation Formulations & Longitudinal Aggregation

---

## 1. Analytics Architecture Overview

The HandAI Analytics and Big Data engine provides a three-tiered evaluation hierarchy designed to serve immediate student feedback, longitudinal pedagogical research, and large-scale model benchmarking.

```
+----------------------------------------------------------------------------------------------------+
|                                  HandAI Analytics Hierarchy                                        |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [Tier 1: Trial Analytics] ────────► Single-document real-time feedback (8-metric quality card)    |
|            │                                                                                       |
|            ▼                                                                                       |
|  [Tier 2: Global Analytics] ───────► Multi-session longitudinal aggregation & trend tracking       |
|            │                                                                                       |
|            ▼                                                                                       |
|  [Tier 3: Research Big Data] ──────► Multi-model ablation benchmark & calibration reliability     |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Core Mathematical Formulations & Algorithms

### 2.1 Character Error Rate (CER)
Character Error Rate measures the edit distance at the character level required to transform predicted string $p$ into ground truth string $t$, normalized by the character length of the ground truth:

$$\text{CER (\%)} = \frac{\text{Levenshtein}(p, t)}{\max(1, |t|)} \times 100 = \frac{I_c + D_c + S_c}{N_{\text{chars}}} \times 100$$

Where:
- $I_c$: Character insertions
- $D_c$: Character deletions
- $S_c$: Character substitutions
- $N_{\text{chars}} = |t|$: Total characters in reference string

**Character Accuracy:**
$$\text{Character Accuracy (\%)} = \max(0, 100 - \text{CER})$$

---

### 2.2 Word Error Rate (WER)
Word Error Rate evaluates complete word token correctness, penalizing any error within a word regardless of whether it was a single accent or an entire syllable:

$$\text{WER (\%)} = \frac{\text{WordEditDistance}(p_{\text{words}}, t_{\text{words}})}{\max(1, |t_{\text{words}}|)} \times 100 = \frac{I_w + D_w + S_w}{N_{\text{words}}} \times 100$$

Where:
- Words are extracted via whitespace tokenization: $t_{\text{words}} = \text{split}(t, \text{" "})$
- $I_w, D_w, S_w$: Word-level insertions, deletions, and substitutions
- $N_{\text{words}} = |t_{\text{words}}|$: Total word count in reference

**Word Accuracy:**
$$\text{Word Accuracy (\%)} = \max(0, 100 - \text{WER})$$

---

### 2.3 Line Accuracy (Exact Match)
Line Accuracy evaluates perfect whole-line sequence matches:

$$\text{Line Accuracy (\%)} = \frac{1}{M} \sum_{i=1}^M \mathbb{I}(p_i = t_i) \times 100$$

Where $\mathbb{I}(\cdot)$ is the indicator function ($1$ if strings match exactly, $0$ otherwise), and $M$ is the number of evaluated lines.

---

### 2.4 Zero-Division & Edge Case Safeguards
To ensure computational stability across sparse lines, edge cases are defined as:
- **Both $p$ and $t$ are empty:** $\text{CER} = 0\%$, $\text{WER} = 0\%$, $\text{Accuracy} = 100\%$.
- **Reference $t$ empty, prediction $p$ non-empty:** $\text{CER} = 100\%$, $\text{WER} = 100\%$, $\text{Accuracy} = 0\%$.
- **Prediction $p$ empty, reference $t$ non-empty:** $\text{CER} = 100\%$, $\text{WER} = 100\%$, $\text{Accuracy} = 0\%$.
- **Global / Trial Normalization:** The denominator is strictly constrained by $\max\left(1, \sum |t_i|\right)$ to guarantee finite numerical results.

---

## 3. Tier 1: Trial Analytics (Per-Document Real-Time Feedback)

Implemented in `apps/student-mobile/src/app/handai-trial-analytics.tsx`:
- **Scope:** Evaluates a single notebook page scan immediately upon confirmation.
- **8-Metric Recognition Quality Report Grid:**
  1. **Line Accuracy:** Percentage of lines with zero errors ($100 \times \text{correct}/\text{total}$).
  2. **Character Accuracy:** Average character correctness ($100 - \text{CER}$).
  3. **CER (Error Rate):** Overall character error percentage.
  4. **Word Accuracy:** Average whole-word correctness ($100 - \text{WER}$).
  5. **WER (Word Error Rate):** Overall word error percentage.
  6. **Raw OCR Accuracy:** Baseline CRNN exact match rate before AI post-correction.
  7. **Final AI Accuracy:** Verified accuracy following LLM arbitration.
  8. **AI Gain:** Marginal lift contributed by AI: $\max(0, \text{FinalAcc} - \text{RawAcc})$.
- **Line-Level Feedback Cards:** Each detected line displays model output, ground truth, individual CER/WER pills, error taxonomy tags, and severity badges.

---

## 4. Tier 2: Global Analytics (Longitudinal Aggregation)

Implemented in `apps/student-mobile/src/app/handai-analytics.tsx`:
- **Scope:** Aggregates metrics across all completed evaluation sessions stored in local persistent state.
- **Aggregation Logic (Micro-Averaging over Macro-Averaging):**
  Rather than averaging session percentages (which biases towards short sessions), global CER and WER are computed via global micro-averaging across all evaluated tokens:

  $$\text{Global CER} = \frac{\sum_{s \in \text{Sessions}} \sum_{i \in \text{Lines}} D_{\text{char}}(p_{s,i}, t_{s,i})}{\max\left(1, \sum_{s \in \text{Sessions}} \sum_{i \in \text{Lines}} |t_{s,i}|\right)} \times 100$$

  $$\text{Global WER} = \frac{\sum_{s \in \text{Sessions}} \sum_{i \in \text{Lines}} D_{\text{word}}(p_{s,i}, t_{s,i})}{\max\left(1, \sum_{s \in \text{Sessions}} \sum_{i \in \text{Lines}} |t_{s,i, \text{words}}|\right)} \times 100$$

- **Longitudinal Trend Visualizations:**
  - **CER Progression Chart:** Historical CER trajectory across completed sessions.
  - **WER Trend Chart:** Progression from Session 1 (20.0%) $\to$ Session 2 (15.0%) $\to$ Session 3 (8.0%).
  - **Error Distribution Breakdown:** Relative frequencies of error categories.

---

## 5. Tier 3: Research Big Data & Ablation Benchmark Layer

Stored in PostgreSQL tables created by Flyway migrations `V14` and `V15`:

### 5.1 AI Impact & Contribution Analysis (`ocr_ai_impact_metrics`)
Quantifies the exact contribution of the contextual AI correction layer over the raw acoustic/visual CRNN baseline:
- **Baseline CRNN Raw Accuracy:** $82.0\%$
- **AI-Assisted Final Accuracy:** $94.0\%$
- **Net Accuracy Gain:** **$+12.0\%$**
- **AI Rescue Rate:**
  $$\text{Rescue Rate} = \frac{\text{OCR Errors Rescued by AI}}{\text{Total Raw OCR Errors}} \times 100 = \frac{4}{6} \times 100 = \mathbf{67.0\%}$$
  *Where a rescued error is defined as a line where raw CRNN was erroneous, arbitration selected AI correction, and the final text matches educator ground truth.*

### 5.2 Confidence Calibration Reliability (`ocr_confidence_calibrations`)
Evaluates whether model certainty scores correlate monotonically with ground truth accuracy across 5 confidence intervals:

| Confidence Range | Validated Samples | Correct Samples | Empirical Accuracy | Calibration State |
|---|:---:|:---:|:---:|---|
| **90–100%** | 500 | 490 | **98.0%** | High Precision (Automated grading safe) |
| **80–89%** | 320 | 291 | **91.0%** | Well Calibrated |
| **70–79%** | 180 | 137 | **76.0%** | Moderate Reliability |
| **60–69%** | 95 | 61 | **64.0%** | Review Recommended |
| **< 60%** | 45 | 21 | **47.0%** | Manual Verification Required |

*Finding:* Strict monotonic calibration validates that model confidence reflects true probability of correctness, satisfying Expected Calibration Error (ECE) standards.

---

## 6. Big Data Export Schemas

HandAI exports evaluation data in three standard formats for academic reporting:

### 6.1 JSON Structured Export (`exportTrialToJson`)
```json
{
  "sessionId": "session_1790156000",
  "datasetVersion": "HandAI-v1.2",
  "modelVersion": "CRNN-v1.2-PyTorch",
  "experimentId": "exp_crnn_v1_2",
  "metrics": {
    "lineAccuracy": 94.0,
    "characterAccuracy": 95.0,
    "cer": 5.0,
    "wordAccuracy": 92.0,
    "wer": 8.0,
    "rawAccuracy": 82.0,
    "finalAccuracy": 94.0,
    "accuracyGain": 12.0,
    "rescueRate": 67.0
  },
  "lines": [
    {
      "lineIndex": 1,
      "modelOutput": "Em yêu mùa hè",
      "groundTruth": "Em yêu mùa hè",
      "cer": 0,
      "wer": 0,
      "isCorrect": true,
      "errorType": "NO_ERROR"
    }
  ]
}
```

### 6.2 CSV Data Export (`exportTrialToCsv`)
Includes standardized tabular headers:
```csv
Line Index,Model Output (OCR),AI Suggestion,Final Text,Confidence,Source,Correction Type,Is Correct,Ground Truth,Evaluation Status,CER (%),Character Accuracy (%),WER (%),Word Accuracy (%),Error Type,Severity,Wrong Character,Correct Character,Dataset Version,Model Version,Experiment ID,Training Date,Session ID
```
