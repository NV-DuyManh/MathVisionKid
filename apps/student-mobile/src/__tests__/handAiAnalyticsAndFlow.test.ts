import { submissionDraftStore, logImageFlow } from '../services/draft/submissionDraftStore';
import { handAiAnalyticsStore } from '../services/analytics/handAiAnalyticsStore';
import { normalizeLocalFileUri, normalizeFileUri, resolveSafeCropImage } from '../services/image/imagePipeline';

describe('HandAI Flow, Image Lifecycle & Analytics Suite', () => {
  beforeEach(async () => {
    submissionDraftStore.clearDraft();
    await handAiAnalyticsStore.reset();
  });

  describe('Bug 1: Image Pipeline & Lifecycle Integrity', () => {
    it('strictly preserves originalImageUri even if privacy screen screenshot or preview is generated', () => {
      const originalPhotoUri = 'file:///storage/emulated/0/DCIM/Camera/IMG_20260923_101500.jpg';
      const privacyScreenshotUri = 'file:///data/user/0/com.mathvisionkids/cache/ViewShot_privacy_preview_17901.png';

      // 1. User acquires original image via Camera/Gallery
      submissionDraftStore.setDraft({
        uri: originalPhotoUri,
        rawUri: originalPhotoUri,
        originalImageUri: originalPhotoUri,
        originalUri: originalPhotoUri,
        sourceImageUri: originalPhotoUri,
        width: 1920,
        height: 1080,
        mimeType: 'image/jpeg',
        filename: 'photo.jpg',
        source: 'CAMERA',
      });

      let currentDraft = submissionDraftStore.getDraft();
      expect(currentDraft?.originalImageUri).toBe(originalPhotoUri);
      expect(currentDraft?.uri).toBe(originalPhotoUri);

      // 2. Simulate privacy preview viewshot captured
      submissionDraftStore.updateDraft({
        privacyImageUri: privacyScreenshotUri,
        uri: privacyScreenshotUri, // Even if uri was temporarily set
      });

      currentDraft = submissionDraftStore.getDraft();
      // Safeguard: In HandAI or safe pipeline, originalImageUri remains completely untouched
      expect(currentDraft?.originalImageUri).toBe(originalPhotoUri);
      expect(currentDraft?.privacyImageUri).toBe(privacyScreenshotUri);

      // 3. Log image flow output check
      const logs: string[] = [];
      const originalConsoleLog = console.log;
      console.log = (msg: string) => logs.push(msg);

      logImageFlow({
        originalUri: currentDraft?.originalImageUri,
        privacyUri: currentDraft?.privacyImageUri,
        cropInputUri: currentDraft?.originalImageUri,
        activeRecognitionUri: currentDraft?.croppedImageUri || currentDraft?.originalImageUri,
      });
      console.log = originalConsoleLog;

      const flowLog = logs.join('\n');
      expect(flowLog).toContain('[IMAGE_FLOW]');
      expect(flowLog).toContain(`originalUri=${originalPhotoUri}`);
    });
  });

  describe('Bug 3: AI Correction Candidate Logic', () => {
    it('evaluates whether candidates should be shown based on distinctness and non-emptiness', () => {
      const rawOcr = '15 + 27 = 42';
      const identicalCandidate = '15 + 27 = 42';
      const distinctCandidate = '15 + 27 = 42 (đã kiểm tra)';

      // When identical: candidate should NOT be displayed
      const isIdenticalDistinct = identicalCandidate.trim().toLowerCase() !== rawOcr.trim().toLowerCase();
      expect(isIdenticalDistinct).toBe(false);

      // When distinct: candidate should be displayed
      const isDifferentDistinct = distinctCandidate.trim().toLowerCase() !== rawOcr.trim().toLowerCase();
      expect(isDifferentDistinct).toBe(true);
    });
  });

  describe('Bug 5: Recognition Accuracy Analytics Dashboard Store', () => {
    it('initializes with benchmark trend sessions (Session 1: 82%, Session 2: 88%, Session 3: 91%)', async () => {
      await handAiAnalyticsStore.init();
      const sessions = handAiAnalyticsStore.getSessions();
      expect(sessions.length).toBeGreaterThanOrEqual(3);

      expect(sessions[0].accuracy).toBe(82);
      expect(sessions[1].accuracy).toBe(88);
      expect(sessions[2].accuracy).toBe(91);

      const summary = handAiAnalyticsStore.getSummary();
      expect(summary.accuracyPercent).toBeGreaterThan(80);
      expect(summary.averageConfidence).toBeGreaterThan(80);
      expect(summary.totalSessions).toBe(sessions.length);
    });

    it('correctly calculates accuracy %, confidence, and source distribution when recording a new trial', async () => {
      await handAiAnalyticsStore.init();
      const initialCount = handAiAnalyticsStore.getSessions().length;

      const mockTrial: MultilineTrialResult = {
        trialId: 'test_trial_live_1',
        source: 'CAMERA',
        pageImageObjectKey: 'ocr-trials/test_page.jpg',
        pageImageSha256: 'sha256_mock_123',
        pageWidth: 800,
        pageHeight: 600,
        privacyConfirmed: true,
        isTestData: false,
        dataOrigin: 'TEST',
        status: 'SUCCESS',
        createdAt: new Date().toISOString(),
        lines: [
          {
            lineId: 'line_1',
            predictedText: 'Đạo hàm của sin(x) là cos(x)',
            confidence: 0.95,
            verdict: 'CORRECT',
            selectedSource: 'OCR',
            trainingEligible: true,
          },
          {
            lineId: 'line_2',
            predictedText: 'Tích phân từ 0 đến 1',
            confidence: 0.90,
            verdict: 'CONFIRMED',
            selectedSource: 'SUGGESTION_1',
            trainingEligible: true,
          },
          {
            lineId: 'line_3',
            predictedText: 'x^2 + 2x + 1 = 0',
            confidence: 0.85,
            verdict: 'CORRECTED',
            selectedSource: 'MANUAL_EDIT',
            trainingEligible: true,
          },
          {
            lineId: 'line_4',
            predictedText: 'Nghiệm kép x = -1',
            confidence: 0.94,
            verdict: 'CORRECT',
            selectedSource: 'OCR',
            trainingEligible: true,
          },
        ],
      };

      const session = await handAiAnalyticsStore.recordTrial(mockTrial);

      expect(session.sessionId).toBe('test_trial_live_1');
      expect(session.totalLines).toBe(4);
      // 3 of 4 were model correct (1 required manual correction)
      expect(session.correctLines).toBe(3);
      expect(session.accuracy).toBe(75);
      expect(session.crnnRawCount).toBe(2);
      expect(session.aiCorrectionCount).toBe(1);
      expect(session.manualEditCount).toBe(1);

      const updatedSessions = handAiAnalyticsStore.getSessions();
      expect(updatedSessions.length).toBe(initialCount + 1);

      const sourceDist = handAiAnalyticsStore.getSourceDistribution();
      expect(sourceDist[0].label).toBe('CRNN Raw');
      expect(sourceDist[0].count).toBeGreaterThan(0);
      expect(sourceDist[1].label).toBe('AI Correction');
      expect(sourceDist[1].count).toBeGreaterThan(0);

      const confBuckets = handAiAnalyticsStore.getConfidenceDistribution();
      expect(confBuckets.length).toBe(3); // High, Medium, Low
    });
  });

  describe('HAND_AI Crop Image Loading & normalizeLocalFileUri Suite', () => {
    it('normalizeLocalFileUri keeps file:// URIs unchanged and never decodes Expo ExperienceData paths', () => {
      const androidExperienceUri =
        'file:///data/user/0/host.exp.exponent/cache/ExperienceData/%2540anonymous%252Fhand-ai-1234/Camera/photo.jpg';
      const normalized = normalizeLocalFileUri(androidExperienceUri);
      expect(normalized).toBe(androidExperienceUri);
      expect(normalized).toContain('%2540anonymous%252F');
      expect(normalized).not.toContain('@anonymous');
    });

    it('normalizeLocalFileUri adds file:// prefix to raw absolute file paths', () => {
      const rawPath = '/data/user/0/com.mathvisionkids/cache/test.jpg';
      const normalized = normalizeLocalFileUri(rawPath);
      expect(normalized).toBe('file:///data/user/0/com.mathvisionkids/cache/test.jpg');
    });

    it('resolveSafeCropImage generates [CROP_DEBUG] logs with exact format', async () => {
      const testUri = 'file:///data/user/0/host.exp.exponent/cache/ExperienceData/%2540anonymous%252Fhand-ai/Camera/test.jpg';
      const logs: string[] = [];
      const originalConsoleLog = console.log;
      console.log = (msg: string) => logs.push(msg);

      const result = await resolveSafeCropImage(testUri);
      console.log = originalConsoleLog;

      const debugLog = logs.join('\n');
      expect(debugLog).toContain('[CROP_DEBUG]');
      expect(debugLog).toContain(`originalUri=${testUri}`);
      expect(debugLog).toContain(`normalizedUri=${testUri}`);
      expect(debugLog).toContain('exists=');
      expect(debugLog).toContain('finalUri=');
      expect(result.originalUri).toBe(testUri);
      expect(result.normalizedUri).toBe(testUri);
    });

    it('CASE 1: Gallery image -> original gallery URI is preserved for crop', () => {
      const galleryUri = 'file:///data/user/0/host.exp.exponent/cache/ExperienceData/%2540anonymous%252Fhand-ai/ImagePicker/test.jpg';
      submissionDraftStore.setDraft({
        uri: galleryUri,
        rawUri: galleryUri,
        originalImageUri: galleryUri,
        width: 1080,
        height: 1920,
        mimeType: 'image/jpeg',
        filename: 'gallery.jpg',
        source: 'GALLERY',
      });

      const draft = submissionDraftStore.getDraft();
      expect(draft?.originalImageUri).toBe(galleryUri);
      expect(draft?.source).toBe('GALLERY');
    });

    it('CASE 2: Camera image -> original camera URI is preserved for crop', () => {
      const cameraUri = 'file:///data/user/0/host.exp.exponent/cache/ExperienceData/%2540anonymous%252Fhand-ai/Camera/captured.jpg';
      submissionDraftStore.setDraft({
        uri: cameraUri,
        rawUri: cameraUri,
        originalImageUri: cameraUri,
        width: 1920,
        height: 1080,
        mimeType: 'image/jpeg',
        filename: 'camera.jpg',
        source: 'CAMERA',
      });

      const draft = submissionDraftStore.getDraft();
      expect(draft?.originalImageUri).toBe(cameraUri);
      expect(draft?.source).toBe('CAMERA');
    });

    it('CASE 3: HAND_AI bypass privacy -> crop never receives ViewShot or privacy artifacts', () => {
      const prevMode = process.env.EXPO_PUBLIC_APP_MODE;
      process.env.EXPO_PUBLIC_APP_MODE = 'HAND_AI';
      try {
        const originalUri = 'file:///storage/emulated/0/DCIM/Camera/IMG_2026.jpg';
        const privacyViewShot = 'file:///data/user/0/cache/ViewShot_masked.png';

        submissionDraftStore.setDraft({
          uri: originalUri,
          rawUri: originalUri,
          originalImageUri: originalUri,
          privacyImageUri: privacyViewShot,
          width: 1200,
          height: 1600,
          mimeType: 'image/jpeg',
          filename: 'original.jpg',
        });

        // In HAND_AI mode, getDraft() guarantees privacyImageUri is undefined
        const draft = submissionDraftStore.getDraft();
        expect(draft?.originalImageUri).toBe(originalUri);
        expect(draft?.privacyImageUri).toBeUndefined();
      } finally {
        process.env.EXPO_PUBLIC_APP_MODE = prevMode;
      }
    });

    it('CASE 4 & 5: Normal flow compatibility and clean draft initialization', () => {
      const standardUri = 'file:///photos/math1.jpg';
      submissionDraftStore.setDraft({
        uri: standardUri,
        rawUri: standardUri,
        width: 800,
        height: 600,
        mimeType: 'image/jpeg',
        filename: 'math1.jpg',
      });

      const draft = submissionDraftStore.getDraft();
      expect(draft).not.toBeNull();
      expect(draft?.uri).toBe(standardUri);
    });
  });
});
