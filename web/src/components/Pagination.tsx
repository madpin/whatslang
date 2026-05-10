import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/Button';

interface Props {
  page: number;
  perPage: number;
  total: number;
  totalPages: number;
  onChange: (page: number) => void;
}

export function PaginationBar({ page, perPage, total, totalPages, onChange }: Props) {
  if (total <= perPage) return null;
  const start = (page - 1) * perPage + 1;
  const end = Math.min(page * perPage, total);
  return (
    <div className="flex items-center justify-between gap-3 px-1 py-3 text-xs text-zinc-500 dark:text-zinc-400">
      <span>
        Showing <span className="font-medium text-zinc-700 dark:text-zinc-200">{start}</span>–
        <span className="font-medium text-zinc-700 dark:text-zinc-200">{end}</span> of{' '}
        <span className="font-medium text-zinc-700 dark:text-zinc-200">{total}</span>
      </span>
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
          leftIcon={<ChevronLeft size={14} />}
        >
          Prev
        </Button>
        <span className="px-2 text-zinc-600 dark:text-zinc-300">
          {page} / {totalPages}
        </span>
        <Button
          variant="outline"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1)}
          rightIcon={<ChevronRight size={14} />}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
