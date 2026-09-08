import { createContext, useContext, useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AppTeacherService } from '../../services/api/ServiceLocator';
import { AuthTokenStore } from '../../services/api/AuthTokenStore';

interface AuthContextType {
  user: any;
  loading: boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({ user: null, loading: true, logout: () => {} });

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const fetchMe = async () => {
      try {
        if (!AppTeacherService.getMe) {
            setUser({ displayName: "Giáo viên", role: "TEACHER" }); // Mock fallback
            setLoading(false);
            return;
        }
        const data = await AppTeacherService.getMe();
        if (data.role !== 'TEACHER') {
          throw new Error('Unauthorized role');
        }
        setUser(data);
      } catch (err) {
        AuthTokenStore.clearTokens();
        setUser(null);
        if (location.pathname !== '/login') {
          navigate('/login');
        }
      } finally {
        setLoading(false);
      }
    };
    
    if (location.pathname !== '/login') {
      fetchMe();
    } else {
      setLoading(false);
    }
  }, [navigate, location.pathname]);

  const logout = () => {
    AuthTokenStore.clearTokens();
    setUser(null);
    navigate('/login');
  };

  return (
    <AuthContext.Provider value={{ user, loading, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
