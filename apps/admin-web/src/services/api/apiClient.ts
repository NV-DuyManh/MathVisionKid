import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { appConfig } from '../../config/runtime';
import { tokenStore } from './tokenStore';
export const apiClient = axios.create({ baseURL: appConfig.apiBaseUrl, timeout: 20000 });
type Request = InternalAxiosRequestConfig & { _retry?: boolean; _session?: string | null; _identity?: string | null };
let refreshing: { token: string; promise: Promise<string> } | null = null;
const identity = () => tokenStore.getSessionId?.() ?? tokenStore.getRefreshToken();
apiClient.interceptors.request.use((config: Request) => {
  const token = tokenStore.getAccessToken();
  config._identity ??= identity();
  config._session ??= tokenStore.getRefreshToken();
  if (!config.url?.startsWith('/auth/') || config.url === '/auth/sso/ticket') {
    if (token) config.headers.Authorization = `Bearer ${token}`;
    else delete config.headers.Authorization;
  }
  return config;
});
apiClient.interceptors.response.use(response => {
  const request = response.config as Request;
  if (!request.url?.startsWith('/auth/') && request._identity !== identity()) throw new Error('Phiên đăng nhập đã thay đổi.');
  return response;
}, async (error: AxiosError) => {
  const request = error.config as Request | undefined;
  if (request && error.response?.status === 403 && request.url?.startsWith('/admin/') && request._identity === identity()) {
    let allowed = false;
    try {
      const { data } = await axios.get(`${appConfig.apiBaseUrl}/me`, { headers: { Authorization: `Bearer ${tokenStore.getAccessToken()}` }, timeout: 10000 });
      allowed = data.role === 'ADMIN' && data.active === true;
    } catch { /* A forbidden session cannot rely on a cached role. */ }
    if (!allowed && request._identity === identity()) {
      tokenStore.clearTokens();
      window.dispatchEvent(new CustomEvent('admin_auth_required', { detail: { status: 403 } }));
    }
  }
  if (!request || request.url?.startsWith('/auth/') || error.response?.status !== 401 || request.signal?.aborted) throw error;
  request._identity ??= identity();
  const refreshToken = tokenStore.getRefreshToken();
  request._session ??= refreshToken;
  if (request._identity !== identity()) throw error;
  if (request._retry || !refreshToken) {
    tokenStore.clearTokens(); window.dispatchEvent(new CustomEvent('admin_auth_required')); throw error;
  }
  request._retry = true;
  // Another request may already have rotated this same session.
  if (request._session !== refreshToken && tokenStore.getAccessToken()) {
    request._session = refreshToken;
    request.headers.Authorization = `Bearer ${tokenStore.getAccessToken()}`;
    return apiClient(request);
  }
  if (!refreshing || refreshing.token !== refreshToken) {
    const pending = axios.post(`${appConfig.apiBaseUrl}/auth/refresh`, { refreshToken }, { timeout: 15000 })
      .then(({ data }) => {
        if (tokenStore.getRefreshToken() !== refreshToken || request._identity !== identity()) throw new Error('Phiên đăng nhập đã thay đổi.');
        if (!data.accessToken || !data.refreshToken) throw new Error('Phản hồi xác thực không hợp lệ.');
        tokenStore.setTokens(data.accessToken, data.refreshToken);
        return data.accessToken as string;
      }).catch(cause => {
        if (request._identity === identity() && tokenStore.getRefreshToken() === refreshToken) {
          tokenStore.clearTokens(); window.dispatchEvent(new CustomEvent('admin_auth_required'));
        }
        throw cause;
      }).finally(() => { if (refreshing?.token === refreshToken) refreshing = null; });
    refreshing = { token: refreshToken, promise: pending };
  }
  const token = await refreshing.promise;
  if (request._identity !== identity()) throw new Error('Phiên đăng nhập đã thay đổi.');
  request._session = tokenStore.getRefreshToken(); request.headers.Authorization = `Bearer ${token}`;
  return apiClient(request);
});
