# MathVision Kids — Handwriting OCR Model V2 Training Data Quality Audit

**Audit Date:** September 21, 2026  
**Auditor:** AI/ML Handwriting Model Engineer  
**Phase:** `AI.HWTEXT.MODEL.V2-FINAL`  
**Status:** **INSUFFICIENT_FOR_TRAINING — CRITICAL DATA DEFICIT IDENTIFIED**  

---

## 1. Executive Summary & Headline Finding

Before undertaking any gradient optimization for Model V2, an exhaustive audit was performed on all handwriting data residing on the local filesystem.

### Primary Audit Findings:
1. **Total Absence of Training Corpus on Disk:** The 59,462 raw image crops and label archives from the upstream HuggingFace `Viet-Handwriting-OCR-v2` dataset (referenced in the V1 model manifest) **do not exist on this machine**. Only the compiled V1 model weights (`best_cer.pth`), vocabulary (`vocab.json`), and 5 isolated validation smoke samples are present.
2. **Quarantined / Parked Owner Data:** The 173-image owner dataset parked under `ai-training/parking/owner_173_untrained/` contains 331 unverified lines with **0 verified annotations** (`"verified": 0, "status": "pending"`). In accordance with `PARKING_README.md` and project governance, this data is strictly barred from active training.
3. **Severe Class Imbalance in Available Assets:** Across all 38 on-disk evaluation samples (33 regression lines + 5 dev samples), uppercase cursive $S$ appears **0 times**, $Đ$ appears **0 times**, $ô$ appears **0 times**, and the tilde tone mark ($ngã$) appears only **4 times**.
4. **Architectural Gating Outcome:** It is mathematically and scientifically impossible to resolve the known visual confusion pairs ($E/S/T/C$, $r/l/h$, diacritics) by training on the current repository contents. Attempting to fine-tune on the 38 lines would cause catastrophic memorization and invalidate the regression suite.
5. **Formal Gate Verdict:** **`BLOCKED: MISSING_TRAINING_DATASET`**.

---

## 2. Inventory of Available Handwriting Assets

| Asset Category | On-Disk Location | Total Lines / Crops | Physical Lines | Synthetic Lines | Unique Pages | Unique Texts | Ground Truth Status | Governance Role |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Historical Upstream Training Set** | `D:\nhom6\...` *(missing)* | 0 | 0 | 0 | 0 | 0 | Missing from machine | `TRAIN` (Unavailable) |
| **Validation Smoke Samples** | `ai-training/handoff/staging/.../samples/` | 5 | 5 | 0 | 5 | 5 | Verified (Upstream) | `DEV` |
| **Locked Regression Benchmark** | `services/ai-service/tests/fixtures/ocr_eval/` | 33 | 25 | 8 | 6 | 12 | 100% Verified (Locked) | `REGRESSION_33` |
| **Parked Owner Dataset** | `ai-training/parking/owner_173_untrained/` | 331 | 331 | 0 | 173 | Unverified | 0 verified / 331 pending | `PARKED_UNTRAINED` |
| **Total Active On-Disk Available** | — | **38** | **30** | **8** | **11** | **17** | **38 Verified** | — |

---

## 3. Character & Linguistic Distribution Audit (38 Active Lines)

Total characters audited: **745** (including 146 spaces and 16 punctuation marks).

### 3.1 Target Uppercase Cursive Confusions ($E / S / T / C$)
| Character | Count in Active Dataset | % of Total Chars | Assessment / Risk |
|:---:|:---:|:---:|---|
| **`E`** | **7** | 0.94% | Underrepresented. Appears only in `"Em yêu mùa hè"` and `"Em hái sim ăn"`. |
| **`S`** | **0** | **0.00%** | **CRITICAL DEFICIT**. Completely absent from the entire on-disk dataset. The model cannot learn to discriminate cursive $E$ vs $S$. |
| **`T`** | **11** | 1.48% | Moderately represented, but restricted to 4 specific poem phrases. |
| **`C`** | **5** | 0.67% | Underrepresented. Appears only in `"Có hoa sim tím"`. |

### 3.2 Target Cursive Ligature Characters ($r / l / h$)
| Character | Count in Active Dataset | % of Total Chars | Assessment / Risk |
|:---:|:---:|:---:|---|
| **`r`** | **26** | 3.49% | Concentrated in `trên`, `trâu`, `rinh`, `ra rả`. Absent in mid-word vowel-r ligatures. |
| **`l`** | **8** | 1.07% | Severely underrepresented. Appears in `lượn`, `lưng`. |
| **`h`** | **42** | 5.64% | Sufficient raw count, but predominantly present as consonant digraph `nh`, `th`, `ch`. |

