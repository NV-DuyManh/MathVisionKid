# HandAI Model Card

## 1. Model Details
- **Name**: CRNN-v1.2-PyTorch
- **Framework**: PyTorch
- **Task**: Offline Handwritten Text Recognition (Vietnamese)
- **Status**: Production (Integrated via ONNX / CoreML equivalents internally or remote API)
- **Dataset Version**: HandAI-v1.2

## 2. Architecture Specification
The model employs a standard CRNN (Convolutional Recurrent Neural Network) architecture optimized for sequence transcription:
1. **CNN Feature Extractor**: Extracts dense feature maps from the input image slice.
2. **BiLSTM (Bidirectional Long Short-Term Memory)**: Captures sequential contextual dependencies across the feature sequence in both directions.
3. **CTC Decoder (Connectionist Temporal Classification)**: Maps the recurrent sequence output into text, allowing alignment-free transcription of the handwriting.

## 3. Training Metadata
- **Parameters**: ~8.5M parameters (approximate standard CRNN).
- **Training Seed**: 42
- **Training Date**: 2026-07-05
- **Optimizer**: Adam
- **Loss Function**: CTC Loss

## 4. Evaluation Metrics
The model is strictly evaluated under the **HandAI Ablation Benchmark Engine**:
- **Character Error Rate (CER)**: Dynamically tracked per session.
- **Word Error Rate (WER)**: Evaluates complete word token correctness.
- **Line Accuracy**: Computes perfect exact-match lines against explicit ground truths.
- *(Note: Specific metrics are aggregated real-time in the `GlobalAnalytics` layer to prevent manual data fabrication).*

## 5. Limitations
- **Handwriting Diversity**: Struggles with extremely cursive or heavily joined Vietnamese scripts.
- **Diacritics Sensitivity**: Minor susceptibility to missing faint diacritics (e.g., `đ`, `ă`, `ô`) if the image contrast is low.
- **Image Quality Constraints**: Requires relatively stable lighting; confidence drops below 65% on severely blurred inputs.
