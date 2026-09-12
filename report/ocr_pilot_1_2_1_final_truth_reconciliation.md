# OCR.PILOT.1.2.1 — Final Post-Test DB Truth Reconciliation & Refreeze Report

**Date:** 2026-09-12  
**Task ID:** OCR.PILOT.1.2.1  
**Branch:** `main`  
**Repository Working Copy:** `E:\MathVisionKid`  
**Status:** COMPLETED (Gate Passed — Ready for Owner Physical OCR Testing)

---

## 1. Executive Summary

Milestone **OCR.PILOT.1.2.1** provides the final post-test state audit and historical process reconciliation for the Vietnamese Handwriting Recognition Pilot mode:
1. **Repository & Process Provenance:** Audited commit `712f806`. Classified as `HISTORICAL_PROCESS_VIOLATION = YES` due to the absence of explicit owner permission at the time of commit creation during `OCR.PILOT.1`. Confirmed that `OCR.PILOT.1.1`, `OCR.PILOT.1.2`, and `OCR.PILOT.1.2.1` created **0** git commits.
2. **Authoritative PostgreSQL State:** Current live database contains exactly **13 rows** in `ocr_trials`. The verdict breakdown sum strictly equals 13 ($4 \text{ CORRECT} + 5 \text{ CORRECTED} + 1 \text{ SKIPPED} + 3 \text{ UNVERIFIED} = 13$). All 13 rows are developer/test rows (`is_test_data = true`, `training_eligible = false`, `privacy_confirmed = false`). Real owner OCR rows = **0**.
3. **Live Trial `b1cc39f9` Reconciliation:** Confirmed that temporary trial `b1cc39f9-611b-40a4-bbed-cfb3bfeeddd4` (created during 1.2 integration testing) is `NOT_PRESENT` in the final database state due to explicit post-test cleanup (`DELETE FROM ocr_trials WHERE trial_id = 'b1cc39f9-611b-40a4-bbed-cfb3bfeeddd4'`). During its lifetime, it maintained fail-closed quarantine (`is_test_data = true`, `privacy_confirmed = false`, `training_eligible = false`).
4. **Legacy Arithmetic Test Metadata Debt:** Formally documented that legacy test rows containing arithmetic text strings (e.g. `12 + 34 = 46`) carry `domain = HANDWRITING_TEXT`. Because they are strictly flagged with `is_test_data = true` and `training_eligible = false`, they are quarantined and excluded from export, representing metadata debt rather than a training blocker.
5. **Clean Export & Safe Metrics:** Executed `export_ocr_feedback_dataset.py` to a fresh output directory, yielding **0** candidate trials and **0** exported samples. Live metrics endpoint returns safe `null` for exact match and CER, and `"N/A"` for percentages.
6. **Model Quality & Status:** CRNN and Vocab SHA-256 hashes are bit-for-bit verified. Model quality is honestly classified as `POOR / NOT YET ACCEPTED`, and the owner goal "read handwriting correctly" is `NOT_YET_ACHIEVED`. The pipeline and feedback loop are `READY_FOR_OWNER_TEST`.

---

## 2. Git History / Process Provenance

The repository status and commit log were audited directly from the filesystem:

- **Top-level directory:** `E:/MathVisionKid`
- **Current branch:** `main`
- **Head commit:** `712f806d898451ca619308e924d261dec5f76c13`
- **Recent Git Log:**
  ```text
  712f806 feat(ocr-pilot): complete handwriting test mode, feedback loop, and mobile image pipeline
  dc9a9de feat(ocr): integrate OCR bridge, arithmetic line dataset handoff, and test cleanup
  f89c43f feat: complete OCR artifact provenance reconciliation and refreeze (INT.1.1, INT.1.1.1, INT.1.1.2)
  b87a028 feat: complete Teacher UI refreeze, backend closure and handwritten OCR staging (UI.2, UI.2.2, INT.1)
  26625a1 feat(student-ui): complete UI refreeze, visual QA, contrast audit and scope compliance
  ```
- **Commit Count Verification by Phase:**
  - `OCR.PILOT.1.1`: **0** commits
  - `OCR.PILOT.1.2`: **0** commits
  - `OCR.PILOT.1.2.1`: **0** commits

---

## 3. Historical Commit Violation

