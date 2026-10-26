# HandAI — Experiment Tracking & Machine Learning Provenance
## Dataset Versioning, Model Lineage & Reproducibility Architecture

---

## 1. Provenance Architecture Overview

HandAI enforces a strict, bi-directional machine learning provenance chain. Every line of recognized handwriting, trial evaluation score, and exported research metric is immutably anchored to its generating experiment, weights checkpoint, and dataset version.

```
+────────────────────────────────────────────────────────────────────────────────────────────────────+
|                                    HandAI ML Provenance Chain                                      |
+────────────────────────────────────────────────────────────────────────────────────────────────────+
|                                                                                                    |
|    [Dataset Version]               [Model Experiment]                                              |
|    • HandAI-v1.2 (59,747)          • CRNN-v1.2-PyTorch (5.96M params)                              |
|    • Hash & Deduplication          • Checkpoint: a807eaa7...                                       |
|            │                               │                                                       |
|            └───────────────┬───────────────┘                                                       |
|                            ▼                                                                       |
|              [Recognition Trial / Session]                                                         |
|              • sessionId: "session_1790145892"                                                     |
|              • Page SHA-256 / Device metadata                                                      |
|                            │                                                                       |
|                            ▼                                                                       |
|              [Line Result & Decision]                                                              |
|              • Line Crop SHA-256                                                                   |
|              • Raw OCR vs AI Suggestion vs Ground Truth                                            |
|                            │                                                                       |
|                            ▼                                                                       |
|              [Evaluation Result & Export]                                                          |
|              • CER: 5.0%, WER: 8.0%, Accuracy: 94.0%                                               |
|              • Immutable Research Export (JSON, CSV, MD)                                           |
|                                                                                                    |
+────────────────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 2. Core Entities & Data Contracts

### 2.1 Dataset Version Management (`DatasetVersion`)
Tracks the immutable benchmark corpus used for training and validation:

```typescript
export interface DatasetVersion {
  datasetId: string;                 // e.g. "ds_handai_v1_2"
  datasetName: string;               // "HandAI Primary Handwriting Dataset"
  version: string;                   // "v1.2"
  description: string;               // Benchmark corpus across grades 1-5
  sampleCount: number;               // 59,747 line samples
  characterCount: number;            // 421,950 characters
  imageCount: number;                // 12,450 page images
  language: string;                  // "Vietnamese"
  gradeLevel: string;                // "1-5"
  createdDate: string;               // "2026-06-20"
  annotationStatus: string;          // "Verified"
  averageImageResolution?: string;   // "1920x1080"
  annotationCoverage?: number;       // 100%
  duplicateRate?: number;            // 0.4%
  validationStatus?: string;         // "Verified"
}
```

### 2.2 Model Experiment Tracking (`ModelExperiment`)
Tracks training configurations, framework versions, parameter footprints, and baseline metrics:

```typescript
export interface ModelExperiment {
  experimentId: string;              // e.g. "exp_crnn_v1_2"
  modelVersion: string;              // "CRNN-v1.2-PyTorch"
  modelName: string;                 // "CRNN ResNet34-BiLSTM-CTC (Production)"
  datasetVersion: string;            // "HandAI-v1.2"
  trainingDate: string;              // "2026-07-05"
  framework: string;                 // "PyTorch 2.3"
  parameters: string;                // "8.4M params" (5.96M weights)
  metrics: {
    lineAccuracy: number;            // 94.0%
    characterAccuracy: number;       // 95.0%
    cer: number;                     // 5.0%
    wer: number;                     // 8.0%
    latency: number;                 // 2.3s end-to-end
  };
  status: 'ACTIVE' | 'BASELINE' | 'EXPERIMENTAL';
}
```

---

## 3. Model Evolution & Benchmarking Table

HandAI tracks iterations across training cycles, documenting measurable improvements across error rates and inference latency:

| Model Version | Dataset Version | Framework | Accuracy | CER | WER | Latency | Status |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---|
| **CRNN-v1.0-Baseline** | Dataset-v1.0 (15,420) | PyTorch 2.1 | 82.0% | 12.0% | 20.0% | 1.8s | `BASELINE` |
| **CRNN-v1.1-ResNet** | Dataset-v1.1 (34,100) | PyTorch 2.2 | 90.0% | 8.0% | 15.0% | 2.1s | `EXPERIMENTAL` |
| **CRNN-v1.2-PyTorch** ★ | Dataset-v1.2 (59,747) | PyTorch 2.3 | **94.0%** | **5.0%** | **8.0%** | **2.3s** | **`ACTIVE MODEL`** |
| **CRNN-v1.2 + Gemini-4B** ★ | Dataset-v1.2 (59,747) | Multi-Consensus | **96.4%** | **2.1%** | **4.5%** | **3.2s** | **`ACTIVE (ARBITRATED)`** |

### Historical Performance Trajectory
- **Character Error Rate Reduction:** $12.0\% \to 5.0\%$ (**$-58.3\%$ relative error reduction**).
- **Word Error Rate Reduction:** $20.0\% \to 8.0\%$ (**$-60.0\%$ relative error reduction**).
- **Net Accuracy Gain:** $82.0\% \to 94.0\%$ (**$+12.0\%$ absolute accuracy lift**).

---

## 4. Relational Database Schema (PostgreSQL)

Created via Flyway migrations `V14__add_handai_research_analytics_tables.sql` and `V15__add_handai_phase3_validation_tables.sql`:

```sql
-- 1. Dataset Version Registry
CREATE TABLE ocr_dataset_versions (
    id VARCHAR(64) PRIMARY KEY,
    dataset_name VARCHAR(128) NOT NULL,
    version_tag VARCHAR(32) NOT NULL UNIQUE,
    sample_count INT NOT NULL,
    character_count INT NOT NULL,
    grade_distribution JSONB,
    duplicate_rate NUMERIC(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Model Experiment Registry
CREATE TABLE ocr_model_experiments (
    id VARCHAR(64) PRIMARY KEY,
    model_version VARCHAR(64) NOT NULL UNIQUE,
    dataset_version_id VARCHAR(64) REFERENCES ocr_dataset_versions(id),
    checkpoint_sha256 VARCHAR(64) NOT NULL,
    parameters_count BIGINT NOT NULL,
    framework VARCHAR(64) NOT NULL,
    baseline_cer NUMERIC(5,2),
    baseline_wer NUMERIC(5,2),
    status VARCHAR(32) NOT NULL
);

-- 3. Recognition Trials with Experiment Attribution
CREATE TABLE ocr_multiline_trials (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    model_experiment_id VARCHAR(64) REFERENCES ocr_model_experiments(id),
    page_image_sha256 VARCHAR(64) NOT NULL,
    page_image_object_key VARCHAR(255) NOT NULL,
    page_width INT NOT NULL,
    page_height INT NOT NULL,
    status VARCHAR(32) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Line Results with Decision Source & Checkpoint Provenance
CREATE TABLE ocr_multiline_lines (
    id BIGSERIAL PRIMARY KEY,
    trial_id BIGINT REFERENCES ocr_multiline_trials(id),
    line_order INT NOT NULL,
    x INT NOT NULL, y INT NOT NULL, width INT NOT NULL, height INT NOT NULL,
    line_image_sha256 VARCHAR(64) NOT NULL,
    raw_ocr_text TEXT,
    corrected_text TEXT,
    predicted_text TEXT NOT NULL,
    confidence NUMERIC(5,2),
    decision_source VARCHAR(32) NOT NULL, -- 'CRNN', 'AI_CORRECTION', 'MANUAL'
    checkpoint_sha256 VARCHAR(64) NOT NULL,
    vocab_sha256 VARCHAR(64) NOT NULL,
    preprocessing_version VARCHAR(64) NOT NULL
);
```

---

## 5. Defense & Research Audit Trail

In academic defense or peer review settings, any evaluated number shown on the screen can be audited back to its physical origin:
1. From **Evaluation Report**: Read `sessionId: "session_1790145892"`.
2. In **Database**: Look up `trial_id` in `ocr_multiline_trials`.
3. Read `page_image_sha256` and fetch exact original image from MinIO.
4. Verify `checkpoint_sha256` matches `best_cer.pth` hash (`a807eaa7...`).
5. Re-run `predict_text()` on the line crop to reproduce the exact raw OCR text string deterministically.