### 3.3 Vietnamese Special Base Characters
| Character | Count | Assessment |
|:---:|:---:|---|
| **`ă`** | 3 | Underrepresented |
| **`â`** | 6 | Minimal |
| **`ê`** | 16 | Adequate (present in `hè`, `quê`, `thế`) |
| **`ô`** | **0** | **CRITICAL DEFICIT** (Zero base instances) |
| **`ơ`** | 1 | Severely underrepresented |
| **`ư`** | 13 | Moderate |
| **`đ`** | 8 | Moderate |
| **`Đ`** | **0** | **CRITICAL DEFICIT** (Zero uppercase instances) |

### 3.4 Vietnamese Diacritic (Tone Mark) Decomposition
Decomposed via Unicode NFD analysis:
| Tone Mark | Name | Instances Found | Relative Frequency |
|---|---|:---:|:---:|
| `\u0301` | Dấu sắc (acute) | **41** | 39.8% |
| `\u0300` | Dấu huyền (grave) | **30** | 29.1% |
| `\u0309` | Dấu hỏi (hook above) | **12** | 11.7% |
| `\u0323` | Dấu nặng (dot below) | **16** | 15.5% |
| `\u0303` | Dấu ngã (tilde) | **4** | **3.9% (Severely deficient)** |

### 3.5 Whitespace & Punctuation
- **Inter-word Spaces (`" "`):** 146 instances (Average 3.8 words per line).
- **Punctuation Marks:**
  - Full stop (`.`): 7
  - Comma (`,`): 3
  - Exclamation mark (`!`): 3
  - Colon (`:`): 2
  - Hyphen (`-`): 1
  - Question mark (`?`): **0** (Absent)
  - Semicolon (`;`): **0** (Absent)

---

## 4. Root-Cause Deficit Analysis

The current on-disk dataset was designed strictly as a **frozen evaluation fixture**, not a training dataset:
1. **Phrastic Redundancy:** Out of 33 regression lines, 17 lines are duplicates or near-duplicates of the 8-line poem by the Owner ("Em yêu mùa hè...").
2. **Zero Vocabulary Coverage on Key Phonotactics:** Crucial Vietnamese elementary handwriting clusters (such as initial $Gi$, $Qu$, $Kh$, $Gh$, $Ng$, $Ngh$ and uppercase initials $A, B, D, Đ, G, H, K, L, M, N, P, Q, R, S, U, V, X, Y$) are either entirely missing or present in single instances.
3. **Missing Negative Pairs:** Disambiguation between $Có$ vs $Tó$ vs $Bó$ requires hundreds of hard-negative cursive strokes written by multiple distinct child hands.

---

## 5. Mandatory Dataset Requirements for Model V2 Readiness

Before Model V2 training can be initiated, the AI/ML data engineering team must ingest and certify the following minimal dataset package:

1. **Volume Contract:**
   - Minimum **10,000 verified line crops** for `TRAIN`.
   - Minimum **1,000 verified line crops** for `DEV`.
   - Minimum **500 verified line crops** for `INDEPENDENT_HOLDOUT_V2`.
2. **Writer Disjointness:**
   - Minimum **15 distinct child writers** spanning Grades 1 to 5.
   - Zero writer overlap between `TRAIN`, `DEV`, and `INDEPENDENT_HOLDOUT`.
3. **Phonotactic & Diacritic Balance:**
   - Minimum **200 instances** of each uppercase cursive letter ($E, S, T, C, A, B, D, Đ, G, H, K, L, M, N, O, P, Q, R, U, V, X, Y$).
   - Balanced distribution of all 5 Vietnamese tone marks (each $\ge 15\%$ of total diacritics).
   - Minimum **500 continuous cursive ligature samples** covering $tr$, $th$, $ch$, $nh$, $ng$, $gh$, $kh$, $ph$.
4. **Physical Capture Diversity:**
   - Lined paper (ô ly tiểu học), standard ruled notebook paper, and unruled plain paper.
   - Blue ballpoint, blue ink fountain pen, black pencil, and gel pen.
   - Varying lighting (300 lux to 1200 lux) and camera angles ($\pm 15^\circ$).
