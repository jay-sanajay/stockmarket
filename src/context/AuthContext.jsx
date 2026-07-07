import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import axios from "axios";
import { getApiBase } from "../api.js";

const AuthContext = createContext(null);

const TOKEN_KEY = "jayquant_token";

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(() => localStorage.getItem(TOKEN_KEY) || "");
  const [user, setUser] = useState(null);

  const setToken = useCallback((t) => {
    setTokenState(t || "");
    if (t) localStorage.setItem(TOKEN_KEY, t);
    else localStorage.removeItem(TOKEN_KEY);
  }, []);

  const refreshMe = useCallback(async () => {
    if (!token) {
      setUser(null);
      return;
    }
    const base = getApiBase();
    try {
      const res = await axios.get(`${base}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUser(res.data);
    } catch {
      setUser(null);
      setToken("");
    }
  }, [token, setToken]);

  const logout = useCallback(() => {
    setToken("");
    setUser(null);
  }, [setToken]);

  useEffect(() => {
    if (token) refreshMe();
  }, [token, refreshMe]);

  const value = useMemo(
    () => ({
      token,
      user,
      setToken,
      refreshMe,
      logout,
      authHeaders: token ? { Authorization: `Bearer ${token}` } : {},
    }),
    [token, user, setToken, refreshMe, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside AuthProvider");
  return ctx;
}
