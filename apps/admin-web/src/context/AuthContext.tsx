import React, { createContext, useContext, useEffect, useState, useCallback, useRef, type ReactNode } from 'react';
import { authService } from '../services/api/authService';
import { tokenStore } from '../services/api/tokenStore';
import { appConfig } from '../config/runtime';
import type { AdminUserResponse } from '../types';
interface AuthContextType {
  user: AdminUserResponse | null; isAuthenticated: boolean; loading: boolean; sessionError: string | null; accessDenied: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithSsoTicket: (code: string) => Promise<void>; logout: () => Promise<void>;
}
const AuthContext = createContext<AuthContextType | undefined>(undefined);
export const AuthProvider: React.FC<{ children: ReactNode; onSessionChange?: () => void }> = ({ children, onSessionChange }) => {
  const [user, setUser] = useState<AdminUserResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [accessDenied, setAccessDenied] = useState(false);
  const revision = useRef(0);
  const clearCache = useRef(onSessionChange);
  clearCache.current = onSessionChange;
  useEffect(() => {
    let active = true;
    const current = revision.current;
    const hasTicket = new URLSearchParams(window.location.hash.slice(1)).has('sso');
    if (!hasTicket && tokenStore.hasTokens()) {
      void authService.getMe().then(profile => {
        if (active && current === revision.current) setUser(profile);
      }).catch(error => {
        if (!active || current !== revision.current) return;
        tokenStore.clearTokens();
        setUser(null);
        setAccessDenied(error?.code === 'ROLE_FORBIDDEN');
        setSessionError(error?.code === 'ROLE_FORBIDDEN'
          ? 'Tài khoản không có quyền quản trị hoặc đã bị khóa.'
          : error?.response ? 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.' : 'Không thể xác minh phiên đăng nhập. Vui lòng kiểm tra kết nối và đăng nhập lại.');
      }).finally(() => { if (active && current === revision.current) setLoading(false); });
    } else setLoading(false);
    const clearSession = (event: Event) => {
      const forbidden = (event as CustomEvent<{ status?: number }>).detail?.status === 403;
      setAccessDenied(forbidden);
      revision.current++;
      authService.cancelPending();
      clearCache.current?.();
      setUser(null);
      setLoading(false);
      setSessionError(forbidden ? 'Tài khoản không còn quyền quản trị. Vui lòng đăng nhập bằng tài khoản phù hợp.' : 'Phiên đăng nhập đã hết hạn hoặc đã thay đổi. Vui lòng đăng nhập lại.');
    };
    const storageChanged = (event: StorageEvent) => {
      if (event.key !== null && !['mvk_admin_access_token', 'mvk_admin_refresh_token', 'mvk_admin_session_id'].includes(event.key)) return;
      if (event.newValue !== null && (event.key === 'mvk_admin_access_token' || event.key === 'mvk_admin_refresh_token')) return;
      if (event.key === null || event.key.startsWith('mvk_admin_')) {
        revision.current++;
        authService.cancelPending(false);
        clearCache.current?.();
        setUser(null);
        setLoading(false);
        setSessionError('Tài khoản đã thay đổi trong cửa sổ khác. Vui lòng tải lại hoặc đăng nhập lại.');
      }
    };
    window.addEventListener('admin_auth_required', clearSession);
    window.addEventListener('storage', storageChanged);
    return () => {
      active = false;
      window.removeEventListener('admin_auth_required', clearSession);
      window.removeEventListener('storage', storageChanged);
    };
  }, []);
  const authenticate = useCallback(async (action: () => Promise<AdminUserResponse>) => {
    const current = ++revision.current;
    clearCache.current?.();
    setUser(null);
    setSessionError(null);
    setAccessDenied(false);
    setLoading(true);
    try {
      const profile = await action();
      if (current !== revision.current) throw new Error('Phiên đăng nhập đã thay đổi.');
      setUser(profile);
    } finally { if (current === revision.current) setLoading(false); }
  }, []);
  const login = useCallback((email: string, password: string) => authenticate(() => authService.login(email, password)), [authenticate]);
  const loginWithSsoTicket = useCallback((code: string) => authenticate(() => authService.exchangeSsoTicket(code)), [authenticate]);
  const logout = async () => {
    const current = ++revision.current;
    setUser(null);
    clearCache.current?.();
    setLoading(true);
    try { await authService.logout(); }
    finally { if (current === revision.current) window.location.replace(`${appConfig.portalOrigin}/logout?source=admin`); }
  };
  return <AuthContext.Provider value={{ user, isAuthenticated: user?.role === 'ADMIN' && user.active === true, loading, sessionError, accessDenied, login, loginWithSsoTicket, logout }}>{children}</AuthContext.Provider>;
};
export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used within an AuthProvider');
  return value;
}
