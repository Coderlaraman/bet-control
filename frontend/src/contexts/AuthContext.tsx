import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI } from '../services/api';
import Cookies from 'js-cookie';

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = Cookies.get('access_token');
    if (token) {
      // En producción, deberías validar el token con el backend
      setUser({
        id: 1,
        username: 'user',
        email: 'user@example.com',
        full_name: 'Test User',
        is_active: true,
      });
    }
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const response = await authAPI.login({ username, password });
      const { access_token, refresh_token } = response.data;

      Cookies.set('access_token', access_token, { expires: 7 });
      Cookies.set('refresh_token', refresh_token, { expires: 30 });

      // En producción, obtén los datos del usuario del backend
      setUser({
        id: 1,
        username,
        email: 'user@example.com',
        full_name: 'Test User',
        is_active: true,
      });
    } catch (error: any) {
      // Extraer mensaje de error específico del backend
      const errorMessage = error.response?.data?.detail || 'Login failed';
      console.error('Login error:', errorMessage);
      throw new Error(errorMessage);
    }
  };

  const register = async (data: any) => {
    try {
      await authAPI.register(data);
      // Auto login after register
      await login(data.username, data.password);
    } catch (error: any) {
      // Extraer mensaje de error específico del backend
      const errorMessage = error.response?.data?.detail || 'Registration failed';
      console.error('Registration error:', errorMessage);
      throw new Error(errorMessage);
    }
  };

  const logout = () => {
    Cookies.remove('access_token');
    Cookies.remove('refresh_token');
    setUser(null);
    window.location.href = '/login';
  };

  const value = {
    user,
    login,
    register,
    logout,
    isLoading,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};