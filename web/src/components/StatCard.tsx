import { cn } from '@/lib/utils';

interface StatCardProps {
  label: string;
  value: React.ReactNode;
  hint?: string;
  icon?: React.ReactNode;
  tone?: 'brand' | 'green' | 'amber' | 'gray' | 'blue' | 'violet';
  loading?: boolean;
}

const TONES: Record<NonNullable<StatCardProps['tone']>, string> = {
  brand: 'from-brand-500/15 to-brand-500/0 text-brand-600 dark:text-brand-400',
  green: 'from-emerald-500/15 to-emerald-500/0 text-emerald-600 dark:text-emerald-400',
  amber: 'from-amber-500/15 to-amber-500/0 text-amber-600 dark:text-amber-400',
  gray: 'from-zinc-500/10 to-zinc-500/0 text-zinc-700 dark:text-zinc-300',
  blue: 'from-sky-500/15 to-sky-500/0 text-sky-600 dark:text-sky-400',
  violet: 'from-violet-500/15 to-violet-500/0 text-violet-600 dark:text-violet-400',
};

export function StatCard({
  label,
  value,
  hint,
  icon,
  tone = 'brand',
  loading,
}: StatCardProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900',
      )}
    >
      <div
        className={cn(
          'pointer-events-none absolute inset-0 bg-gradient-to-br opacity-100',
          TONES[tone],
        )}
      />
      <div className="relative flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            {label}
          </p>
          <div className="mt-2 text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
            {loading ? (
              <span className="inline-block h-7 w-12 animate-pulse rounded-md bg-zinc-100 dark:bg-zinc-800" />
            ) : (
              value
            )}
          </div>
          {hint ? (
            <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">{hint}</p>
          ) : null}
        </div>
        {icon ? (
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/60 text-current shadow-sm ring-1 ring-zinc-200/60 dark:bg-zinc-950/40 dark:ring-zinc-700/40">
            {icon}
          </div>
        ) : null}
      </div>
    </div>
  );
}
