import { useState } from 'react';
import {
  ChevronDown,
  LogOut,
  Menu,
  Moon,
  RefreshCw,
  Sun,
  SunMoon,
  User as UserIcon,
} from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { useTheme } from '@/lib/theme';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';

export function TopBar({
  onToggleSidebar,
  onRefresh,
  refreshing,
}: {
  onToggleSidebar?: () => void;
  onRefresh?: () => void;
  refreshing?: boolean;
}) {
  const { status, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const [open, setOpen] = useState(false);

  const cycleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light');
  };

  const ThemeIcon = theme === 'light' ? Sun : theme === 'dark' ? Moon : SunMoon;

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-3 border-b border-zinc-200 bg-white/80 px-4 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/80">
      <div className="flex items-center gap-2">
        {onToggleSidebar ? (
          <button
            type="button"
            onClick={onToggleSidebar}
            className="rounded-md p-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
            aria-label="Toggle sidebar"
          >
            <Menu size={18} />
          </button>
        ) : null}
      </div>
      <div className="flex items-center gap-2">
        {onRefresh ? (
          <Button
            variant="ghost"
            size="icon"
            onClick={onRefresh}
            title="Refresh data"
            aria-label="Refresh data"
          >
            <RefreshCw size={16} className={cn(refreshing && 'animate-spin')} />
          </Button>
        ) : null}
        <Button
          variant="ghost"
          size="icon"
          onClick={cycleTheme}
          title={`Theme: ${theme}`}
          aria-label="Toggle theme"
        >
          <ThemeIcon size={16} />
        </Button>
        <div className="relative">
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className="flex items-center gap-2 rounded-lg border border-zinc-200 px-2 py-1.5 text-sm hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-800/60"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-100 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300">
              <UserIcon size={14} />
            </span>
            <span className="hidden font-medium text-zinc-800 sm:inline dark:text-zinc-100">
              {status?.user ?? 'guest'}
            </span>
            <ChevronDown size={14} className="text-zinc-400" />
          </button>
          {open ? (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setOpen(false)}
                aria-hidden
              />
              <div className="absolute right-0 z-20 mt-2 w-56 overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-xl dark:border-zinc-800 dark:bg-zinc-950">
                <div className="px-3 py-3">
                  <p className="text-xs uppercase tracking-wider text-zinc-400">
                    Signed in as
                  </p>
                  <p className="truncate text-sm font-medium text-zinc-800 dark:text-zinc-100">
                    {status?.user ?? 'guest'}
                  </p>
                </div>
                <div className="border-t border-zinc-100 p-1 dark:border-zinc-800">
                  <button
                    type="button"
                    onClick={() => {
                      setOpen(false);
                      logout();
                    }}
                    className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm text-zinc-700 hover:bg-zinc-100 dark:text-zinc-200 dark:hover:bg-zinc-800"
                  >
                    <LogOut size={14} />
                    Log out
                  </button>
                </div>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </header>
  );
}