### Audit of Commit `712f806`
- **Message:** `feat(ocr-pilot): complete handwriting test mode, feedback loop, and mobile image pipeline`
- **Author Date:** `Fri Sep 11 22:31:57 2026 +0700`
- **Origin:** Created during the conclusion of task `OCR.PILOT.1`.
- **Authorization Audit:** While the user submitted chat requests regarding warnings and git, project permanent rules strictly mandated: *NO commit/push unless owner explicitly allowed it*. In prior task review, no formal explicit authorization for a permanent git commit was recorded.
- **Classification:**
  ```text
  HISTORICAL_PROCESS_VIOLATION = YES
  Violation Commit = 712f806
  ```
- **Remediation Policy:** No rollback or git history rewrite was performed. This is documented strictly as process provenance.

---

## 4. Final PostgreSQL Row Count

Executed against active PostgreSQL container (`mathvision-postgres`):

```sql
SELECT count(*) FROM ocr_trials;

SELECT
  count(*) FILTER (WHERE is_test_data = true) AS test_rows,
  count(*) FILTER (WHERE is_test_data = false) AS real_rows,
  count(*) FILTER (WHERE privacy_confirmed = true) AS privacy_true,
  count(*) FILTER (WHERE privacy_confirmed = false) AS privacy_false,
  count(*) FILTER (WHERE training_eligible = true) AS eligible_rows
FROM ocr_trials;
```

**Output:**
```text
 count 
-------
    13
(1 row)

 test_rows | real_rows | privacy_true | privacy_false | eligible_rows 
-----------+-----------+--------------+---------------+---------------
        13 |         0 |            0 |            13 |             0
(1 row)
```

- **Final Live OCR Trial Rows:** 13
- **Developer/Test Rows:** 13
- **Real Owner Rows:** 0
- **Training Eligible Rows:** 0
- **Privacy True Rows:** 0
- **Privacy False Rows:** 13

---

## 5. Final Verdict Breakdown

```sql
SELECT verdict, count(*)
FROM ocr_trials
GROUP BY verdict
ORDER BY verdict;
```

**Output:**
```text
  verdict   | count 
------------+-------
 CORRECT    |     4
 CORRECTED  |     5
 SKIPPED    |     1
 UNVERIFIED |     3
(4 rows)
```

### Invariant Proof
$$\text{CORRECT}(4) + \text{CORRECTED}(5) + \text{SKIPPED}(1) + \text{UNVERIFIED}(3) = 13$$
$$\text{Verdict Sum Check} = \mathbf{PASS}$$

---

## 6. Live b1cc Trial Reconciliation

During `OCR.PILOT.1.2`, a live integration test executed `scratch/test_live_closure.py` which created temporary trial `b1cc39f9-611b-40a4-bbed-cfb3bfeeddd4` to verify end-to-end communication from Spring Boot to FastAPI using `X-Internal-API-Key`.

### Database Status:
```sql
SELECT trial_id, verdict, is_test_data, privacy_confirmed, training_eligible, domain, data_origin, predicted_text 
FROM ocr_trials 
WHERE trial_id = 'b1cc39f9-611b-40a4-bbed-cfb3bfeeddd4';
```
```text
(0 rows)
```

- **State:** `NOT_PRESENT`
- **Reconciliation Cause:** Explicit post-test cleanup executed during the closure phase (`DELETE FROM ocr_trials WHERE trial_id = 'b1cc39f9-611b-40a4-bbed-cfb3bfeeddd4'`).
- **Quarantine Invariant During Existence:** Live test logs prove that while present, the trial was created with `is_test_data = true`, `privacy_confirmed = false`, and `training_eligible = false`. Feedback submission (`CORRECT`) confirmed `training_eligible` remained `false`.
- **Safe Quarantine Classification:** `PASS`

---

## 7. Test-Row Quarantine State

Full audit of all 13 existing records in PostgreSQL:

