import { apiClient } from './apiClient';
import { tokenStore, adminSession } from './tokenStore';
import type { AdminUserResponse } from '../../types';

let attempt = 0;
function requireAdmin(user: AdminUserResponse) {
  if (user.role !== 'ADMIN' || user.active !== true) {
    throw Object.assign(new Error('Tài khoản không có quyền quản trị hoặc đã bị khóa.'), { code: 'ROLE_FORBIDDEN' });
  }
  return user;
}
async function establish(path: string, body: object): Promise<AdminUserResponse> {
  const current = ++attempt;
  try {
    await adminSession.establish(path, body, undefined, () => current === attempt);
    if (current !== attempt) throw new Error('Phiên đăng nhập đã thay đổi.');
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
    const { data } = await apiClient.get<AdminUserResponse>('/me');
    return requireAdmin(data);
  },
  cancelPending(clearTokens = true) { attempt++; if (clearTokens) tokenStore.clearTokens(); },
  async logout(): Promise<void> {
    this.cancelPending(false);
    await adminSession.logout();
  },
};
