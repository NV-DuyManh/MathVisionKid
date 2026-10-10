/* eslint-disable import/no-named-as-default-member */
import axios from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';
import { appConfig } from '../config/runtime';

const API_BASE_URL = appConfig.apiBaseUrl;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const tokenStore = {
  getAccessToken(): string | null {
    return sessionStorage.getItem('portal_access_token');
  },
  setTokens(accessToken: string, refreshToken: string, newSession = false) {
    sessionStorage.setItem('portal_access_token', accessToken);
    sessionStorage.setItem('portal_refresh_token', refreshToken);
    if (newSession) window.dispatchEvent(new Event('portal_auth_changed'));
  },
  getRefreshToken(): string | null {
    return sessionStorage.getItem('portal_refresh_token');
  },
  clearTokens() {
    sessionStorage.removeItem('portal_access_token');
    sessionStorage.removeItem('portal_refresh_token');
    window.dispatchEvent(new Event('portal_auth_changed'));
  },
  hasTokens(): boolean {
    return !!sessionStorage.getItem('portal_access_token');
  },
};

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStore.getAccessToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && !originalRequest.signal?.aborted) {
      if (originalRequest.url?.includes('/auth/login') || originalRequest.url?.includes('/auth/refresh')) {
        return Promise.reject(error);
      }

      originalRequest._retry = true;
      const refreshToken = tokenStore.getRefreshToken();
      if (!refreshToken) {
        tokenStore.clearTokens();
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, { refreshToken }, {
          signal: originalRequest.signal, timeout: 30000,
        });
        if (originalRequest.signal?.aborted || tokenStore.getRefreshToken() !== refreshToken) {
          return Promise.reject(error);
        }
        tokenStore.setTokens(data.accessToken, data.refreshToken);
        originalRequest.headers.Authorization = `Bearer ${data.accessToken}`;
        return apiClient(originalRequest);
      } catch (refreshErr) {
        if (!originalRequest.signal?.aborted && tokenStore.getRefreshToken() === refreshToken) {
          tokenStore.clearTokens();
        }
        return Promise.reject(refreshErr);
      }
    }
    return Promise.reject(error);
  }
);
