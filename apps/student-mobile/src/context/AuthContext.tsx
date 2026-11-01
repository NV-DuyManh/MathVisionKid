import React, { createContext, useState, useEffect, useRef, ReactNode } from 'react';
import { tokenStorage } from '../services/auth/tokenStorage';
import { requireStudent } from '../services/auth/studentAccess';
import { sessionEvents } from '../services/auth/sessionEvents';
import { authApi } from '../services/api/authApi';
import apiClient from '../services/api/apiClient';
import { useRouter } from 'expo-router';
import { RecognitionService } from '../features/recognition/api/RecognitionService';
import { recognitionDraftStore } from '../features/recognition/state/recognitionDraftStore';
import { recognitionAnalyticsStore } from '../features/recognition/analytics/recognitionAnalyticsStore';
interface AuthContextType {
  user: any; isAuthenticated: boolean; isLoading: boolean; sessionError?: string | null;
  login: (credentials: any) => Promise<void>; logout: () => Promise<void>;
}
export const AuthContext = createContext<AuthContextType | undefined>(undefined);
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const revision = useRef(0);
  const { replace } = useRouter();
  const setSessionUser = (profile: any) => {
    RecognitionService.clearCache();
    recognitionDraftStore.clearDraft();
    recognitionAnalyticsStore.setUserScope(profile?.id || profile?.userId);
    setUser(profile);
  };
  useEffect(() => {
    let active = true;
    const current = revision.current;
    void (async () => {
      try {
        const access = await tokenStorage.getAccessToken();
        const refresh = await tokenStorage.getRefreshToken();
        if (!active || current !== revision.current) return;
        if (access || refresh) {
          const profile = requireStudent(await authApi.getMe());
          if (!active || current !== revision.current) return;
          await tokenStorage.saveUser(profile);
          if (active && current === revision.current) setSessionUser(profile);
        }
      } catch (error: any) {
        if (active && current === revision.current) {
          await tokenStorage.clearTokens();
          delete apiClient.defaults.headers.common.Authorization;
          setSessionUser(null);
          setSessionError(error?.code === 'STUDENT_ACCESS_DENIED' ? error.message
            : error?.response ? 'Phiên đăng nhập không còn hợp lệ. Vui lòng đăng nhập lại.'
            : 'Chưa thể xác minh phiên đăng nhập. Vui lòng kiểm tra kết nối và đăng nhập lại.');
        }
      } finally { if (active && current === revision.current) setIsLoading(false); }
    })();
    const unsubscribe = sessionEvents.subscribe(reason => {
      revision.current++;
      setSessionUser(null);
      setIsLoading(false);
      setSessionError(reason === 'forbidden' ? 'Tài khoản không còn quyền truy cập ứng dụng học sinh. Vui lòng đăng nhập qua cổng MathVision Kids trên trình duyệt.' : 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
      replace('/login');
    });
    return () => { active = false; unsubscribe(); };
  }, [replace]);
  const login = async (credentials: any) => {
    setSessionError(null);
    const current = ++revision.current;
    setSessionUser(null);
    await tokenStorage.clearTokens();
    delete apiClient.defaults.headers.common.Authorization;
    try {
      const data = await authApi.login(credentials);
      if (current !== revision.current) throw new Error('Phiên đăng nhập đã thay đổi.');
      await tokenStorage.saveTokens(data.accessToken, data.refreshToken);
      const profile = requireStudent(data.user || await authApi.getMe());
      if (current !== revision.current) throw new Error('Phiên đăng nhập đã thay đổi.');
      await tokenStorage.saveUser(profile);
      if (current !== revision.current) throw new Error('Phiên đăng nhập đã thay đổi.');
      setSessionUser(profile);
      replace('/(tabs)' as any);
    } catch (error) {
      if (current === revision.current) {
        await tokenStorage.clearTokens();
        delete apiClient.defaults.headers.common.Authorization;
        setSessionUser(null);
      }
      throw error;
    }
  };
  const logout = async () => {
    const current = ++revision.current;
    setSessionUser(null);
    const accessToken = await tokenStorage.getAccessToken();
    if (current !== revision.current) return;
    const pending = authApi.logout(accessToken);
    await tokenStorage.clearTokens();
    delete apiClient.defaults.headers.common.Authorization;
    if (current === revision.current) replace('/login');
    await pending;
  };
  return <AuthContext.Provider value={{ user, isAuthenticated: user?.role === 'STUDENT' && user.active === true, isLoading, sessionError, login, logout }}>{children}</AuthContext.Provider>;
};
