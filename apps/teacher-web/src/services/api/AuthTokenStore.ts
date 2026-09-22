export const AuthTokenStore = {
  getAccessToken: (): string | null => {
    return sessionStorage.getItem('accessToken');
  },
  getRefreshToken: (): string | null => {
    return sessionStorage.getItem('refreshToken');
  },
  setTokens: (accessToken: string, refreshToken: string) => {
    sessionStorage.setItem('accessToken', accessToken);
    sessionStorage.setItem('refreshToken', refreshToken);
  },
  clearTokens: () => {
    sessionStorage.removeItem('accessToken');
    sessionStorage.removeItem('refreshToken');
  },
};
