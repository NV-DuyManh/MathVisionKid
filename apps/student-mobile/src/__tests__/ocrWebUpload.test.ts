import { Platform } from 'react-native';
import apiClient from '../services/api/apiClient';
import { RecognitionService } from '../features/recognition/api/RecognitionService';

jest.mock('../services/api/apiClient', () => ({ __esModule: true,
  default: { post: jest.fn(), defaults: { baseURL: 'http://test.invalid' } } }));
jest.mock('../services/auth/tokenStorage', () => ({ tokenStorage: { getAccessToken: jest.fn().mockResolvedValue(null) } }));

test.each(['blob:https://app.invalid/photo', 'data:image/png;base64,aGVsbG8='])(
  'web sends image bytes for %s through the authenticated backend client', async (uri) => {
    const oldOS = Platform.OS;
    const oldFetch = global.fetch;
    const oldFormData = global.FormData;
    const parts: unknown[][] = [];
    const image = new Blob(['actual-image-bytes'], { type: 'image/png' });
    Platform.OS = 'web';
    global.fetch = jest.fn().mockResolvedValue({ ok: true, blob: async () => image });
    global.FormData = class { append(...values: unknown[]) { parts.push(values); } } as any;
    (apiClient.post as jest.Mock).mockResolvedValue({ status: 200, data: { lines: [] } });
    try {
      await RecognitionService.detectLines(uri);
      expect(global.fetch).toHaveBeenCalledWith(uri, { signal: undefined });
      expect(parts[0][0]).toBe('image');
      expect(parts[0][1]).toBe(image);
      expect(apiClient.post).toHaveBeenCalledWith('/ocr/multiline/detect', expect.anything(), expect.anything());
    } finally {
      Platform.OS = oldOS;
      global.fetch = oldFetch;
      global.FormData = oldFormData;
    }
  }
);
