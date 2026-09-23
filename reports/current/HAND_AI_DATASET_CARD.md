# HandAI Dataset Card

## 1. Dataset Overview
- **Name**: HandAI Vietnamese Primary Handwriting Dataset
- **Version**: HandAI-v1.2
- **Source**: Collected from primary school student notebooks and assignments across multiple regions.
- **Grade Range**: Grade 1 to Grade 5.
- **Sample Count**: Scalable internal repository (exact counts dynamically managed via backend pipelines).

## 2. Collection and Curation
- **Annotation Process**: 
  - Raw images are uploaded and cropped.
  - Automatic line segmentation isolates individual handwriting lines.
  - Initial CRNN OCR attempts transcription.
  - Human review establishes the explicit `groundTruth` for model training and benchmark evaluations.
- **Duplicate Checking**: Images are hashed and deduplicated upon ingestion.
- **Privacy Handling**: Submissions are anonymized; PII and non-handwriting regions are cropped out during the `IMAGE_FLOW` phase before reaching the OCR engine.

## 3. Dataset Split
- **Training Set**: ~70% (Used for optimizing the CRNN BiLSTM layers)
- **Validation Set**: ~15% (Used for hyperparameter tuning and preventing overfitting)
- **Test Set**: ~15% (Strictly isolated for `computeTrialAnalytics` benchmark validations)

## 4. Known Limitations
- **Handwriting Diversity**: Highly stylized or non-standard grip handwriting may be underrepresented.
- **Image Quality Variation**: Shadows, poor lighting, and crumpled paper can introduce noise that the dataset augmentations may not perfectly cover.
- **Regional Handwriting Differences**: Regional stylistic variations in certain Vietnamese letters (e.g., `q`, `g`, `k`) may require further balancing.
