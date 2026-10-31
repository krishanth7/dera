"use client";

import * as React from "react";
import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { apiClient, UserResponse, DeraApiError } from "@/lib/api-client";
import { useRouter, usePathname } from "next/navigation";

interface AuthContextType {
  user: UserResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refreshUser = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const currentUser = await apiClient.getCurrentUser();
      setUser(currentUser);
    } catch (err: unknown) {
      if (err instanceof DeraApiError && err.status === 401) {
        setUser(null);
      } else {
        // Fallback for development if local backend is unmounted
        setUser(null);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.login(email, password);
      setUser(response.user);
      router.push("/app/overview");
    } catch (err: unknown) {
      const msg = err instanceof DeraApiError ? err.problem.detail : "Login failed";
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.register(email, password);
      setUser(response.user);
      router.push("/app/overview");
    } catch (err: unknown) {
      const msg = err instanceof DeraApiError ? err.problem.detail : "Registration failed";
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await apiClient.logout();
    } catch (err) {
      console.warn("Logout error:", err);
    } finally {
      setUser(null);
      setIsLoading(false);
      router.push("/login");
    }
  };

  const logoutAll = async () => {
    setIsLoading(true);
    try {
      await apiClient.logoutAll();
    } catch (err) {
      console.warn("Logout-all error:", err);
    } finally {
      setUser(null);
      setIsLoading(false);
      router.push("/login");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        error,
        login,
        register,
        logout,
        logoutAll,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
