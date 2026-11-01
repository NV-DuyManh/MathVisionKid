jest.mock('../config/env', () => ({ ENV: { USE_MOCK: true } }));
jest.mock('../services/api/apiClient', () => ({ __esModule: true, default: { post: jest.fn(), get: jest.fn() } }));
jest.mock('../services/auth/tokenStorage', () => ({ tokenStorage: { getAccessToken: jest.fn(), getUser: jest.fn() } }));
import { authApi, getMockStudentUser } from '../services/api/authApi';
import { ENV } from '../config/env';
import apiClient from '../services/api/apiClient';
import { tokenStorage } from '../services/auth/tokenStorage';
afterEach(() => { ENV.USE_MOCK = true; jest.clearAllMocks(); });
test.each(['admin.demo@mathvision.local', 'lan.teacher@mathvision.local', 'unknown@overhaul.test'])('mock rejects unlisted identity %s', async email => {
  expect(() => getMockStudentUser(email)).toThrow();
  await expect(authApi.login({ email, password: 'fixture-only' })).rejects.toThrow();
});
test('explicit student fixture is active and has only the student role', async () => {
  const result = await authApi.login({ email: 'minh.student@mathvision.local', password: 'fixture-only' });
  expect(result.user.role).toBe('STUDENT');
  expect(result.user.active).toBe(true);
});
test('mock restore never invents a default account', async () => {
  (tokenStorage.getUser as jest.Mock).mockResolvedValue(null);
  await expect(authApi.getMe()).rejects.toThrow();
});
test('real login drops any inline profile and offline remains an error', async () => {
  ENV.USE_MOCK = false;
  (apiClient.post as jest.Mock).mockResolvedValueOnce({ data: { accessToken: 'test-a', refreshToken: 'test-r', user: { role: 'STUDENT' } } });
  expect((await authApi.login({ email: 'account@overhaul.test', password: 'fixture-only' })).user).toBeUndefined();
  (apiClient.post as jest.Mock).mockRejectedValueOnce(new Error('Network Error'));
  await expect(authApi.login({ email: 'minh.student@mathvision.local', password: 'fixture-only' })).rejects.toThrow('Network Error');
});

test('production ignores the public mock flag even when it is true', () => {
  const descriptor = Object.getOwnPropertyDescriptor(globalThis, '__DEV__');
  const previous = process.env.EXPO_PUBLIC_USE_MOCK;
  try {
    Object.defineProperty(globalThis, '__DEV__', { configurable: true, value: false });
    process.env.EXPO_PUBLIC_USE_MOCK = 'true';
    jest.isolateModules(() => {
      const actual = jest.requireActual('../config/env');
      expect(actual.ENV.USE_MOCK).toBe(false);
    });
  } finally {
    if (descriptor) Object.defineProperty(globalThis, '__DEV__', descriptor);
    if (previous === undefined) delete process.env.EXPO_PUBLIC_USE_MOCK;
    else process.env.EXPO_PUBLIC_USE_MOCK = previous;
  }
});
