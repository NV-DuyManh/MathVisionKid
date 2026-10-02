# HandAI System Architecture

## 1. High-Level Architecture
HandAI is built on a streamlined, mobile-first architecture utilizing native processing and cloud intelligence to provide robust, academically sound handwriting evaluation.

```mermaid
graph TD
    A[Mobile Application] --> B[Backend API]
    B --> C[OCR Processing Layer]
    C --> D[CRNN Recognition Engine]
    D --> E[AI Correction Layer]
    E --> F[Evaluation Analytics]
    F --> G[Research Dashboard]
```

## 2. Detailed AI Pipeline
The core evaluation pipeline follows a strict, sequential process ensuring that raw model performance and AI enhancements are independently measurable:

```mermaid
graph TD
    A1[Image Input] --> B1[Image Normalization]
    B1 --> C1[Line Detection]
    C1 --> D1[CRNN Recognition]
    D1 --> E1[AI Correction Arbitration]
    E1 --> F1[Ground Truth Evaluation]
    F1 --> G1[Metrics Calculation]
    G1 --> H1[Error Analysis]
```

## 3. Data Flow and Provenance
To ensure academic integrity, every evaluation adheres to a rigid data provenance chain:

```mermaid
graph TD
    I1[Dataset Version] --> J1[Model Experiment]
    J1 --> K1[Recognition Trial]
    K1 --> L1[Line Result]
    L1 --> M1[Metrics]
    M1 --> N1[Report Export]
```
- **Dataset Version**: Fixed splits, bounding boxes, and image augmentations.
- **Model Experiment**: Tracks specific weights, framework (PyTorch), and hyperparameters.
- **Recognition Trial**: Immutable session capturing image quality and latency.
- **Metrics & Export**: Ensures all numbers calculated in the UI are permanently attached to their corresponding trials.
