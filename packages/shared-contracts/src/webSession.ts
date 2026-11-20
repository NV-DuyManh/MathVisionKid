import axios, { type AxiosError, type AxiosRequestConfig, type InternalAxiosRequestConfig } from 'axios';

type WebClient = 'portal' | 'teacher' | 'admin';
type SessionRequest = InternalAxiosRequestConfig & { _identity?: string | null; _logoutSession?: string };

export function createWebSession(client: WebClient, legacyKeys: string[], timeout = 20000) {
  const key = `mvk_${client}_web_session`;
  const events = new Set<() => void>();
  const externalChanges = new Set<() => void | Promise<void>>();
  const storage = () => typeof window === 'undefined' ? undefined : window.localStorage;
  if (typeof window !== 'undefined') {
    for (const oldKey of [...legacyKeys, `mvk_${client}_tab_session`]) window.sessionStorage?.removeItem(oldKey);
  }
  const getSessionId = () => storage()?.getItem(key) ?? null;
  let documentSession = getSessionId();
  let reloading = false;
  function clearProfile() {
    if (client === 'portal' && typeof window !== 'undefined') window.sessionStorage?.removeItem('mathvision_student_web_user_v1');
  }
  if (typeof window !== 'undefined') window.addEventListener?.('storage', event => {
    if (event.storageArea !== storage() || (event.key !== key && event.key !== null) || reloading || documentSession === getSessionId()) return;
    reloading = true;
    clearProfile();
    void Promise.allSettled([...externalChanges].map(cleanup => Promise.resolve().then(cleanup)))
      .then(() => window.location.reload());
  });
  function clearSession() {
    if (documentSession !== getSessionId()) return;
    documentSession = null;
    storage()?.removeItem(key);
    clearProfile();
  }
  const apiClient = axios.create({ baseURL: '/api/v1', timeout, allowAbsoluteUrls: false });
  apiClient.interceptors.request.use((request: SessionRequest) => {
    const id = getSessionId();
    if (reloading || documentSession !== id || (request._identity !== undefined && request._identity !== id)) {
      throw new axios.CanceledError('Phiên đăng nhập đã thay đổi.');
    }
    request._identity = id;
    request.headers.set('X-MathVision-Web', client);
    request.headers.delete('Authorization');
    const session = request.url === '/auth/logout' ? request._logoutSession : id;
    if (session) request.headers.set('X-MathVision-Session', session);
    else request.headers.delete('X-MathVision-Session');
    return request;
  }, error => { throw error; }, { synchronous: true });
  apiClient.interceptors.response.use(response => {
    if ((response.config as SessionRequest)._identity !== getSessionId()) throw new axios.CanceledError('Phiên đăng nhập đã thay đổi.');
    return response;
  }, (error: AxiosError) => {
    const request = error.config as SessionRequest | undefined;
    if (request?._identity !== undefined && request._identity !== getSessionId()) throw new axios.CanceledError('Phiên đăng nhập đã thay đổi.');
    if (request?._identity && !request.signal?.aborted && request.url !== '/me'
        && !request.url?.startsWith('/auth/') && error.response?.status === 401) {
      clearSession();
      events.forEach(notify => notify());
    }
    throw error;
  });

  // Serialize cookie-issuing calls across tabs. The first successful login seeds the browser cookie.
  const exclusive = async <T,>(action: () => Promise<T>): Promise<T> =>
    typeof navigator !== 'undefined' && navigator.locks ? await navigator.locks.request(key, action) : action();
  function establish(path: string, body: object, config?: AxiosRequestConfig & { _identity?: string | null },
                     isCurrent: () => boolean = () => !config?.signal?.aborted) {
    return exclusive(async () => {
      if (!isCurrent()) throw new axios.CanceledError('Phiên đăng nhập đã thay đổi.');
      const { data } = await apiClient.post<{ sessionId: string }>(path, body, config);
      if (!isCurrent()) throw new axios.CanceledError('Phiên đăng nhập đã thay đổi.');
      if (!data.sessionId) throw new Error('Phản hồi xác thực không hợp lệ.');
      documentSession = data.sessionId;
      storage()?.setItem(key, data.sessionId);
      return data.sessionId;
    });
  }

  async function logout() {
    const id = getSessionId();
    if (documentSession !== id) return;
    if (!id) return;
    if (client === 'portal') clearSession();
    return exclusive(async () => {
      try {
        const request = { timeout: 2000, _logoutSession: id };
        await apiClient.post('/auth/logout', {}, request);
      } catch { /* Keep local sign-out available when the server is unreachable. */ }
      finally { if (client !== 'portal' && documentSession === id) clearSession(); }
    });
  }

  return {
    apiClient, establish, logout, getSessionId, clearSession,
    hasSession: () => getSessionId() !== null,
    onExpired(notify: () => void) { events.add(notify); },
    onExternalChange(cleanup: () => void | Promise<void>) {
      externalChanges.add(cleanup);
      return () => { externalChanges.delete(cleanup); };
    },
  };
}