| Trial ID | Verdict | Domain | is_test_data | privacy_confirmed | training_eligible | Predicted Text | Verified Text Raw |
|---|---|---|---|---|---|---|---|
| `4a4a497b-f1df-474c-ac9c-cadd220d2c71` | UNVERIFIED | HANDWRITING_TEXT | `true` | `false` | `false` | `nsa-ao` | [NULL] |
| `af7225b2-e149-4b74-bf48-d9c1ef22c106` | CORRECT | HANDWRITING_TEXT | `true` | `false` | `false` | `nsa-ao` | `nsa-ao` |
| `e34ec39f-cc01-4772-8eb1-9fc0021504fe` | UNVERIFIED | HANDWRITING_TEXT | `true` | `false` | `false` | `nsa-ao` | [NULL] |
| `be96abc5-ce2c-4ce3-bff7-bc55b8c6bdaa` | CORRECT | HANDWRITING_TEXT | `true` | `false` | `false` | `nsa-ao` | `nsa-ao` |
| `5a908c6a-8f60-4f5e-b354-ece86de763e3` | UNVERIFIED | HANDWRITING_TEXT | `true` | `false` | `false` | `nsa-ao` | [NULL] |
| `84cde238-e547-422e-b99c-8e73ef5d9372` | CORRECT | HANDWRITING_TEXT | `true` | `false` | `false` | `nsa-ao` | `nsa-ao` |
| `bb4848bb-5e30-4580-b3ae-c91686b5d1da` | CORRECTED | HANDWRITING_TEXT | `true` | `false` | `false` | `nsa-ao` | `12 + 34 = 46` |
| `6d908058-eb25-4d97-837e-dd304bd0a331` | CORRECT | HANDWRITING_TEXT | `true` | `false` | `false` | `nsa-ao` | `nsa-ao` |
| `e9ac32ac-e82e-4f74-ae9b-cc6f0ab3427c` | CORRECTED | HANDWRITING_TEXT | `true` | `false` | `false` | `nsa-ao` | `12 + 34 = 46` |
| `0cb0dba1-8ffc-40a6-b616-f5a164b9ad55` | CORRECTED | HANDWRITING_TEXT | `true` | `false` | `false` | `nrer` | `  hôm nay trời nắng  ` |
| `6c1bf2ed-6e4b-4947-81fb-5edbf60b8b93` | CORRECTED | HANDWRITING_TEXT | `true` | `false` | `false` | `nrer` | `  hôm nay trời nắng  ` |
| `b23779eb-2d6a-4813-b481-de7bbbad78ef` | CORRECTED | HANDWRITING_TEXT | `true` | `false` | `false` | `Earsem` | `Em yêu trường em` |
| `ecbe3845-6d15-4504-82e4-72fbed4e6678` | SKIPPED | HANDWRITING_TEXT | `true` | `false` | `false` | `Tro` | [NULL] |

**Quarantine Invariants Verified:**
- 100% of rows have `is_test_data = true`
- 100% of rows have `privacy_confirmed = false`
- 100% of rows have `training_eligible = false`

---

## 8. Legacy Arithmetic Test Metadata Debt

- **Audit Findings:** Rows `bb4848bb-5e30-4580-b3ae-c91686b5d1da` and `e9ac32ac-e82e-4f74-ae9b-cc6f0ab3427c` contain arithmetic string `12 + 34 = 46` as `verified_text_raw` while tagged with `domain = HANDWRITING_TEXT`.
- **Root Cause:** During initial developer testing in `OCR.PILOT.1`, sample math lines were tested before arithmetic domain isolation was established.
- **Impact Analysis:** Because both rows are quarantined (`is_test_data = true`, `privacy_confirmed = false`, `training_eligible = false`), they are automatically rejected by `export_ocr_feedback_dataset.py` and cannot leak into model training.
- **Classification:** `LEGACY_TEST_DOMAIN_METADATA_DEBT = PRESENT`.
- **Policy:** Preserved as-is without schema changes to maintain pristine historical test logs.

---

## 9. Final Default Export Result

Executed against the final database state using `services/ai-service/.venv`:

```powershell
& "E:\MathVisionKid\services\ai-service\.venv\Scripts\python.exe" scripts/export_ocr_feedback_dataset.py --out-dir scratch/export_1_2_1_reconcile
```

**Output:**
```text
[EXPORT] Evaluating 0 candidate verified OCR trials...
[EXPORT] Qualified 0 trustworthy handwriting samples.
[EXPORT] Successfully generated dataset package: E:\MathVisionKid\scratch\export_1_2_1_reconcile\ocr_feedback_export_20260912_094831.zip
[EXPORT] Export directory: E:\MathVisionKid\scratch\export_1_2_1_reconcile\ocr_feedback_export_20260912_094831
```

