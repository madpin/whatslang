import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

export function Spinner({
  className,
  size = 16,
}: {
  className?: string;
  size?: number;
}) {
  return <Loader2 className={cn('animate-spin', className)} size={size} />;
}

export function FullPageSpinner({ label }: { label?: string }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-sm text-zinc-500">
      <Spinner size={28} />
      {label ? <span>{label}</span> : null}
    </div>
  );
}
