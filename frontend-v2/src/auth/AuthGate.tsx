import { useEffect, useState, type ReactNode } from 'react';

const LOGIN = '/static/login.html';

export function AuthGate({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      const token = sessionStorage.getItem('auth_token');
      try {
        const r = await fetch('/auth/status');
        if (cancelled) return;

        if (!r.ok) {
          if (!cancelled) setReady(true);
          return;
        }

        const data = (await r.json()) as { auth_required?: boolean };

        if (data.auth_required && !token) {
          const back = `${window.location.pathname}${window.location.search}${window.location.hash}`;
          sessionStorage.setItem('redirect_after_login', back);
          window.location.replace(LOGIN);
          return;
        }
      } catch {
        if (cancelled) return;
        if (!token) {
          const back = `${window.location.pathname}${window.location.search}${window.location.hash}`;
          sessionStorage.setItem('redirect_after_login', back);
          window.location.replace(LOGIN);
          return;
        }
      }
      if (!cancelled) setReady(true);
    }

    void run();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!ready) {
    return (
      <div className="auth-loading">
        <p>Loading…</p>
      </div>
    );
  }

  return <>{children}</>;
}
