import axios from 'axios';
import { apiClient } from './apiClient';
import { appConfig } from '../../config/runtime';
import { tokenStore } from './tokenStore';
import type { AdminUserResponse, LoginResponse } from '../../types';

let attempt = 0;
function requireAdmin(user: AdminUserResponse) {
  if (user.role !== 'ADMIN' || user.active !== true) {
    throw Object.assign(new Error('Tài khoản không có quyền quản trị hoặc đã bị khóa.'), { code: 'ROLE_FORBIDDEN' });
  }
  return user;
}
async function establish(path: string, body: object): Promise<AdminUserResponse> {
  const current = ++attempt;
  tokenStore.clearTokens();
  try {
    const { data } = await apiClient.post<LoginResponse>(path, body);
    if (current !== attempt) throw new Error('Phiên đăng nhập đã thay đổi.');
    if (!data.accessToken || !data.refreshToken) throw new Error('Phản hồi xác thực không hợp lệ.');
    tokenStore.setTokens(data.accessToken, data.refreshToken);
    const user = await authService.getMe();
    if (current !== attempt) throw new Error('Phiên đăng nhập đã thay đổi.');
    return user;
  } catch (error) {
    if (current === attempt) tokenStore.clearTokens();
    throw error;
  }
}
export const authService = {
  login(email: string, password: string) {
    return establish('/auth/login', { email: email.trim().toLowerCase(), password });
  },
  exchangeSsoTicket(code: string) {
    return establish('/auth/sso/exchange', { code, targetApp: 'ADMIN' });
  },
  async getMe(): Promise<AdminUserResponse> {
    const token = tokenStore.getAccessToken();
    if (token && /^(mock|demo)[_-]/i.test(token)) throw new Error('Phiên thử nghiệm không có quyền quản trị. Vui lòng đăng nhập lại.');
    const { data } = await apiClient.get<AdminUserResponse>('/me');
    return requireAdmin(data);
  },
  cancelPending(clearTokens = true) { attempt++; if (clearTokens) tokenStore.clearTokens(); },
  async logout(): Promise<void> {
    const accessToken = tokenStore.getAccessToken();
    this.cancelPending();
    try {
      if (accessToken) await axios.post(`${appConfig.apiBaseUrl}/auth/logout`, {}, {
        headers: { Authorization: `Bearer ${accessToken}` }, timeout: 5000,
      });
    } catch { /* Local logout completes even when the backend is unavailable. */ }
  },
};
