import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Lock, MessagesSquare, User } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useAuth } from '@/lib/auth';
import { useToast } from '@/lib/toast';
import { ApiError } from '@/api/client';

export function LoginPage() {
  const { authenticated, login, status, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const [user, setUser] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? '/';

  useEffect(() => {
    if (!loading && authenticated) {
      navigate(from, { replace: true });
    }
  }, [loading, authenticated, navigate, from]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(user, password);
      toast.show({ title: 'Welcome back', tone: 'success' });
      navigate(from, { replace: true });
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.message : 'Unable to sign in. Check credentials.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (status && !status.auth_required) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
        <div className="rounded-2xl border border-zinc-200 bg-white p-8 text-center dark:border-zinc-800 dark:bg-zinc-900">
          <p className="text-sm text-zinc-600 dark:text-zinc-300">
            Authentication is disabled. Continue to the app.
          </p>
          <Button className="mt-4" onClick={() => navigate('/', { replace: true })}>
            Open dashboard
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-zinc-50 via-white to-brand-50 px-4 dark:from-zinc-950 dark:via-zinc-950 dark:to-brand-950">
      <div className="w-full max-w-md">
        <div className="mb-6 flex items-center justify-center gap-2 text-brand-600 dark:text-brand-300">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-white shadow-lg">
            <MessagesSquare size={20} />
          </span>
          <span className="text-lg font-bold tracking-tight">Whatslang Console</span>
        </div>
        <div className="rounded-2xl border border-zinc-200 bg-white p-8 shadow-xl dark:border-zinc-800 dark:bg-zinc-900">
          <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">
            Sign in to continue
          </h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Use the credentials configured in your environment.
          </p>
          <form className="mt-6 space-y-4" onSubmit={onSubmit}>
            <Input
              label="Username"
              name="user"
              autoFocus
              autoComplete="username"
              leftIcon={<User size={16} />}
              value={user}
              onChange={(e) => setUser(e.target.value)}
              required
            />
            <Input
              label="Password"
              name="password"
              type="password"
              autoComplete="current-password"
              leftIcon={<Lock size={16} />}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {error ? (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900 dark:bg-red-900/20 dark:text-red-300">
                {error}
              </div>
            ) : null}
            <Button type="submit" loading={submitting} className="w-full" size="lg">
              Sign in
            </Button>
          </form>
        </div>
        <p className="mt-4 text-center text-xs text-zinc-400">
          Whatslang · v3.0
        </p>
      </div>
    </div>
  );
}
