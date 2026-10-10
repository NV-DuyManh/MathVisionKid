const ACCESS_TOKEN_KEY = 'portal_access_token';
const REFRESH_TOKEN_KEY = 'portal_refresh_token';
const USER_DATA_KEY = 'mathvision_student_web_user_v1';

export const tokenStorage = {
  async saveTokens(accessToken: string, refreshToken: string) {
    if (typeof window === 'undefined') return;
    window.sessionStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    window.sessionStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  },

  async clearTokens() {
    if (typeof window === 'undefined') return;
    window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    window.sessionStorage.removeItem(REFRESH_TOKEN_KEY);
    window.sessionStorage.removeItem(USER_DATA_KEY);
    window.dispatchEvent(new Event('portal_auth_changed'));
  },

  async getAccessToken() {
    try {
      return typeof window === 'undefined' ? null : window.sessionStorage.getItem(ACCESS_TOKEN_KEY);
    } catch {
      return null;
    }
  },

  async getRefreshToken() {
    try {
      return typeof window === 'undefined' ? null : window.sessionStorage.getItem(REFRESH_TOKEN_KEY);
    } catch {
      return null;
    }
  },

  async saveUser(user: any) {
    if (typeof window === 'undefined') return;
    window.sessionStorage.setItem(USER_DATA_KEY, JSON.stringify(user));
  },

  async getUser() {
    try {
      const item = typeof window === 'undefined' ? null : window.sessionStorage.getItem(USER_DATA_KEY);
      return item ? JSON.parse(item) : null;
    } catch {
      return null;
    }
  },
};
