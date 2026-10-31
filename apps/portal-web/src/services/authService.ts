import { apiClient, tokenStore } from './apiClient';
export interface UserProfile {
  userId: string; email: string; role: 'STUDENT' | 'TEACHER' | 'ADMIN';
  displayName: string; active: boolean; gradeLevel?: number;
}
export interface SsoTicketResponse { code: string; expiresIn: number; targetApp: string }
let attempt = 0;
export const authService = {
  async login(email: string, password: string): Promise<UserProfile> {
    const current = ++attempt;
    tokenStore.clearTokens();
    try {
      const { data } = await apiClient.post('/auth/login', { email: email.trim().toLowerCase(), password });
      if (current !== attempt) throw new Error('Phiên đăng nhập đã thay đổi.');
      if (!data.accessToken || !data.refreshToken) throw new Error('Phản hồi xác thực không hợp lệ.');
      tokenStore.setTokens(data.accessToken, data.refreshToken, true);
      const profile = await this.getMe();
      if (current !== attempt) throw new Error('Phiên đăng nhập đã thay đổi.');
      return profile;
    } catch (error) {
      if (current === attempt) tokenStore.clearTokens();
      throw error;
    }
  },
  async getMe(signal?: AbortSignal): Promise<UserProfile> {
    const { data } = await apiClient.get<UserProfile>('/me', { signal });
    if (data.active !== true || !['STUDENT', 'TEACHER', 'ADMIN'].includes(data.role)) {
      throw Object.assign(new Error('Tài khoản không có quyền truy cập hoặc đã bị khóa.'), { response: { status: 403 } });
    }
    return data;
  },
  async requestSsoTicket(targetApp: 'TEACHER' | 'ADMIN', signal?: AbortSignal): Promise<SsoTicketResponse> {
    const { data } = await apiClient.post<SsoTicketResponse>('/auth/sso/ticket', { targetApp }, { signal });
    return data;
  },
  async logout(): Promise<void> {
    attempt++;
    const accessToken = tokenStore.getAccessToken();
    tokenStore.clearTokens();
    try {
      if (accessToken) await apiClient.post('/auth/logout', {}, { headers: { Authorization: `Bearer ${accessToken}` }, timeout: 5000 });
    } catch { /* Local logout completes without waiting for server availability. */ }
  },
};
