import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { tokenStorage } from '../services/auth/tokenStorage';
import { authApi, getMockStudentUser } from '../services/api/authApi';
import apiClient from '../services/api/apiClient';
import { useRouter } from 'expo-router';
import { RecognitionService } from '../features/recognition/api/RecognitionService';
import { recognitionDraftStore } from '../features/recognition/state/recognitionDraftStore';
import { recognitionAnalyticsStore } from '../features/recognition/analytics/recognitionAnalyticsStore';

interface AuthContextType {
  user: any;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: any) => Promise<void>;
  loginWithGoogle: (credential: string, gradeLevel?: number) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<any>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter();
  const setSessionUser = (userData: any) => {
    RecognitionService.clearCache();
    recognitionAnalyticsStore.setUserScope(userData?.id || userData?.userId || userData?.email);
    setUser(userData);
  };

  useEffect(() => {
    const restoreSession = async () => {
      try {
        const token = await tokenStorage.getAccessToken();
        const savedUser = await tokenStorage.getUser();

        if (token) {
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          try {
            const userData = await authApi.getMe();
            setSessionUser(userData);
            await tokenStorage.saveUser(userData);
            setIsAuthenticated(true);
          } catch (apiErr) {
            if (savedUser) {
              setSessionUser(savedUser);
              setIsAuthenticated(true);
            } else {
              throw apiErr;
            }
          }
        } else {
          // Attempt refresh if refresh token exists
          const refreshToken = await tokenStorage.getRefreshToken();
          if (refreshToken) {
            try {
              const userData = await authApi.getMe();
              setSessionUser(userData);
              await tokenStorage.saveUser(userData);
              setIsAuthenticated(true);
            } catch {
              if (savedUser) {
                setSessionUser(savedUser);
                setIsAuthenticated(true);
              }
            }
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
    const token = data.accessToken;
    await tokenStorage.saveTokens(token, data.refreshToken);
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;

    let userData = data.user;
    if (!userData) {
      try {
        userData = await authApi.getMe();
      } catch {
        userData = getMockStudentUser(credentials.email);
      }
    }
    await tokenStorage.saveUser(userData);
    setSessionUser(userData);
    setIsAuthenticated(true);
    router.replace('/(tabs)' as any);
  };

  const loginWithGoogle = async (credential: string, gradeLevel?: number) => {
    const data = await authApi.loginWithGoogle(credential, gradeLevel);
    const token = data.accessToken;
    await tokenStorage.saveTokens(token, data.refreshToken);
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;

    try {
      const userData = data.user ?? await authApi.getMe();
      if (userData.role?.toUpperCase().replace('ROLE_', '') !== 'STUDENT') {
        throw new Error('Tài khoản này không thuộc ứng dụng học sinh.');
      }
      await tokenStorage.saveUser(userData);
      setSessionUser(userData);
      setIsAuthenticated(true);
      router.replace('/(tabs)' as any);
    } catch (error) {
      await tokenStorage.clearTokens();
      delete apiClient.defaults.headers.common['Authorization'];
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (e) {
      console.log('Backend logout failed, proceeding with local logout', e);
    }
    await tokenStorage.clearTokens();
    RecognitionService.clearCache();
    recognitionDraftStore.clearDraft();
    delete apiClient.defaults.headers.common['Authorization'];
    setSessionUser(null);
    setIsAuthenticated(false);
    router.replace('/login');
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isLoading, login, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
