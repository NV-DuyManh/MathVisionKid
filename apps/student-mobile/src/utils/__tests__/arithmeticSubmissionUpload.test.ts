import { Platform } from 'react-native';
import apiClient from '../../services/api/apiClient';
import { SpringSubmissionServiceClass } from '../../services/api/SpringSubmissionService';
import { recognitionDraftStore } from '../../features/recognition/state/recognitionDraftStore';

jest.mock('../../services/api/apiClient');
const service = new SpringSubmissionServiceClass();
const fetchBefore = global.fetch;

beforeEach(() => {
  jest.spyOn(console, 'log').mockImplementation(() => {});
  recognitionDraftStore.setDraft({ rawUri: 'file:///private-original.jpg', uri: 'blob:masked-cropped', width: 200, height: 300,
    mimeType: 'image/png', filename: 'crop.png', source: 'GALLERY', mode: 'ARITHMETIC' });
  (apiClient.post as jest.Mock).mockResolvedValue({ status: 202, data: { submissionId: 'server-sub', status: 'PROCESSING', jobId: 'job-latest' } });
});
afterEach(() => { global.fetch = fetchBefore; recognitionDraftStore.clearDraft(); jest.restoreAllMocks(); jest.clearAllMocks(); });

test.each(['upload', 'retry'])('web %s sends actual photo Blob, gallery source and cancellation signal', async operation => {
  jest.replaceProperty(Platform, 'OS', 'web');
  const photo = new Blob(['actual selected image bytes'], { type: 'image/png' });
  global.fetch = jest.fn().mockResolvedValue({ ok: true, blob: async () => photo });
  const append = jest.spyOn(FormData.prototype, 'append');
  const signal = new AbortController().signal;
  const result = operation === 'upload' ? await service.uploadImage('blob:masked-cropped', signal) : await service.retrySubmission('old-sub', 'blob:masked-cropped', signal);
  expect(global.fetch).toHaveBeenCalledWith('blob:masked-cropped', { signal });
  expect(append).toHaveBeenCalledWith('image', photo, expect.any(String));
  expect(append).toHaveBeenCalledWith('source', 'GALLERY');
  expect(apiClient.post).toHaveBeenCalledWith(operation === 'upload' ? '/student/submissions' : '/student/submissions/old-sub/retry', expect.any(FormData), expect.objectContaining({ signal }));
  expect(result).toMatchObject({ id: 'server-sub', status: 'PROCESSING', jobId: 'job-latest' });
});

test('web photo read failure does not POST an unusable object string', async () => {
  jest.replaceProperty(Platform, 'OS', 'web');
  global.fetch = jest.fn().mockResolvedValue({ ok: false });
  await expect(service.uploadImage('blob:masked-cropped')).rejects.toThrow();
  expect(apiClient.post).not.toHaveBeenCalled();
});

test('confirmation sends identified token JSON and preserves returned structured result', async () => {
  const correction = { jobId: 'job-latest', tokenId: 'second-seven', newClass: '3' };
  const returned = { submissionId: 'real', jobId: 'job-latest', status: 'FEEDBACK_READY', recognizedExercise: { expression: '17 + 13 = 30', tokens: [{ tokenId: 'second-seven', value: '3' }] }, validation: { isValid: true, diagnosisState: 'VALID' } };
  (apiClient.post as jest.Mock).mockResolvedValue({ data: returned });
  const signal = new AbortController().signal;
  expect(await service.confirmToken('real', correction, signal)).toEqual({ ...returned, id: 'real' });
  expect(apiClient.post).toHaveBeenCalledWith('/student/submissions/real/confirm-token', correction, { signal });
});
