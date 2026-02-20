'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import API, { TokenManager, User, AuthResponse } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (phone: string, pass: string) => Promise<boolean>;
  signup: (userData: any) => Promise<boolean>;
  logout: () => Promise<void>;
  updateUser: (newUser: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const initAuth = async () => {
      const storedUser = TokenManager.getUser();
      const token = TokenManager.getAccessToken();

      if (token && storedUser) {
        setUser(storedUser);
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (phone: string, pass: string) => {
    try {
      const response = await API.Auth.login(phone, pass);
      if (response && response.success && response.user) {
        // Validation: user object should be set
        setUser(response.user);
        router.push('/dashboard');
        return true;
      }
      return false;
    } catch (error) {
      console.error("Login failed", error);
      throw error;
    }
  };

  const signup = async (userData: any) => {
    try {
      const response = await API.Auth.signup(userData);
      if (response && response.success && response.user) {
        setUser(response.user);
        router.push('/dashboard');
        return true;
      }
      return false;
    } catch (error) {
      console.error("Signup failed", error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await API.Auth.logout();
    } catch (error) {
      console.error("Logout error", error);
    }
    setUser(null);
    router.push('/login');
  };

  const updateUser = (newUser: User) => {
    setUser(newUser);
    TokenManager.setUser(newUser);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
