import { recognitionDraftStore } from '../features/recognition/state/recognitionDraftStore';
import { normalizeOcrError } from '../features/recognition/api/RecognitionService';

describe('Recognition uses MathVision privacy and authentication', () => {
  afterEach(() => recognitionDraftStore.clearDraft());
  it('keeps a protected image and its immutable original separate', () => {
    const original = 'file:///photos/notebook.jpg';
    const masked = 'file:///cache/ViewShot_masked.png';
    recognitionDraftStore.setDraft({ uri: original, sourceImageUri: original, privacyImageUri: masked, isMasked: true });
    expect(recognitionDraftStore.getDraft()?.privacyImageUri).toBe(masked);
    expect(recognitionDraftStore.getDraft()?.isMasked).toBe(true);
    recognitionDraftStore.updateDraft({ uri: masked, originalImageUri: masked });
    expect(recognitionDraftStore.getDraft()?.originalImageUri).toBe(original);
    expect(recognitionDraftStore.getDraft()?.uri).toBe(masked);
  });
  test.each([401, 403])('requests login again on %s', status => {
    const error = normalizeOcrError({ response: { status } });
    expect(error.title).toContain('Phiên đăng nhập hết hạn');
    expect(error.message).toContain('đăng nhập lại');
  });
  it('explains a failed request without exposing backend details or calling every failure busy', () => {
    const error = normalizeOcrError({ response: { status: 500, data: { error: { message: 'SQL error gemini_confidence_source' } } } });
    expect(error.message).toContain('vẫn được giữ');
    expect(error.message).not.toMatch(/SQL|gemini|500/);
    expect(error.title).not.toContain('đang bận');
    expect(normalizeOcrError({ response: { status: 503 } }).title).toContain('đang bận');
  });
});
