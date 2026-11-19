import React, { createContext, useCallback, useEffect, useState, useRef, useSyncExternalStore, ReactNode } from 'react';
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
import { imageDraftPersistence } from '../features/recognition/state/imageDraftPersistence';
import { recognitionAnalyticsStore } from '../features/recognition/analytics/recognitionAnalyticsStore';
import { COLORS, FONTS } from '../constants/theme';
interface AuthContextType {
  user: any; isAuthenticated: boolean; isLoading: boolean;
  logout: () => Promise<void>;
  refreshUser?: () => Promise<void>;
  changePassword?: (currentPassword: string, newPassword: string, signal?: AbortSignal) => Promise<void>;
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
  const photoRecovery = useSyncExternalStore(imageDraftPersistence.subscribe, imageDraftPersistence.getSnapshot, imageDraftPersistence.getSnapshot);
  const revision = useRef(0);
  const renderedRevision = revision.current;
  const router = useRouter();
  const pathname = usePathname();
  // The shared export is mounted under /study, while the standalone preview
  // can expose the same public onboarding screen at /welcome or /onboarding.
  // Keep both entry points public so an anonymous student can reach the real
  // login handoff without being held by the protected-route guard.
  const publicWelcome = /^(?:\/(?:study|learn))?\/(?:welcome|onboarding)\/?$/.test(pathname);
  const loginRoute = /^(?:\/(?:study|learn))?\/login\/?$/.test(pathname);
  const portal = typeof window !== 'undefined' && /^\/(?:study|learn)(?:\/|$)/.test(window.location.pathname);
  const setSessionUser = useCallback((profile: any) => {
    const recovery = imageDraftPersistence.activate(profile?.id || profile?.userId);
    RecognitionService.clearCache();
    recognitionAnalyticsStore.setUserScope(profile?.id || profile?.userId);
    setUser(profile);
    return recovery;
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
    let restoring = true;
    const current = revision.current;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    const restore = async () => {
      try {
        const [access, refresh] = await Promise.all([tokenStorage.getAccessToken(), tokenStorage.getRefreshToken()]);
        if (!active || current !== revision.current) return;
        if (!access && !refresh) {
          if (!publicWelcome) {
            if (portal) window.location.replace(loginRoute ? '/login' + window.location.search : '/login');
            else if (!loginRoute) router.replace('/login');
          }
          return;
        }
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
      } finally { restoring = false; clearTimeout(timer); if (active && current === revision.current) setIsLoading(false); }
    };
    void restore();
    const unsubscribe = sessionEvents.subscribe(reason => {
      revision.current++;
      setSessionUser(null);
      setIsLoading(false);
      if (portal) window.location.replace(reason === 'forbidden' ? '/access-denied' : restoring ? '/login?session=expired' : '/session-expired');
      else router.replace('/login');
    });
    return () => { active = false; unsubscribe(); controller.abort(); clearTimeout(timer); };
  }, [setSessionUser, portal, publicWelcome, loginRoute, router]);
  useEffect(() => {
    if (!portal && !isLoading && !user && !loginRoute && !publicWelcome) router.replace('/login');
  }, [portal, isLoading, user, loginRoute, publicWelcome, router]);
  useEffect(() => {
    if (loginRoute && user) router.replace('/(tabs)');
  }, [loginRoute, user, router]);
  const logout = async () => {
    const current = ++revision.current;
    const clearPhoto = setSessionUser(null);
    recognitionDraftStore.clearDraft();
    const accessToken = await tokenStorage.getAccessToken();
    if (current !== revision.current) return;
    await tokenStorage.clearTokens();
    await clearPhoto;
    delete apiClient.defaults.headers.common.Authorization;
    if (accessToken) await axios.post(`${ENV.API_BASE_URL}/auth/logout`, {}, {
      headers: { Authorization: `Bearer ${accessToken}` }, timeout: 2000,
    }).catch(() => {});
    if (current !== revision.current) return;
    if (portal) window.location.replace('/logout?source=student');
    else router.replace('/login');
  };
  const refreshUser = async () => {
    const current = revision.current;
    const { data } = await apiClient.get('/me');
    if (current !== revision.current || data.role !== 'STUDENT' || data.active !== true) return;
    const profile = studentProfile(data);
    if (profile.id !== user?.id) return;
    await tokenStorage.saveUser(profile);
    if (current === revision.current) setUser(profile);
  };
  const changePassword = async (currentPassword: string, newPassword: string, signal?: AbortSignal) => {
    const current = renderedRevision;
    if (current !== revision.current || signal?.aborted) throw new Error('Phiên đăng nhập đã thay đổi.');
    const session = await tokenStorage.getSessionId();
    if (current !== revision.current || signal?.aborted) throw new Error('Phiên đăng nhập đã thay đổi.');
    const config = { signal, _identity: session };
    const { data } = await apiClient.post('/student/profile/password', { currentPassword, newPassword }, config);
    if (current !== revision.current || signal?.aborted) throw new Error('Phiên đăng nhập đã thay đổi.');
    if (!data.accessToken || !data.refreshToken) throw new Error('Chưa xác minh được phiên đăng nhập mới.');
    await tokenStorage.saveTokens(data.accessToken, data.refreshToken, session);
    if (current !== revision.current || signal?.aborted || await tokenStorage.getSessionId() !== session) throw new Error('Phiên đăng nhập đã thay đổi.');
  };
  return <AuthContext.Provider value={{ user, isAuthenticated: user?.role === 'STUDENT' && user.active === true, isLoading, logout, refreshUser, changePassword }}>
    {(user && (!portal || !loginRoute)) || (!user && !isLoading && (publicWelcome || (!portal && loginRoute))) ? photoRecovery.restoring ?
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 16, backgroundColor: COLORS.background }}>
        <ActivityIndicator color={COLORS.primary} /><Text>Đang khôi phục ảnh của em...</Text>
      </View> : children : <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 16, padding: 24, backgroundColor: COLORS.background }}>
      {failure ? <><Text style={{ fontFamily: FONTS.regular, color: COLORS.textSecondary }}>{failure}</Text>
        <Pressable accessibilityRole="button" onPress={() => window.location.replace('/login')}><Text>Đăng nhập lại</Text></Pressable></> :
        <><ActivityIndicator color={COLORS.primary} /><Text style={{ fontFamily: FONTS.regular, color: COLORS.textSecondary }}>Đang xác minh tài khoản…</Text></>}
    </View>}
  </AuthContext.Provider>;
};
