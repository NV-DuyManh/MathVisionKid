const ACCESS = 'portal_access_token', REFRESH = 'portal_refresh_token', USER = 'mathvision_student_web_user_v1', SESSION = 'portal_session_id';
function identity() {
  if (typeof window === 'undefined') return null;
  let id = window.sessionStorage.getItem(SESSION);
  if (!id && (window.sessionStorage.getItem(ACCESS) || window.sessionStorage.getItem(REFRESH))) {
    id = globalThis.crypto?.randomUUID?.() || Date.now().toString(36) + Math.random().toString(36);
    window.sessionStorage.setItem(SESSION, id);
  }
  return id;
}
export const tokenStorage = {
  async getSessionId() { return identity(); },
  async saveTokens(access: string, refresh: string, expected?: string | null) {
    if (typeof window === 'undefined' || (expected != null && expected !== identity())) return;
    window.sessionStorage.setItem(ACCESS, access); window.sessionStorage.setItem(REFRESH, refresh); identity();
  },
  async clearTokens() {
    if (typeof window === 'undefined') return;
    for (const key of [ACCESS, REFRESH, USER, SESSION]) window.sessionStorage.removeItem(key);
    window.dispatchEvent(new Event('portal_auth_changed'));
  },
  async getAccessToken() { return typeof window === 'undefined' ? null : window.sessionStorage.getItem(ACCESS); },
  async getRefreshToken() { return typeof window === 'undefined' ? null : window.sessionStorage.getItem(REFRESH); },
  async saveUser(user: any) { if (typeof window !== 'undefined') window.sessionStorage.setItem(USER, JSON.stringify(user)); },
  async getUser() { try { const value = typeof window === 'undefined' ? null : window.sessionStorage.getItem(USER); return value ? JSON.parse(value) : null; } catch { return null; } },
};
