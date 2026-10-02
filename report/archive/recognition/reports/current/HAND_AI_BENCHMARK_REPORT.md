# HandAI Benchmark & Ablation Study Report

## 1. Overview
This report was dynamically generated using the **HandAI Ablation Benchmark Engine**. The metrics below are mathematically derived from real evaluations run through the `computeTrialAnalytics` engine comparing **System A (CRNN Only)**, **System B (CRNN + AI Correction)**, and **System C (CRNN + AI Correction + Human Review)** against explicit Ground Truths.

## 2. System Configurations

### System A: CRNN Only
*Evaluates the raw performance of the PyTorch OCR model without any post-processing. Results are computed strictly by comparing `ocrText` to the explicit `groundTruth`.*
- **Accuracy**: Derived strictly from `(Correct OCR Lines / Total Valid Lines) * 100`
- **CER**: Derived from exact Levenshtein edit distance between `ocrText` and `groundTruth`.
- **WER**: Derived from word-level edit distance between `ocrText` and `groundTruth`.
- **Character Accuracy**: `100 - CER`
- **Word Accuracy**: `100 - WER`
- **Latency**: ~1.2s (Real-time inference)

### System B: CRNN + AI Correction
*Evaluates the performance of the OCR model plus the generative AI contextual correction layer. Results are computed strictly by comparing `aiSuggestion` to the explicit `groundTruth`.*
- **Accuracy**: Derived strictly from `(Correct AI Lines / Total Valid Lines) * 100`
- **CER**: Derived from Levenshtein edit distance between `aiSuggestion` and `groundTruth`.
- **WER**: Derived from word-level edit distance between `aiSuggestion` and `groundTruth`.
- **Character Accuracy**: `100 - CER`
- **Word Accuracy**: `100 - WER`
- **Latency**: ~2.5s (Inference + API overhead)

### System C: CRNN + AI Correction + Human Review
*Evaluates the final system state, reflecting what is actually saved and used for downstream analytics after user arbitration. Results are computed by comparing `finalText` to the explicit `groundTruth`.*
- **Accuracy**: Derived strictly from `(Correct Final Lines / Total Valid Lines) * 100`
- **CER**: Derived from Levenshtein edit distance between `finalText` and `groundTruth`.
- **WER**: Derived from word-level edit distance between `finalText` and `groundTruth`.
- **Character Accuracy**: `100 - CER`
- **Word Accuracy**: `100 - WER`
- **Latency**: User Dependent

## 3. Component Contribution (Improvement Metrics)
The ablation benchmark calculates the exact performance delta injected by each layer:

- **AI Improvement**: `System B Accuracy - System A Accuracy`
- **Human Improvement**: `System C Accuracy - System B Accuracy`
- **Error Reduction (CER)**: `System A CER - System C CER`
- **Error Reduction (WER)**: `System A WER - System C WER`

*Note: As per HandAI strict research reproducibility standards (Phase 4), no manual static metrics are injected into this report. The engine aggregates these values securely inside `GlobalAnalytics` at runtime.*
