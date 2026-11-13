import { createContext, useContext, useEffect, useState, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { AppTeacherService } from '../../services/api/ServiceLocator';
import { AuthTokenStore } from '../../services/api/AuthTokenStore';
import axios from 'axios';
import { appConfig } from '../../config/runtime';

interface AuthContextType {
  user: any;
  loading: boolean;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({ user: null, loading: true, logout: async () => {} });

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();
  const isHandoff = ['/login', '/auth/continue'].includes(location.pathname);
  const queryClient = useQueryClient();
  const sessionVersion = useRef(0);
  const loggingOut = useRef(false);

  useEffect(() => {
    const revalidate = (event: PageTransitionEvent) => {
      if (event.persisted) window.location.reload();
    };
    window.addEventListener('pageshow', revalidate);
    return () => window.removeEventListener('pageshow', revalidate);
  }, []);
  useEffect(() => {
    const clearSession = () => {
      sessionVersion.current += 1;
      void queryClient.cancelQueries();
      queryClient.clear();
      setUser(null);
      if (!loggingOut.current && !AuthTokenStore.getAccessToken() && !AuthTokenStore.getRefreshToken()) {
        navigate('/login', { replace: true });
      }
    };
    window.addEventListener('teacher_auth_changed', clearSession);
    return () => window.removeEventListener('teacher_auth_changed', clearSession);
  }, [queryClient, navigate]);

  useEffect(() => {
    let active = true;
    const version = sessionVersion.current;
    const fetchMe = async () => {
      try {
        if (!AuthTokenStore.getAccessToken() && !AuthTokenStore.getRefreshToken()) {
          if (active) navigate('/login', { replace: true });
          return;
        }
        if (!AppTeacherService.getMe) {
            setUser({ displayName: "Giáo viên", role: "TEACHER" }); // Mock fallback
            setLoading(false);
            return;
        }
        const data = await AppTeacherService.getMe();
        if (!active || version !== sessionVersion.current) return;
        if (data.role !== 'TEACHER' || data.active === false) {
          throw new Error('Unauthorized role');
        }
        setUser(data);
      } catch {
        if (!active || version !== sessionVersion.current) return;
        AuthTokenStore.clearTokens();
        setUser(null);
        if (!isHandoff) {
          navigate('/login');
        }
      } finally {
        if (active && version === sessionVersion.current) setLoading(false);
      }
    };
    
    if (!isHandoff) {
      fetchMe();
    } else {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLoading(false);
    }
    return () => { active = false; };
  }, [navigate, isHandoff]);

  const logout = async () => {
    const accessToken = AuthTokenStore.getAccessToken();
    // Let the explicit Portal logout own navigation. Mounting /login here can
    // redirect to the landing page before the Portal clears its own session.
    loggingOut.current = true;
    AuthTokenStore.clearTokens();
    setUser(null);
    // Revoke only the captured session; network availability must not delay leaving.
    if (accessToken) void axios.post(`${appConfig.apiBaseUrl}/auth/logout`, {}, {
      headers: { Authorization: `Bearer ${accessToken}` }, timeout: 5000,
    }).catch(() => {});
    window.location.replace(`${appConfig.portalOrigin}/logout?source=teacher`);
  };

  return (
    <AuthContext.Provider value={{ user, loading, logout }}>
      {isHandoff || user ? children : (
        <main className="auth-page teacher-session-screen"><p role="status">Đang mở không gian giáo viên…</p></main>
      )}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
