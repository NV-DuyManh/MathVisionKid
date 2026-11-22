import { apiClient, tokenStore, webSession } from './apiClient';
export interface UserProfile {
  userId: string; email: string; role: 'STUDENT' | 'TEACHER' | 'ADMIN';
  displayName: string; active: boolean; gradeLevel?: number;
}
export interface SsoTicketResponse { code: string; expiresIn: number; targetApp: string }
let attempt = 0;
export interface RegisterPayload {
  email: string; displayName: string; password: string; role: 'STUDENT' | 'TEACHER';
  gender: 'MALE' | 'FEMALE' | 'OTHER' | 'PREFER_NOT_TO_SAY'; phoneNumber: string; gradeLevel?: number;
}
async function authenticate(path: string, credentials: object): Promise<UserProfile> {
  const current = ++attempt;
  let established = false;
  try {
    await webSession.establish(path, credentials, undefined, () => current === attempt);
    established = true;
    if (current !== attempt) throw new Error('Phiên đăng nhập đã thay đổi.');
    window.dispatchEvent(new Event('portal_auth_changed'));
    const profile = await authService.getMe();
    if (current !== attempt) throw new Error('Phiên đăng nhập đã thay đổi.');
    return profile;
  } catch (error) {
    if (current === attempt && established) tokenStore.clearTokens();
    throw error;
  }
}
export const authService = {
  async login(email: string, password: string): Promise<UserProfile> {
    return authenticate('/auth/login', { email: email.trim().toLowerCase(), password });
  },
  async loginWithGoogle(credential: string, role?: 'STUDENT' | 'TEACHER', gradeLevel?: number) {
    return authenticate('/auth/google', { credential, role, gradeLevel });
  },
  async loginWithFacebook(credential: string, role?: 'STUDENT' | 'TEACHER', gradeLevel?: number) {
    return authenticate('/auth/facebook', { credential, role, gradeLevel });
  },
  async register(payload: RegisterPayload): Promise<{ message: string }> {
    return (await apiClient.post('/auth/register', payload)).data;
  },
  async requestPasswordReset(email: string): Promise<{ message: string }> {
    return (await apiClient.post('/auth/password-reset/request', { email })).data;
  },
  async confirmPasswordReset(email: string, code: string, newPassword: string): Promise<{ message: string }> {
    return (await apiClient.post('/auth/password-reset/confirm', { email, code, newPassword })).data;
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
    const revocation = webSession.logout();
    window.dispatchEvent(new Event('portal_auth_changed'));
    await revocation;
  },
};
