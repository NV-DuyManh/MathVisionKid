import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { tokenStorage } from '../services/auth/tokenStorage';
import { authApi } from '../services/api/authApi';
import apiClient from '../services/api/apiClient';
import { useRouter } from 'expo-router';

interface AuthContextType {
  user: any;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: any) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<any>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter();

  useEffect(() => {
    const restoreSession = async () => {
      try {
        const token = await tokenStorage.getAccessToken();
        if (token) {
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          const userData = await authApi.getMe();
          setUser(userData);
          setIsAuthenticated(true);
        } else {
          // Attempt refresh if refresh token exists
          const refreshToken = await tokenStorage.getRefreshToken();
          if (refreshToken) {
            // we will let the first API call trigger the interceptor or we can just try to fetch me
            const userData = await authApi.getMe();
            setUser(userData);
            setIsAuthenticated(true);
          }
        }
      } catch (e) {
        console.log('Session restore failed', e);
        await tokenStorage.clearTokens();
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  const login = async (credentials: any) => {
    const data = await authApi.login(credentials);
    await tokenStorage.saveTokens(data.accessToken, data.refreshToken);
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${data.accessToken}`;
    const userData = await authApi.getMe();
    setUser(userData);
    setIsAuthenticated(true);
    router.replace('/');
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (e) {
      console.log('Backend logout failed, proceeding with local logout', e);
    }
    await tokenStorage.clearTokens();
    delete apiClient.defaults.headers.common['Authorization'];
    setUser(null);
    setIsAuthenticated(false);
    router.replace('/login');
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
