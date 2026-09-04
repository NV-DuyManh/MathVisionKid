# MathVision AI Internal Contract

## Overview
This document defines the strict internal contract between the Spring Boot Business Backend and the FastAPI AI Service.

## Internal Analysis Endpoint

### `POST /internal/v1/analyze-submission`

#### Request Payload
```json
{
  "submissionId": "sub_12345",
  "imageReference": "s3://mathvision-raw/images/sub_12345.jpg",
  "allowedOperations": ["VERTICAL_ADDITION", "VERTICAL_SUBTRACTION"],
  "maxDigits": 3,
  "oneExerciseOnly": true,
  "policyVersion": "v1.2"
}
```
*Note: `imageReference` is used for internal storage retrieval. FastAPI should not use public URLs.*

#### Expected Responses
FastAPI must return one of the following statuses for internal routing:
- `FEEDBACK_READY` (AI successfully parsed and graded)
- `NEEDS_CONFIRMATION` (Ambiguous tokens, student needs to confirm)
- `NEEDS_RETAKE` (Image is illegible or severely blurry)
- `OUT_OF_SCOPE` (Image does not contain a math exercise or contains forbidden content)
- `REVIEW_REQUIRED` (System error, rule conflict, or low confidence)

FastAPI **cannot** create an official final grade (`isOfficial: false`). Only the teacher can approve.

#### Example Response (FEEDBACK_READY)
```json
{
  "status": "FEEDBACK_READY",
  "gradeProposal": {
    "suggestedScore": 8,
    "maxScore": 10,
    "confidence": 0.95,
    "isOfficial": false
  }
}
```
