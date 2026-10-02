import { RecognitionService, type LineBox } from '../features/recognition/api/RecognitionService';

jest.mock('../services/api/apiClient', () => ({ __esModule: true, default: {} }));
jest.mock('../features/recognition/image/imagePipeline', () => ({ ensureFileUri: (uri: string) => uri }));
jest.mock('../services/auth/tokenStorage', () => ({ tokenStorage: {} }));

test('confirmed handwriting preserves measured zero and score provenance over JSON transport', () => {
  const line: LineBox = {
    line_id: 'line-1', x: 1, y: 2, width: 100, height: 30, order: 1,
    rawOcrText: '25 - 8 = 18', rawOcrConfidence: 0,
    rawOcrConfidenceSource: 'CRNN_CTC_SOFTMAX',
    groqConfidence: 0, groqConfidenceSource: 'AI_SELF_REPORTED', groqStatus: 'SUCCESS',
  };
  const payload = JSON.parse(JSON.stringify(RecognitionService.minimizeLineForTransport(line)));
  expect(payload.rawOcrText).toBe('25 - 8 = 18');
  expect(payload.rawOcrConfidence).toBe(0);
  expect(payload.rawOcrConfidenceSource).toBe('CRNN_CTC_SOFTMAX');
  expect(payload.groqConfidence).toBe(0);
  expect(payload.groqConfidenceSource).toBe('AI_SELF_REPORTED');
  expect(payload).not.toHaveProperty('geminiConfidence');
  expect(payload).not.toHaveProperty('geminiConfidenceSource');
});
