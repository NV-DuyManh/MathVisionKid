const ACCESS = 'mvk_admin_access_token';
const REFRESH = 'mvk_admin_refresh_token';
const SESSION = 'mvk_admin_session_id';
const newId = () => globalThis.crypto?.randomUUID?.() || Date.now().toString(36) + Math.random().toString(36);
export const tokenStore = {
  getAccessToken: () => localStorage.getItem(ACCESS),
  getRefreshToken: () => localStorage.getItem(REFRESH),
  getSessionId(): string | null {
    let id = localStorage.getItem(SESSION);
    if (!id && this.hasTokens()) { id = newId(); localStorage.setItem(SESSION, id); }
    return id;
  },
  setAccessToken(token: string) { localStorage.setItem(ACCESS, token); },
  setRefreshToken(token: string) { localStorage.setItem(REFRESH, token); },
  setTokens(access: string, refresh: string) {
    if (!localStorage.getItem(SESSION)) localStorage.setItem(SESSION, newId());
    localStorage.setItem(ACCESS, access); localStorage.setItem(REFRESH, refresh);
  },
  clearTokens() { localStorage.removeItem(ACCESS); localStorage.removeItem(REFRESH); localStorage.removeItem(SESSION); },
  hasTokens: () => !!(localStorage.getItem(ACCESS) || localStorage.getItem(REFRESH)),
};
