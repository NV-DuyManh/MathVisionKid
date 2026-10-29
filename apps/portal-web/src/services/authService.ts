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

export interface PasswordResetResponse {
  message: string;
}

export interface RegisterPayload {
  email: string;
  displayName: string;
  password: string;
  role: 'STUDENT' | 'TEACHER';
  gender: 'MALE' | 'FEMALE' | 'OTHER' | 'PREFER_NOT_TO_SAY';
  phoneNumber: string;
  gradeLevel?: number;
}

export const authService = {
  async login(email: string, password: string): Promise<UserProfile> {
    const { data } = await apiClient.post('/auth/login', { email, password });
    tokenStore.setTokens(data.accessToken, data.refreshToken, true);
    const profile = await this.getMe();
    return profile;
  },

  async loginWithGoogle(credential: string, role?: 'STUDENT' | 'TEACHER', gradeLevel?: number): Promise<UserProfile> {
    const { data } = await apiClient.post('/auth/google', { credential, role, gradeLevel });
    tokenStore.setTokens(data.accessToken, data.refreshToken, true);
    return this.getMe();
  },

  async loginWithFacebook(credential: string, role?: 'STUDENT' | 'TEACHER', gradeLevel?: number): Promise<UserProfile> {
    const { data } = await apiClient.post('/auth/facebook', { credential, role, gradeLevel });
    tokenStore.setTokens(data.accessToken, data.refreshToken, true);
    return this.getMe();
  },

  async register(payload: RegisterPayload): Promise<PasswordResetResponse> {
    const { data } = await apiClient.post<PasswordResetResponse>('/auth/register', payload);
    return data;
  },

  async requestPasswordReset(email: string): Promise<PasswordResetResponse> {
    const { data } = await apiClient.post<PasswordResetResponse>('/auth/password-reset/request', { email });
    return data;
  },

  async confirmPasswordReset(email: string, code: string, newPassword: string): Promise<PasswordResetResponse> {
    const { data } = await apiClient.post<PasswordResetResponse>('/auth/password-reset/confirm', { email, code, newPassword });
    return data;
  },

  async getMe(signal?: AbortSignal): Promise<UserProfile> {
    const { data } = await apiClient.get<UserProfile>('/me', { signal });
    return data;
  },

  async requestSsoTicket(targetApp: 'TEACHER' | 'ADMIN', signal?: AbortSignal): Promise<SsoTicketResponse> {
    const { data } = await apiClient.post<SsoTicketResponse>('/auth/sso/ticket', { targetApp }, { signal });
    return data;
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // Ignore network errors on logout
    } finally {
      tokenStore.clearTokens();
      if (import.meta.env.VITE_FIREBASE_API_KEY) {
        try {
          const { signOutFacebook } = await import('./facebookAuth');
          await signOutFacebook();
        } catch {
          // The application session is already cleared.
        }
      }
    }
  },
};
