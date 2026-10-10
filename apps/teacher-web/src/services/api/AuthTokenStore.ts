export const AuthTokenStore = {
  getAccessToken: (): string | null => {
    return sessionStorage.getItem('accessToken');
  },
  getRefreshToken: (): string | null => {
    return sessionStorage.getItem('refreshToken');
  },
  setTokens: (accessToken: string, refreshToken: string, newSession = false) => {
    if (newSession) window.dispatchEvent(new Event('teacher_auth_changed'));
    sessionStorage.setItem('accessToken', accessToken);
    sessionStorage.setItem('refreshToken', refreshToken);
  },
  clearTokens: () => {
    sessionStorage.removeItem('accessToken');
    sessionStorage.removeItem('refreshToken');
    window.dispatchEvent(new Event('teacher_auth_changed'));
  },
};
