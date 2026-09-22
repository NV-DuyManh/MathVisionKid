import { apiClient, tokenStore } from './apiClient';

export interface UserProfile {
  userId: string;
  email: string;
  role: 'STUDENT' | 'TEACHER' | 'ADMIN';
  displayName: string;
  active: boolean;
  gradeLevel?: number;
}

export interface SsoTicketResponse {
  code: string;
  expiresIn: number;
  targetApp: string;
}

export const authService = {
  async login(email: string, password: string): Promise<UserProfile> {
    const { data } = await apiClient.post('/auth/login', { email, password });
    tokenStore.setTokens(data.accessToken, data.refreshToken);
    const profile = await this.getMe();
    return profile;
  },

  async getMe(): Promise<UserProfile> {
    const { data } = await apiClient.get<UserProfile>('/me');
    return data;
  },

  async requestSsoTicket(targetApp: 'TEACHER' | 'ADMIN'): Promise<SsoTicketResponse> {
    const { data } = await apiClient.post<SsoTicketResponse>('/auth/sso/ticket', { targetApp });
    return data;
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // Ignore network errors on logout
    } finally {
      tokenStore.clearTokens();
    }
  },
};
