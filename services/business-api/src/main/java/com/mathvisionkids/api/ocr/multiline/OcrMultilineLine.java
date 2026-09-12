package com.mathvisionkids.api.ocr.multiline;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "ocr_multiline_lines")
@Getter
@Setter
@NoArgsConstructor
public class OcrMultilineLine {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "line_id")
    private UUID lineId;

    @com.fasterxml.jackson.annotation.JsonIgnore
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "trial_id", nullable = false)
    private OcrMultilineTrial trial;

    @Column(name = "line_order", nullable = false)
    private int lineOrder;

    @Column(nullable = false)
    private int x;

    @Column(nullable = false)
    private int y;

    @Column(nullable = false)
    private int width;

    @Column(nullable = false)
    private int height;

    @Column(name = "line_image_object_key", nullable = false)
    private String lineImageObjectKey;

    @Column(name = "line_image_sha256", nullable = false)
    private String lineImageSha256;

    @Column(name = "predicted_text", nullable = false)
    private String predictedText;

    @Column(name = "verified_text_raw")
    private String verifiedTextRaw;

    @Column(name = "verified_text_normalized")
    private String verifiedTextNormalized;

    @Column(nullable = false)
    private String verdict = "UNVERIFIED";

    @Column(name = "training_eligible", nullable = false)
    private boolean trainingEligible = false;

    @Column(name = "model_name")
    private String modelName = "Vietnamese-Handwriting-OCR-Full";

    @Column(name = "model_version")
    private String modelVersion = "1.0.0";

    @Column(name = "checkpoint_sha256")
    private String checkpointSha256;

    @Column(name = "vocab_sha256")
    private String vocabSha256;

    @Column(name = "preprocessing_version")
    private String preprocessingVersion = "v1_resize_64x1024_imagenet";

    @Column(name = "feedback_at")
    private Instant feedbackAt;

    @Column(name = "created_at", updatable = false)
    private Instant createdAt = Instant.now();
}
