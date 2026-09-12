package com.mathvisionkids.api.ocr.multiline;

import com.mathvisionkids.api.user.User;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "ocr_multiline_trials")
@Getter
@Setter
@NoArgsConstructor
public class OcrMultilineTrial {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "trial_id")
    private UUID trialId;

    @com.fasterxml.jackson.annotation.JsonIgnore
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    @Column(nullable = false)
    private String source = "CAMERA";

    @Column(name = "page_image_object_key", nullable = false)
    private String pageImageObjectKey;

    @Column(name = "page_image_sha256", nullable = false)
    private String pageImageSha256;

    @Column(name = "page_width")
    private Integer pageWidth;

    @Column(name = "page_height")
    private Integer pageHeight;

    @Column(name = "privacy_confirmed", nullable = false)
    private boolean privacyConfirmed = false;

    @Column(name = "is_test_data", nullable = false)
    private boolean isTestData = false;

    @Column(name = "data_origin", nullable = false)
    private String dataOrigin = "PHYSICAL_USER";

    @Column(nullable = false)
    private String domain = "HANDWRITING_TEXT";

    @Column(nullable = false)
    private String status = "COMPLETED";

    @Column(name = "created_at", updatable = false)
    private Instant createdAt = Instant.now();

    @OneToMany(mappedBy = "trial", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    @OrderBy("lineOrder ASC")
    private List<OcrMultilineLine> lines = new ArrayList<>();

    @com.fasterxml.jackson.annotation.JsonProperty("userId")
    public UUID getUserId() {
        return user != null ? user.getId() : null;
    }
}
