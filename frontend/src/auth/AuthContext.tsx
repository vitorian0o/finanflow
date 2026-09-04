import { createContext, createElement, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "../api/client";
import type { User } from "../api/types";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  token: string | null;
  setToken: (token: string | null) => void;
  logout: () => void;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => localStorage.getItem("ff_token"));
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(Boolean(token));

  const setToken = (value: string | null) => {
    setTokenState(value);
    if (value) localStorage.setItem("ff_token", value);
    else localStorage.removeItem("ff_token");
  };

  const refresh = async () => {
    if (!localStorage.getItem("ff_token")) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api<User>("/api/v1/auth/me");
      setUser(me);
    } catch {
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, [token]);

  const value = useMemo(
    () => ({
      user,
      loading,
      token,
      setToken,
      logout: () => {
        setToken(null);
        setUser(null);
      },
      refresh,
    }),
    [user, loading, token],
  );

  return createElement(AuthContext.Provider, { value }, children);
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
