import React, { createContext, useCallback, useEffect, useState, useRef, ReactNode } from 'react';
import { ActivityIndicator, Text, View, Pressable } from 'react-native';
import { usePathname, useRouter } from 'expo-router';
import axios from 'axios';
import { tokenStorage } from '../services/auth/tokenStorage';
import { sessionEvents } from '../services/auth/sessionEvents';
import apiClient from '../services/api/apiClient';
import { ENV } from '../config/env';
import { workspaceOrigin } from '../config/workspaceOrigin.web';
import { RecognitionService } from '../features/recognition/api/RecognitionService';
import { recognitionDraftStore } from '../features/recognition/state/recognitionDraftStore';
import { recognitionAnalyticsStore } from '../features/recognition/analytics/recognitionAnalyticsStore';
import { COLORS, FONTS } from '../constants/theme';
interface AuthContextType {
  user: any; isAuthenticated: boolean; isLoading: boolean;
  login: (credentials: any) => Promise<void>; logout: () => Promise<void>;
}
export const AuthContext = createContext<AuthContextType | undefined>(undefined);
function studentProfile(profile: any) {
  const name = profile.displayName || profile.name || 'Học sinh';
  return { id: profile.id || profile.userId, userId: profile.userId || profile.id, role: profile.role, active: true,
    name: typeof name === 'string' && !name.includes('@') ? name : 'Học sinh',
    grade: profile.gradeLevel || profile.grade, gradeLevel: profile.gradeLevel || profile.grade };
}
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [failure, setFailure] = useState<string | null>(null);
  const revision = useRef(0);
  const router = useRouter();
  const pathname = usePathname();
  const portal = typeof window !== 'undefined' && /^\/(?:study|learn)(?:\/|$)/.test(window.location.pathname);
  const setSessionUser = useCallback((profile: any) => {
    RecognitionService.clearCache();
    recognitionAnalyticsStore.setUserScope(profile?.id || profile?.userId);
    setUser(profile);
  }, []);
  useEffect(() => {
    const revalidate = (event: PageTransitionEvent) => {
      if (!event.persisted) return;
      void Promise.all([tokenStorage.getAccessToken(), tokenStorage.getRefreshToken()]).then(([access, refresh]) => {
        if (portal && !access && !refresh) window.location.replace('/');
        else window.location.reload();
      });
    };
    window.addEventListener('pageshow', revalidate);
    return () => window.removeEventListener('pageshow', revalidate);
  }, [portal]);
  useEffect(() => {
    let active = true;
    const current = revision.current;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    const restore = async () => {
      try {
        const [access, refresh] = await Promise.all([tokenStorage.getAccessToken(), tokenStorage.getRefreshToken()]);
        if (!active || current !== revision.current) return;
        if (!access && !refresh) { if (portal) window.location.replace(window.performance?.getEntriesByType?.('navigation').some(entry => (entry as PerformanceNavigationTiming).type === 'back_forward') ? '/' : '/login'); return; }
        const { data } = await apiClient.get('/me', { signal: controller.signal, timeout: 15000 });
        if (!active || current !== revision.current) return;
        if (data.role !== 'STUDENT' || data.active !== true) {
          await tokenStorage.clearTokens();
          delete apiClient.defaults.headers.common.Authorization;
          if (portal) window.location.replace('/access-denied');
          return;
        }
        const profile = studentProfile(data);
        await tokenStorage.saveUser(profile);
        if (active && current === revision.current) setSessionUser(profile);
      } catch (error: any) {
        if (!active || current !== revision.current) return;
        await tokenStorage.clearTokens();
        delete apiClient.defaults.headers.common.Authorization;
        setFailure(error?.response ? 'Phiên đăng nhập không còn hợp lệ. Vui lòng đăng nhập lại.' : 'Chưa kết nối được máy chủ. Vui lòng kiểm tra kết nối và đăng nhập lại.');
        if (portal) window.location.replace(error?.response ? '/login?session=expired' : '/login?connection=failed');
      } finally { clearTimeout(timer); if (active && current === revision.current) setIsLoading(false); }
    };
    void restore();
    const unsubscribe = sessionEvents.subscribe(reason => {
      revision.current++;
      setSessionUser(null);
      setIsLoading(false);
      if (portal) window.location.replace(reason === 'forbidden' ? '/access-denied' : '/session-expired');
      else router.replace('/login');
    });
    return () => { active = false; unsubscribe(); controller.abort(); clearTimeout(timer); };
  }, [setSessionUser, portal, router]);
  useEffect(() => {
    if (!portal && !isLoading && !user && pathname !== '/login') router.replace('/login');
  }, [portal, isLoading, user, pathname, router]);
  useEffect(() => {
    if (portal && pathname === '/login' && user) router.replace('/(tabs)');
  }, [portal, pathname, user, router]);
  const login = async (credentials: any) => {
    const current = ++revision.current;
    setFailure(null);
    setSessionUser(null);
    recognitionDraftStore.clearDraft();
    await tokenStorage.clearTokens();
    delete apiClient.defaults.headers.common.Authorization;
    try {
      const { data } = await apiClient.post('/auth/login', credentials, { timeout: 15000 });
      if (current !== revision.current) throw new Error('Phiên đăng nhập đã thay đổi.');
      if (!data.accessToken || !data.refreshToken) throw new Error('Phản hồi xác thực không hợp lệ.');
      // Verify fresh credentials without persisting a Teacher/Admin session in Student storage.
      const authorization = { Authorization: `Bearer ${data.accessToken}` };
      const { data: verified } = await axios.get(`${ENV.API_BASE_URL}/me`, { headers: authorization, timeout: 15000 });
      if (current !== revision.current) throw new Error('Phiên đăng nhập đã thay đổi.');
      if (!['STUDENT', 'TEACHER', 'ADMIN'].includes(verified.role) || verified.active !== true) {
        if (portal) window.location.replace('/access-denied');
        throw Object.assign(new Error('Tài khoản chưa được phép học.'), { response: { status: 403 } });
      }
      if (verified.role === 'TEACHER' || verified.role === 'ADMIN') {
        const origin = workspaceOrigin(verified.role);
        const { data: ticket } = await axios.post(`${ENV.API_BASE_URL}/auth/sso/ticket`, { targetApp: verified.role },
          { headers: authorization, timeout: 15000 });
        if (current !== revision.current) throw new Error('Phiên đăng nhập đã thay đổi.');
        if (ticket?.targetApp !== verified.role || typeof ticket.code !== 'string' ||
            !/^mvk_sso_[a-f0-9]{64}$/.test(ticket.code) || !(ticket.expiresIn > 0)) {
          throw Object.assign(new Error('Chưa chuyển được tới không gian làm việc. Vui lòng đăng nhập lại.'), { code: 'VALIDATION_ERROR' });
        }
        window.location.replace(`${origin}/auth/continue#sso=${encodeURIComponent(ticket.code)}`);
        return;
      }
      await tokenStorage.saveTokens(data.accessToken, data.refreshToken);
      if (current !== revision.current) throw new Error('Phiên đăng nhập đã thay đổi.');
      const profile = studentProfile(verified);
      await tokenStorage.saveUser(profile);
      if (current !== revision.current) throw new Error('Phiên đăng nhập đã thay đổi.');
      setSessionUser(profile);
      router.replace('/(tabs)' as any);
    } catch (error) {
      if (current === revision.current) { await tokenStorage.clearTokens(); delete apiClient.defaults.headers.common.Authorization; }
      throw error;
    }
  };
  const logout = async () => {
    const current = ++revision.current;
    setSessionUser(null);
    recognitionDraftStore.clearDraft();
    const accessToken = await tokenStorage.getAccessToken();
    if (current !== revision.current) return;
    await tokenStorage.clearTokens();
    delete apiClient.defaults.headers.common.Authorization;
    if (accessToken) void axios.post(`${ENV.API_BASE_URL}/auth/logout`, {}, {
      headers: { Authorization: `Bearer ${accessToken}` }, timeout: 5000,
    }).catch(() => {});
    if (portal) window.location.replace('/logout?source=student');
    else router.replace('/login');
  };
  return <AuthContext.Provider value={{ user, isAuthenticated: user?.role === 'STUDENT' && user.active === true, isLoading, login, logout }}>
    {(user && (!portal || pathname !== '/login')) || (!portal && !isLoading && pathname === '/login') ? children : <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 16, padding: 24, backgroundColor: COLORS.background }}>
      {failure ? <><Text style={{ fontFamily: FONTS.regular, color: COLORS.textSecondary }}>{failure}</Text>
        <Pressable accessibilityRole="button" onPress={() => window.location.replace('/login')}><Text>Đăng nhập lại</Text></Pressable></> :
        <><ActivityIndicator color={COLORS.primary} /><Text style={{ fontFamily: FONTS.regular, color: COLORS.textSecondary }}>Đang xác minh tài khoản…</Text></>}
    </View>}
  </AuthContext.Provider>;
};
