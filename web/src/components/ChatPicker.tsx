import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Check, Hash, MessagesSquare, Search, X } from 'lucide-react';

import { Chats } from '@/api/endpoints';
import type { ChatBrief } from '@/api/types';
import { chatDisplayName, cn, formatJid } from '@/lib/utils';

interface ChatPickerProps {
  value: string; // selected chat_jid (empty string = none)
  onChange: (jid: string) => void;
  placeholder?: string;
  emptyLabel?: string;
  disabled?: boolean;
  /** Restrict search to a chat type. */
  chatType?: '' | 'group' | 'individual';
  /** Optional callback to render the empty / "none" choice as a real menu item. */
  allowClear?: boolean;
  className?: string;
}

/**
 * Searchable, server-side filtered chat picker.
 *
 * Designed to scale to thousands of chats: the list is fetched on demand
 * with a 250ms debounce and a hard cap of 30 results. The selected value's
 * friendly name is fetched separately when needed so it shows up even if
 * the chat isn't in the latest search slice.
 */
export function ChatPicker({
  value,
  onChange,
  placeholder = 'Search chats…',
  emptyLabel = 'No chat selected',
  disabled = false,
  chatType = '',
  allowClear = true,
  className,
}: ChatPickerProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [debounced, setDebounced] = useState('');
  const [highlight, setHighlight] = useState(0);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const wrapperRef = useRef<HTMLDivElement | null>(null);

  // Debounce query changes.
  useEffect(() => {
    const t = setTimeout(() => setDebounced(query.trim()), 200);
    return () => clearTimeout(t);
  }, [query]);

  // Resolve the friendly name of the current value, even if it's not in the
  // latest search list.
  const selectedQ = useQuery({
    enabled: !!value,
    queryKey: ['chats', 'pick', 'one', value],
    queryFn: async (): Promise<ChatBrief | null> => {
      if (!value) return null;
      const list = await Chats.search(value, 1, chatType);
      const exact = list.find((c) => c.chat_jid === value);
      return exact ?? { chat_jid: value, chat_name: value };
    },
    staleTime: 60_000,
  });

  const searchQ = useQuery({
    enabled: open,
    queryKey: ['chats', 'pick', 'search', debounced, chatType],
    queryFn: () => Chats.search(debounced, 30, chatType),
    placeholderData: (p) => p,
    staleTime: 5_000,
  });

  const items = useMemo(() => searchQ.data ?? [], [searchQ.data]);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (!wrapperRef.current?.contains(e.target as Node)) setOpen(false);
    };
    window.addEventListener('mousedown', onClick);
    return () => window.removeEventListener('mousedown', onClick);
  }, [open]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      setOpen(false);
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlight((h) => Math.min(items.length - 1, h + 1));
      return;
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlight((h) => Math.max(0, h - 1));
      return;
    }
    if (e.key === 'Enter') {
      e.preventDefault();
      const pick = items[highlight];
      if (pick) {
        onChange(pick.chat_jid);
        setOpen(false);
        setQuery('');
      }
    }
  };

  const selected = selectedQ.data ?? null;
  const selectedLabel = value
    ? selected
      ? chatDisplayName(selected)
      : formatJid(value)
    : '';

  return (
    <div ref={wrapperRef} className={cn('relative', className)}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((v) => !v)}
        className={cn(
          'flex w-full items-center justify-between gap-2 rounded-lg border bg-white px-3 py-2 text-left text-sm shadow-sm transition-colors',
          'border-zinc-200 hover:border-zinc-300 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500',
          'dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700',
          disabled && 'cursor-not-allowed opacity-60',
        )}
      >
        <span className="flex min-w-0 items-center gap-2">
          {value ? (
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-300">
              {value.endsWith('@g.us') ? <Hash size={12} /> : <MessagesSquare size={12} />}
            </span>
          ) : null}
          <span className="min-w-0 flex-1 truncate">
            {value ? (
              <>
                <span className="text-zinc-900 dark:text-zinc-100">{selectedLabel}</span>
                <span className="ml-2 truncate text-xs text-zinc-500 dark:text-zinc-400">
                  {value}
                </span>
              </>
            ) : (
              <span className="text-zinc-500 dark:text-zinc-400">{emptyLabel}</span>
            )}
          </span>
        </span>
        {value && allowClear && !disabled ? (
          <span
            role="button"
            aria-label="Clear selection"
            onClick={(e) => {
              e.stopPropagation();
              onChange('');
              setQuery('');
            }}
            className="rounded p-1 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-200"
          >
            <X size={14} />
          </span>
        ) : (
          <span className="text-zinc-400">▾</span>
        )}
      </button>

      {open ? (
        <div className="absolute z-30 mt-1 w-full overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-xl dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center gap-2 border-b border-zinc-100 px-3 py-2 dark:border-zinc-800">
            <Search size={14} className="text-zinc-400" />
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setHighlight(0);
              }}
              onKeyDown={onKeyDown}
              placeholder={placeholder}
              className="w-full bg-transparent text-sm text-zinc-800 placeholder:text-zinc-400 focus:outline-none dark:text-zinc-100"
            />
            {searchQ.isFetching ? (
              <span className="text-[10px] uppercase tracking-wider text-zinc-400">
                Searching…
              </span>
            ) : null}
          </div>
          <ul className="max-h-72 overflow-auto py-1 text-sm">
            {items.length === 0 ? (
              <li className="px-3 py-3 text-center text-xs text-zinc-500">
                {searchQ.isLoading ? 'Loading…' : 'No matches.'}
              </li>
            ) : (
              items.map((c, i) => {
                const isActive = i === highlight;
                const isSelected = c.chat_jid === value;
                return (
                  <li key={c.chat_jid}>
                    <button
                      type="button"
                      className={cn(
                        'flex w-full items-center gap-2 px-3 py-2 text-left',
                        isActive && 'bg-brand-50 dark:bg-brand-900/20',
                      )}
                      onMouseEnter={() => setHighlight(i)}
                      onClick={() => {
                        onChange(c.chat_jid);
                        setOpen(false);
                        setQuery('');
                      }}
                    >
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
                        {c.chat_jid.endsWith('@g.us') ? (
                          <Hash size={12} />
                        ) : (
                          <MessagesSquare size={12} />
                        )}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-zinc-900 dark:text-zinc-100">
                          {chatDisplayName(c)}
                        </span>
                        <span className="block truncate text-xs text-zinc-500 dark:text-zinc-400">
                          {c.chat_jid}
                        </span>
                      </span>
                      {isSelected ? (
                        <Check size={14} className="text-brand-600 dark:text-brand-300" />
                      ) : null}
                    </button>
                  </li>
                );
              })
            )}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
