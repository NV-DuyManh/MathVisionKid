import { apiClient } from './apiClient';
import { tokenStore } from './tokenStore';
import type { AdminUserResponse, LoginResponse } from '../../types';

export const authService = {
  async login(email: string, password: string): Promise<AdminUserResponse> {
    const { data: loginData } = await apiClient.post<LoginResponse>('/auth/login', {
      email: email.trim().toLowerCase(),
      password,
    });

    tokenStore.setTokens(loginData.accessToken, loginData.refreshToken);

    try {
      const { data: userData } = await apiClient.get<AdminUserResponse>('/me');
      if (userData.role !== 'ADMIN') {
        tokenStore.clearTokens();
        throw new Error('Tài khoản này không có quyền truy cập Cổng Quản Trị Hệ Thống (Yêu cầu vai trò ADMIN).');
      }
      return userData;
    } catch (err) {
      tokenStore.clearTokens();
      throw err;
    }
  },

  async exchangeSsoTicket(code: string): Promise<AdminUserResponse> {
    const { data: exchangeData } = await apiClient.post<LoginResponse>('/auth/sso/exchange', {
      code,
      targetApp: 'ADMIN',
    });

    tokenStore.setTokens(exchangeData.accessToken, exchangeData.refreshToken);

    try {
      const { data: userData } = await apiClient.get<AdminUserResponse>('/me');
      if (userData.role !== 'ADMIN') {
        tokenStore.clearTokens();
        throw new Error('Tài khoản này không có quyền truy cập Cổng Quản Trị Hệ Thống (Yêu cầu vai trò ADMIN).');
      }
      return userData;
    } catch (err) {
      tokenStore.clearTokens();
      throw err;
    }
  },

  async getMe(): Promise<AdminUserResponse> {
    const { data } = await apiClient.get<AdminUserResponse>('/me');
    return data;
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // Ignore errors on logout
    } finally {
      tokenStore.clearTokens();
    }
  },
};
