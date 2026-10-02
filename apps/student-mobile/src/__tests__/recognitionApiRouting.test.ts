import { RecognitionService } from '../features/recognition/api/RecognitionService';
import apiClient from '../services/api/apiClient';

jest.mock('../services/api/apiClient', () => ({ __esModule: true, default: {
  defaults: { baseURL: 'http://test.invalid/api/v1' }, post: jest.fn(), get: jest.fn(),
} }));

describe('Recognition uses the canonical authenticated client', () => {
  beforeEach(() => { jest.clearAllMocks(); RecognitionService.clearCache(); });
  it('detects lines through /ocr', async () => {
    (apiClient.post as jest.Mock).mockResolvedValue({ data: { width: 800, height: 600, lines: [{ line_id: '1' }] } });
    const result = await RecognitionService.detectLines('file:///notebook.jpg');
    expect((apiClient.post as jest.Mock).mock.calls[0][0]).toBe('/ocr/multiline/detect');
    expect(result.lines).toHaveLength(1);
  });
  it('creates trials through /ocr', async () => {
    (apiClient.post as jest.Mock).mockResolvedValue({ data: { trialId: 'trial-1', lines: [] } });
    await RecognitionService.createMultilineTrial('file:///notebook.jpg', []);
    expect((apiClient.post as jest.Mock).mock.calls[0][0]).toBe('/ocr/multiline/trials');
  });
  it('passes detection cancellation to the authenticated upload', async () => {
    const controller = new AbortController();
    (apiClient.post as jest.Mock).mockResolvedValue({ data: { width: 800, height: 600, lines: [] } });
    await RecognitionService.detectLines('file:///notebook.jpg', true, true, controller.signal);
    expect((apiClient.post as jest.Mock).mock.calls[0][2].signal).toBe(controller.signal);
  });
  it('fetches trials and clears cached page data between users', async () => {
    (apiClient.get as jest.Mock).mockResolvedValue({ data: { trialId: 'trial-1', lines: [] } });
    await RecognitionService.getMultilineTrial('trial-1');
    expect(apiClient.get).toHaveBeenCalledWith('/ocr/multiline/trials/trial-1');
    expect(RecognitionService.getCachedTrial('trial-1')).toBeDefined();
    RecognitionService.clearCache();
    expect(RecognitionService.getCachedTrial('trial-1')).toBeUndefined();
  });
  it('submits corrections through /ocr', async () => {
    (apiClient.post as jest.Mock).mockResolvedValue({ data: { lineId: 'line-1', verdict: 'CORRECTED' } });
    await RecognitionService.submitLineFeedback('trial-1', 'line-1', 'CORRECTED', '25 - 8 = 18');
    expect((apiClient.post as jest.Mock).mock.calls[0][0]).toBe('/ocr/multiline/trials/trial-1/lines/line-1/feedback');
  });
  it('discards an old account response arriving after logout', async () => {
    let resolve!: (value: any) => void;
    (apiClient.get as jest.Mock).mockImplementationOnce(() => new Promise(done => { resolve = done; }));
    const pending = RecognitionService.getMultilineTrial('old-account-trial');
    RecognitionService.clearCache();
    resolve({ data: { trialId: 'old-account-trial', lines: [] } });
    await expect(pending).rejects.toThrow('Phiên nhận dạng đã thay đổi');
    expect(RecognitionService.getCachedTrial('old-account-trial')).toBeUndefined();
  });
});
