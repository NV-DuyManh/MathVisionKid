import apiClient from './apiClient';

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  user: any; // User type
}

export const authApi = {
  login: async (credentials: any): Promise<LoginResponse> => {
    const response = await apiClient.post('/auth/login', credentials);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
  },

  getMe: async (): Promise<any> => {
    const response = await apiClient.get('/me');
    return response.data;
  },
};
