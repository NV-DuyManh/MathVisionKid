import React, { createContext, useCallback, useEffect, useState, ReactNode } from 'react';
import { ActivityIndicator, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import axios from 'axios';
import { tokenStorage } from '../services/auth/tokenStorage';
import apiClient from '../services/api/apiClient';
import { ENV } from '../config/env';
import { RecognitionService } from '../features/recognition/api/RecognitionService';
import { recognitionDraftStore } from '../features/recognition/state/recognitionDraftStore';
import { recognitionAnalyticsStore } from '../features/recognition/analytics/recognitionAnalyticsStore';
import { COLORS, FONTS } from '../constants/theme';

interface AuthContextType {
  user: any;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: any) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

function studentProfile(profile: any) {
  const name = profile.displayName || profile.name || 'Học sinh';
  return {
    id: profile.id || profile.userId,
    userId: profile.userId || profile.id,
    role: profile.role,
    name: typeof name === 'string' && !name.includes('@') ? name : 'Học sinh',
    grade: profile.gradeLevel || profile.grade,
    gradeLevel: profile.gradeLevel || profile.grade,
  };
}

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const setSessionUser = useCallback((profile: any) => {
    RecognitionService.clearCache();
    recognitionAnalyticsStore.setUserScope(profile?.id || profile?.userId);
    setUser(profile);
  }, []);

  useEffect(() => {
    let active = true;
    const restoreSession = async () => {
      try {
        const [accessToken, refreshToken] = await Promise.all([
          tokenStorage.getAccessToken(), tokenStorage.getRefreshToken(),
        ]);
        if (!active) return;
        if (!accessToken && !refreshToken) {
          window.location.replace('/login');
          return;
        }
        // The shared client refreshes expired tokens; cached profiles never grant access.
        const { data } = await apiClient.get('/me');
        if (!active) return;
        if (data.role !== 'STUDENT' || data.active === false) {
          window.location.replace('/access-denied');
          return;
        }
        const profile = studentProfile(data);
        await tokenStorage.saveUser(profile);
        if (active) setSessionUser(profile);
      } catch {
        if (!active) return;
        await tokenStorage.clearTokens();
        delete apiClient.defaults.headers.common.Authorization;
        window.location.replace('/login');
      } finally {
        if (active) setIsLoading(false);
      }
    };
    void restoreSession();
    return () => { active = false; };
  }, [setSessionUser]);

  const login = async (credentials: any) => {
    try {
      const { data } = await apiClient.post('/auth/login', credentials);
      await tokenStorage.saveTokens(data.accessToken, data.refreshToken);
      const { data: profileData } = await apiClient.get('/me');
      if (profileData.role !== 'STUDENT' || profileData.active === false) {
        window.location.replace('/access-denied');
        return;
      }
      const profile = studentProfile(profileData);
      await tokenStorage.saveUser(profile);
      setSessionUser(profile);
      router.replace('/(tabs)' as any);
    } catch (error) {
      await tokenStorage.clearTokens();
      delete apiClient.defaults.headers.common.Authorization;
      throw error;
    }
  };

  const logout = async () => {
    try {
      const accessToken = await tokenStorage.getAccessToken();
      if (accessToken) {
        // A rejected logout must not start the shared client's token refresh queue.
        await axios.post(`${ENV.API_BASE_URL}/auth/logout`, {}, {
          headers: { Authorization: `Bearer ${accessToken}` }, timeout: 5000,
        });
      }
    } catch {
      // Local logout completes even if the server is unavailable or the token expired.
    } finally {
      await tokenStorage.clearTokens();
      RecognitionService.clearCache();
      recognitionDraftStore.clearDraft();
      delete apiClient.defaults.headers.common.Authorization;
      setSessionUser(null);
      window.location.replace('/logout?source=student');
    }
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout }}>
      {user ? children : <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 16, backgroundColor: COLORS.background }}>
        <ActivityIndicator color={COLORS.primary} />
        <Text style={{ fontFamily: FONTS.regular, color: COLORS.textSecondary }}>Đang mở bài học cho em…</Text>
      </View>}
    </AuthContext.Provider>
  );
};
