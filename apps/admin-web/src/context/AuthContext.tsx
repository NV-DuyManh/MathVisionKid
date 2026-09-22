import React, { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { authService } from '../services/api/authService';
import { tokenStore } from '../services/api/tokenStore';
import type { AdminUserResponse } from '../types';

interface AuthContextType {
  user: AdminUserResponse | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithSsoTicket: (code: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AdminUserResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      if (tokenStore.hasTokens()) {
        try {
          const userData = await authService.getMe();
          if (userData.role === 'ADMIN') {
            setUser(userData);
          } else {
            tokenStore.clearTokens();
            setUser(null);
          }
        } catch {
          tokenStore.clearTokens();
          setUser(null);
        }
      }
      setLoading(false);
    };

    initAuth();

    const handleAuthRequired = () => {
      setUser(null);
    };

    window.addEventListener('admin_auth_required', handleAuthRequired);
    return () => {
      window.removeEventListener('admin_auth_required', handleAuthRequired);
    };
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const userData = await authService.login(email, password);
      setUser(userData);
    } finally {
      setLoading(false);
    }
  };

  const loginWithSsoTicket = async (code: string) => {
    setLoading(true);
    try {
      const userData = await authService.exchangeSsoTicket(code);
      setUser(userData);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } finally {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user && user.role === 'ADMIN',
        loading,
        login,
        loginWithSsoTicket,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
