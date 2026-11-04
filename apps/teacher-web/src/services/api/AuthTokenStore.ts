const newSessionId = () => globalThis.crypto?.randomUUID?.() || Date.now().toString(36) + Math.random().toString(36);
export const AuthTokenStore = {
  getSessionId: (): string | null => {
    let id = sessionStorage.getItem('teacher_session_id');
    if (!id && (sessionStorage.getItem('accessToken') || sessionStorage.getItem('refreshToken'))) {
      id = newSessionId(); sessionStorage.setItem('teacher_session_id', id);
    }
    return id;
  },
  getAccessToken: (): string | null => {
    return sessionStorage.getItem('accessToken');
  },
  getRefreshToken: (): string | null => {
    return sessionStorage.getItem('refreshToken');
  },
  setTokens: (accessToken: string, refreshToken: string, newSession = false) => {
    if (newSession || !sessionStorage.getItem('teacher_session_id')) sessionStorage.setItem('teacher_session_id', newSessionId());
    sessionStorage.setItem('accessToken', accessToken);
    sessionStorage.setItem('refreshToken', refreshToken);
    if (newSession) window.dispatchEvent(new Event('teacher_auth_changed'));
  },
  clearTokens: () => {
    sessionStorage.removeItem('accessToken');
    sessionStorage.removeItem('refreshToken');
    sessionStorage.removeItem('teacher_session_id');
    window.dispatchEvent(new Event('teacher_auth_changed'));
  },
};
