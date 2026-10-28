import axios from 'axios';
import '../services/api/apiClient';
import { tokenStorage } from '../services/auth/tokenStorage';

jest.mock('../config/env', () => ({ ENV: { API_BASE_URL: 'http://test-only.invalid' } }));
jest.mock('../services/auth/tokenStorage', () => ({ tokenStorage: { getSessionId: jest.fn(async () => 'test-session'), getAccessToken: jest.fn(), getRefreshToken: jest.fn(), saveTokens: jest.fn(), clearTokens: jest.fn() } }));
jest.mock('axios', () => {
  const client = Object.assign(jest.fn(), { defaults: { headers: { common: {} } }, interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } } });
  return { __esModule: true, default: { create: () => client, post: jest.fn(), client } };
});
const client = (axios as any).client;
const rejected = client.interceptors.response.use.mock.calls[0][1];
const prepareRequest = client.interceptors.request.use.mock.calls[0][0];
const failure = (url = '/me') => ({ response: { status: 401 }, config: { url, headers: {}, _identity: 'test-session', _session: 'test-refresh' } });
beforeEach(() => { (axios.post as jest.Mock).mockReset(); (tokenStorage.getRefreshToken as jest.Mock).mockReset(); client.mockReset(); });

it('does not try refreshing a rejected login or refresh request', async () => {
  for (const path of ['/auth/login', '/auth/refresh', '/auth/logout']) {
    const error = failure(path);
    await expect(rejected(error)).rejects.toBe(error);
  }
  expect(axios.post).not.toHaveBeenCalled();
});

it('does not send an expired session token on a new login', async () => {
  (tokenStorage.getAccessToken as jest.Mock).mockClear().mockResolvedValue('expired-test-token');
  const config=await prepareRequest({url:'/auth/login',headers:{Authorization:'Bearer expired-test-token'}});
  expect(config.headers.Authorization).toBeUndefined();
  expect(tokenStorage.getAccessToken).not.toHaveBeenCalled();
});

it('rejects every waiter if the refresh token is missing instead of leaving the queue hung', async () => {
  let finish!: (value: null) => void;
  (tokenStorage.getRefreshToken as jest.Mock).mockReturnValue(new Promise(resolve => { finish = resolve; }));
  const first = rejected(failure()), second = rejected(failure());
  const settled = Promise.allSettled([first, second]); finish(null);
  expect((await settled).every(result => result.status === 'rejected')).toBe(true);
});

it('bounds a refresh call and retries queued requests only once', async () => {
  (tokenStorage.getRefreshToken as jest.Mock).mockResolvedValue('test-refresh');
  (axios.post as jest.Mock).mockResolvedValue({ data: { accessToken: 'test-access', refreshToken: 'new-test-refresh' } });
  client.mockImplementation(async (request: any) => { if (request._retry) throw failure(); });
  await expect(rejected(failure())).rejects.toBeDefined();
  expect(axios.post).toHaveBeenCalledTimes(1);
  expect(axios.post).toHaveBeenCalledWith(expect.any(String), expect.anything(), { timeout: 8000 });
  expect(client.mock.calls[0][0]._retry).toBe(true);
});
