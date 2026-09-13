import { apiClient } from './apiClient';
import { tokenStore } from './tokenStore';
import type { AdminUserResponse, LoginResponse } from '../../types';

const MOCK_ADMIN: AdminUserResponse = {
  userId: 'u_admin_001',
  email: 'admin.demo@mathvision.local',
  displayName: 'Demo Administrator',
  role: 'ADMIN',
  active: true,
  createdAt: '2026-09-01T00:00:00Z',
  updatedAt: '2026-09-01T00:00:00Z',
};

export const authService = {
  async login(email: string, password: string): Promise<AdminUserResponse> {
    try {
      const { data: loginData } = await apiClient.post<LoginResponse>('/auth/login', {
        email: email.trim().toLowerCase(),
        password,
      });

      tokenStore.setTokens(loginData.accessToken, loginData.refreshToken);

      const { data: userData } = await apiClient.get<AdminUserResponse>('/me');
      if (userData.role !== 'ADMIN') {
        tokenStore.clearTokens();
        throw new Error('Tài khoản này không có quyền truy cập Cổng Quản Trị Hệ Thống (Yêu cầu vai trò ADMIN).');
      }
      return userData;
    } catch (err: any) {
      if (err.code === 'ERR_NETWORK' || !err.response || err.message?.includes('Network Error')) {
        // Fallback for standalone demo when backend is offline
        if (email.trim().toLowerCase() === 'admin.demo@mathvision.local' && password === 'MathVision123!') {
          tokenStore.setTokens('mock-admin-access-token', 'mock-admin-refresh-token');
          return MOCK_ADMIN;
        }
      }
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
    try {
      const { data } = await apiClient.get<AdminUserResponse>('/me');
      return data;
    } catch (err: any) {
      if (err.code === 'ERR_NETWORK' || !err.response || err.message?.includes('Network Error')) {
        if (tokenStore.hasTokens()) {
          return MOCK_ADMIN;
        }
      }
      throw err;
    }
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