- **Candidate Rows Evaluated:** 0
- **Qualified Samples Exported:** 0
- **Integrity Status:** **PASS**

---

## 10. Metrics Current-State Verification

Live call to Student Metrics API (`GET /api/v1/ocr/trials/metrics`):

```json
{
  "totalTrials": 0,
  "verifiedTrials": 0,
  "correctCount": 0,
  "correctedCount": 0,
  "skippedCount": 0,
  "unverifiedCount": 0,
  "exactMatchRate": null,
  "exactMatchPercentage": "N/A",
  "characterErrorRate": null,
  "cerPercentage": "N/A",
  "domain": "HANDWRITING_TEXT",
  "evaluationScope": "User-verified pilot handwriting samples (excluding test/synthetic/skipped)"
}
```

- **Verified Real Trials:** 0
- **Exact Match Rate:** `null`
- **Exact Match Percentage:** `"N/A"`
- **Character Error Rate:** `null`
- **CER Percentage:** `"N/A"`
- **Zero-Denominator Safety:** **PASS**

---

## 11. Security Regression Check

Reconfirmed against running local daemons:

| Security Assertion | Test Action | Expected Result | Actual Result |
|---|---|---|---|
| FastAPI Internal OCR Auth (Missing Key) | `POST /internal/v1/ocr/recognize-line` without key | `401 Unauthorized` | `401` (**PASS**) |
| FastAPI Internal OCR Auth (Bad Key) | `POST /internal/v1/ocr/recognize-line` with bad key | `401 Unauthorized` | `401` (**PASS**) |
| Stream-Only Media Type Enforcement | `POST /internal/v1/ocr/recognize-line` with JSON body | `415 Unsupported Media Type` | `415` (**PASS**) |
| Internal OCR Success | `POST /internal/v1/ocr/recognize-line` with valid key + raw bytes | `200 OK` | `200` (**PASS**) |
| Spring Boot OCR Student RBAC | `GET /api/v1/ocr/trials/metrics` as Teacher | `403 Forbidden` | `403` (**PASS**) |
| Spring Boot OCR Unauthenticated | `GET /api/v1/ocr/trials/metrics` without token | `401 Unauthorized` | `401` (**PASS**) |

---

## 12. Model SHA/Vocab SHA

PowerShell `Get-FileHash -Algorithm SHA256` results:

- **CRNN Checkpoint (`best_cer.pth`):**
  `A807EAA763A4471BC057B9545A3521612423214858D50B1EF42B7BAF28DE0941` (**PASS**)
- **OCR Vocab (`vocab.json`):**
  `6AF4062E92E22CC91ECE5198638E29A6CEEC6CB92E3B12BD71DEB4B874AC9E0D` (**PASS**)
- **Training Commands Executed:** 0
- **New Checkpoint Generated:** NONE

---

## 13. Current OCR Accuracy Truth

Honest classification of model quality:
- **Pipeline Status:** `READY_FOR_OWNER_TEST`
- **Feedback Collection Loop:** `READY_FOR_OWNER_TEST`
- **Current Handwriting Accuracy:** `POOR / NOT YET ACCEPTED`
- **Owner Goal "read the handwriting correctly":** `NOT_YET_ACHIEVED`

*Note:* Known developer evidence records severe misrecognitions (e.g. *"hôm nay trời nắng"* $\to$ `nrer`, *"Em yêu trường em"* $\to$ `Earsem`). The system is architected so the owner can collect real corrections to drive offline model retraining.

---

## 14. Physical Owner Test Status

- **Status:** **`OWNER_TEST_REQUIRED`**
- All pre-requisite audits, security checks, and database protections are completed.
- The laptop backend is running and ready to receive real requests from the owner's physical Android phone.

---

## 15. Final Refreeze Verdict

The database state, security rules, and dataset export mechanisms are completely reconciled, verified, and frozen.

```text
============================================================
FINAL GATE VERDICT: OCR.PILOT.1.2.1 — PASSED
============================================================
- Repository Status: Clean audit, no new commits
- Total Database Rows: 13 (all quarantined test data)
- Real Owner Rows: 0
- Training Eligible Rows: 0
- Default Export Rows: 0
- Security Invariants: All 6 checks passed
- Model Checkpoints: Bit-for-bit identical
- Physical OCR Test: OWNER_TEST_REQUIRED
============================================================
```
