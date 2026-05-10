import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  error?: string;
  label?: string;
  hint?: string;
};

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, leftIcon, rightIcon, error, label, hint, id, ...props },
  ref,
) {
  const inputId = id ?? props.name;
  return (
    <div className="flex w-full flex-col gap-1.5">
      {label ? (
        <label
          htmlFor={inputId}
          className="text-xs font-medium text-zinc-600 dark:text-zinc-300"
        >
          {label}
        </label>
      ) : null}
      <div
        className={cn(
          'relative flex items-center rounded-lg border bg-white shadow-sm transition-colors',
          'border-zinc-300 focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-500/30',
          'dark:bg-zinc-900 dark:border-zinc-700 dark:focus-within:border-brand-400',
          error && 'border-red-500 focus-within:border-red-500 focus-within:ring-red-500/30',
        )}
      >
        {leftIcon ? (
          <span className="pl-3 text-zinc-400">{leftIcon}</span>
        ) : null}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            'h-10 w-full bg-transparent px-3 text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none dark:text-zinc-100',
            leftIcon && 'pl-2',
            rightIcon && 'pr-2',
            className,
          )}
          {...props}
        />
        {rightIcon ? <span className="pr-3 text-zinc-400">{rightIcon}</span> : null}
      </div>
      {error ? (
        <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
      ) : hint ? (
        <p className="text-xs text-zinc-500 dark:text-zinc-400">{hint}</p>
      ) : null}
    </div>
  );
});
