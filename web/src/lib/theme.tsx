import { createContext, useContext, useEffect, useMemo, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';
const STORAGE_KEY = 'whatslang.theme';

interface ThemeCtx {
  theme: Theme;
  resolved: 'light' | 'dark';
  setTheme: (t: Theme) => void;
  toggle: () => void;
}

const Ctx = createContext<ThemeCtx | null>(null);

function resolve(theme: Theme): 'light' | 'dark' {
  if (theme === 'system') {
    return typeof window !== 'undefined' &&
      window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
  }
  return theme;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null;
    return (stored as Theme) || 'dark';
  });
  const [resolved, setResolved] = useState<'light' | 'dark'>(() => resolve(theme));

  useEffect(() => {
    const r = resolve(theme);
    setResolved(r);
    document.documentElement.classList.toggle('dark', r === 'dark');
    document.documentElement.classList.toggle('light', r === 'light');
  }, [theme]);

  useEffect(() => {
    if (theme !== 'system') return;
    const mql = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      const r = resolve('system');
      setResolved(r);
      document.documentElement.classList.toggle('dark', r === 'dark');
    };
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, [theme]);

  const value = useMemo<ThemeCtx>(
    () => ({
      theme,
      resolved,
      setTheme: (t) => {
        localStorage.setItem(STORAGE_KEY, t);
        setThemeState(t);
      },
      toggle: () => {
        const next = resolved === 'dark' ? 'light' : 'dark';
        localStorage.setItem(STORAGE_KEY, next);
        setThemeState(next);
      },
    }),
    [theme, resolved],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useTheme() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider');
  return ctx;
}
