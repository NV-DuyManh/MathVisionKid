# AI Training Workspace

This directory (`ai-training/`) is the dedicated workspace for the MathVision Kids AI/ML team member to perform:
- DATASET PREPARATION
- ANNOTATION
- TRAINING
- EXPERIMENTATION
- MODEL EXPORT

This is NOT the production FastAPI service. (The production inference service will live separately at `services/ai-service/`).

## Intended Flow
```
ai-training/
    ↓
trained/exported model
    ↓
handoff manifest
    ↓
services/ai-service/
    ↓
FastAPI inference
    ↓
Spring Boot Business API
```

## Quick Start for AI/ML Teammate
1. Put local raw/de-identified data in approved local data folders (`data/raw-local/`, `data/deidentified-local/`).
2. Do not commit raw child images.
3. Follow annotation schema.
4. Save primary/secondary/adjudicated labels separately.
5. Freeze train/validation/test manifests.
6. Save training configs.
7. Save experiment metrics.
8. Export final model.
9. Complete model card.
10. Complete dataset card.
11. Complete `AI_HANDOFF_CHECKLIST.md`.
12. Tell integration owner when model handoff is ready.
