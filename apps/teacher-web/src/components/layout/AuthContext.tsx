import { createContext, useContext, useEffect, useState, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { AppTeacherService } from '../../services/api/ServiceLocator';
import { AuthTokenStore } from '../../services/api/AuthTokenStore';
import apiClient from '../../services/api/apiClient';
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
  const queryClient = useQueryClient();
  const sessionVersion = useRef(0);

  useEffect(() => {
    const clearSession = () => {
      sessionVersion.current += 1;
      void queryClient.cancelQueries();
      queryClient.clear();
      setUser(null);
    };
    window.addEventListener('teacher_auth_changed', clearSession);
    return () => window.removeEventListener('teacher_auth_changed', clearSession);
  }, [queryClient]);

  useEffect(() => {
    let active = true;
    const version = sessionVersion.current;
    const fetchMe = async () => {
      try {
        if (!AppTeacherService.getMe) {
            setUser({ displayName: "Giáo viên", role: "TEACHER" }); // Mock fallback
            setLoading(false);
            return;
        }
        const data = await AppTeacherService.getMe();
        if (!active || version !== sessionVersion.current) return;
        if (data.role !== 'TEACHER') {
          throw new Error('Unauthorized role');
        }
        setUser(data);
      } catch {
        if (!active || version !== sessionVersion.current) return;
        AuthTokenStore.clearTokens();
        setUser(null);
        if (location.pathname !== '/login') {
          navigate('/login');
        }
      } finally {
        if (active && version === sessionVersion.current) setLoading(false);
      }
    };
    
    if (location.pathname !== '/login') {
      fetchMe();
    } else {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLoading(false);
    }
    return () => { active = false; };
  }, [navigate, location.pathname]);

  const logout = async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // Ignore network errors
    } finally {
      AuthTokenStore.clearTokens();
      setUser(null);
      window.location.href = `${appConfig.portalOrigin}/logout?source=teacher`;
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, logout }}>
      {location.pathname === '/login' || user ? children : <div role="status">Đang kiểm tra phiên đăng nhập...</div>}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
