import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { appConfig } from '../../config/runtime';
import { AuthTokenStore } from './AuthTokenStore';
const apiClient = axios.create({ baseURL: appConfig.apiBaseUrl, timeout: 20000 });
type Request = InternalAxiosRequestConfig & { _retry?: boolean; _session?: string | null; _identity?: string | null };
let refreshing: { token: string; promise: Promise<string> } | null = null;
const identity = () => AuthTokenStore.getSessionId?.() ?? AuthTokenStore.getRefreshToken();
apiClient.interceptors.request.use((config: Request) => {
  const token = AuthTokenStore.getAccessToken();
  config._identity ??= identity();
  config._session ??= AuthTokenStore.getRefreshToken();
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
  if (!request || request.url?.startsWith('/auth/') || error.response?.status !== 401 || request.signal?.aborted) throw error;
  request._identity ??= identity();
  const refreshToken = AuthTokenStore.getRefreshToken();
  request._session ??= refreshToken;
  if (request._identity !== identity()) throw error;
  if (request._retry || !refreshToken) {
    AuthTokenStore.clearTokens(); window.dispatchEvent(new Event('teacher_auth_changed')); throw error;
  }
  request._retry = true;
  // Another request may already have rotated this same session.
  if (request._session !== refreshToken && AuthTokenStore.getAccessToken()) {
    request._session = refreshToken;
    request.headers.Authorization = `Bearer ${AuthTokenStore.getAccessToken()}`;
    return apiClient(request);
  }
  if (!refreshing || refreshing.token !== refreshToken) {
    const pending = axios.post(`${appConfig.apiBaseUrl}/auth/refresh`, { refreshToken }, { timeout: 15000 })
      .then(({ data }) => {
        if (AuthTokenStore.getRefreshToken() !== refreshToken || request._identity !== identity()) throw new Error('Phiên đăng nhập đã thay đổi.');
        if (!data.accessToken || !data.refreshToken) throw new Error('Phản hồi xác thực không hợp lệ.');
        AuthTokenStore.setTokens(data.accessToken, data.refreshToken);
        return data.accessToken as string;
      }).catch(cause => {
        if (request._identity === identity() && AuthTokenStore.getRefreshToken() === refreshToken) {
          AuthTokenStore.clearTokens(); window.dispatchEvent(new Event('teacher_auth_changed'));
        }
        throw cause;
      }).finally(() => { if (refreshing?.token === refreshToken) refreshing = null; });
    refreshing = { token: refreshToken, promise: pending };
  }
  const token = await refreshing.promise;
  if (request._identity !== identity()) throw new Error('Phiên đăng nhập đã thay đổi.');
  request._session = AuthTokenStore.getRefreshToken(); request.headers.Authorization = `Bearer ${token}`;
  return apiClient(request);
});

export default apiClient;
