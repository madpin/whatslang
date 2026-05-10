import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Auth } from '@/api/endpoints';
import type { AuthStatus } from '@/api/types';

interface AuthCtx {
  loading: boolean;
  status: AuthStatus | null;
  authenticated: boolean;
  login: (user: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const refresh = useCallback(async () => {
    try {
      const s = await Auth.status();
      setStatus(s);
    } catch {
      setStatus({ auth_required: true, user: null });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    const onUnauth = () => {
      setStatus((prev) => (prev ? { ...prev, user: null } : prev));
      if (window.location.pathname !== '/login') {
        navigate('/login', { replace: true });
      }
    };
    window.addEventListener('whatslang:unauthorized', onUnauth);
    return () => window.removeEventListener('whatslang:unauthorized', onUnauth);
  }, [navigate]);

  const login = useCallback(
    async (user: string, password: string) => {
      await Auth.login(user, password);
      await refresh();
    },
    [refresh],
  );

  const logout = useCallback(async () => {
    await Auth.logout();
    await refresh();
    navigate('/login', { replace: true });
  }, [refresh, navigate]);

  const value = useMemo<AuthCtx>(
    () => ({
      loading,
      status,
      authenticated: status ? !status.auth_required || !!status.user : false,
      login,
      logout,
      refresh,
    }),
    [loading, status, login, logout, refresh],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
