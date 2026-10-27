import axios, { CanceledError } from 'axios';
import { ENV } from '../../config/env';
import { tokenStorage } from '../auth/tokenStorage';
import { sessionEvents } from '../auth/sessionEvents';
// eslint-disable-next-line import/no-named-as-default-member
const apiClient = axios.create({ baseURL: ENV.API_BASE_URL, timeout: 60000 });
let refreshing: { token: string; promise: Promise<string> } | null = null;
const identity = async () => tokenStorage.getSessionId?.() ?? tokenStorage.getRefreshToken();
async function expire(id: string | null, reason: 'expired' | 'forbidden' = 'expired') {
  if (await identity() !== id) return;
  await tokenStorage.clearTokens();
  delete apiClient.defaults.headers.common.Authorization;
  sessionEvents.expired(reason);
}
apiClient.interceptors.request.use(async config => {
  config.baseURL = ENV.API_BASE_URL;
  const before = await identity();
  const token = await tokenStorage.getAccessToken();
  const refresh = await tokenStorage.getRefreshToken();
  if (before !== await identity()) throw new CanceledError('Phiên đăng nhập đã thay đổi.');
  const request = config as any;
  request._identity ??= before; request._session ??= refresh;
  if (!config.url?.startsWith('/auth/')) {
    if (token && /^(demo|mock)[_-]/i.test(token)) throw new Error('Phiên thử nghiệm không được sử dụng với dữ liệu trực tuyến. Vui lòng đăng nhập lại.');
    if (token) config.headers.Authorization = `Bearer ${token}`; else delete config.headers.Authorization;
  }
  const form = config.data && (config.data instanceof FormData || typeof config.data.append === 'function' || Boolean(config.data._parts));
  if (form) { config.headers.delete('Content-Type'); config.headers.delete('content-type'); }
  if (!config.headers['X-Request-ID']) config.headers['X-Request-ID'] = 'req_' + Math.random().toString(36).slice(2, 10) + '_' + Date.now().toString(36);
  return config;
});
apiClient.interceptors.response.use(async response => {
  const request = response.config as any;
  if (!request.url?.startsWith('/auth/') && request._identity !== await identity()) throw new CanceledError('Phiên đăng nhập đã thay đổi.');
  const requestId = response.headers?.['x-request-id'];
  if (requestId && response.data && typeof response.data === 'object' && !response.data.requestId) response.data.requestId = requestId;
  return response;
}, async error => {
  const request = error.config;
  if (request && error.response?.status === 403 && !request.url?.startsWith('/auth/') && request._identity === await identity()) {
    let allowed = false;
    try {
      const token = await tokenStorage.getAccessToken();
      const { data } = await axios.get(`${ENV.API_BASE_URL}/me`, { headers: { Authorization: `Bearer ${token}` }, timeout: 10000 });
      allowed = data.role === 'STUDENT' && data.active === true;
    } catch { /* Never use a saved profile as authority after a forbidden response. */ }
    if (!allowed) await expire(request._identity, 'forbidden');
  }
  if (!request || request.url?.startsWith('/auth/') || error.response?.status !== 401 || request.signal?.aborted) throw error;
  const id = await identity();
  if (request._identity !== id) throw error;
  const refresh = await tokenStorage.getRefreshToken();
  if (request._retry || !refresh || /^(demo|mock)[_-]/i.test(refresh)) { await expire(id); throw error; }
  request._retry = true;
  if (request._session !== refresh) {
    request._session = refresh; request.headers.Authorization = `Bearer ${await tokenStorage.getAccessToken()}`; return apiClient(request);
  }
  if (!refreshing || refreshing.token !== refresh) {
    const promise = axios.post(`${ENV.API_BASE_URL}/auth/refresh`, { refreshToken: refresh }, { timeout: 15000 })
      .then(async ({ data }) => {
        if (await identity() !== id || await tokenStorage.getRefreshToken() !== refresh) throw new CanceledError('Phiên đăng nhập đã thay đổi.');
        if (!data.accessToken || !data.refreshToken) throw new Error('Phản hồi xác thực không hợp lệ.');
        await tokenStorage.saveTokens(data.accessToken, data.refreshToken, id);
        if (await identity() !== id) throw new CanceledError('Phiên đăng nhập đã thay đổi.');
        return data.accessToken as string;
      }).catch(async cause => { await expire(id); throw cause; })
      .finally(() => { if (refreshing?.token === refresh) refreshing = null; });
    refreshing = { token: refresh, promise };
  }
  request.headers.Authorization = `Bearer ${await refreshing.promise}`;
  request._session = await tokenStorage.getRefreshToken();
  return apiClient(request);
});
export default apiClient;
