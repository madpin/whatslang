import { createContext, useCallback, useContext, useState } from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';
import clsx from 'clsx';

type ToastKind = 'success' | 'error' | 'info';
interface Toast {
  id: number;
  kind: ToastKind;
  title: string;
  description?: string;
}

interface ShowOptions {
  title: string;
  description?: string;
  tone?: ToastKind;
}

interface ToastCtx {
  push: (kind: ToastKind, title: string, description?: string) => void;
  show: (opts: ShowOptions) => void;
  success: (title: string, description?: string) => void;
  error: (title: string, description?: string) => void;
  info: (title: string, description?: string) => void;
}

const Ctx = createContext<ToastCtx | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const push = useCallback<ToastCtx['push']>((kind, title, description) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, kind, title, description }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const value: ToastCtx = {
    push,
    show: ({ title, description, tone = 'info' }) => push(tone, title, description),
    success: (t, d) => push('success', t, d),
    error: (t, d) => push('error', t, d),
    info: (t, d) => push('info', t, d),
  };

  return (
    <Ctx.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-96 max-w-[calc(100vw-2rem)] flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={clsx(
              'pointer-events-auto flex items-start gap-3 rounded-xl border bg-white/95 p-3 shadow-soft backdrop-blur-md dark:bg-slate-900/90',
              t.kind === 'success' && 'border-emerald-200 dark:border-emerald-700/60',
              t.kind === 'error' && 'border-rose-200 dark:border-rose-700/60',
              t.kind === 'info' && 'border-slate-200 dark:border-slate-700/60',
            )}
          >
            <div
              className={clsx(
                'mt-0.5',
                t.kind === 'success' && 'text-emerald-500',
                t.kind === 'error' && 'text-rose-500',
                t.kind === 'info' && 'text-sky-500',
              )}
            >
              {t.kind === 'success' && <CheckCircle2 size={18} />}
              {t.kind === 'error' && <AlertCircle size={18} />}
              {t.kind === 'info' && <Info size={18} />}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                {t.title}
              </div>
              {t.description && (
                <div className="mt-0.5 truncate text-xs text-slate-500 dark:text-slate-400">
                  {t.description}
                </div>
              )}
            </div>
            <button
              onClick={() =>
                setToasts((prev) => prev.filter((x) => x.id !== t.id))
              }
              className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800"
              aria-label="Dismiss"
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}

export function useToast() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useToast must be used inside ToastProvider');
  return ctx;
}
