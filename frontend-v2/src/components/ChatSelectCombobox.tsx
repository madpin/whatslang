import { useState, useRef, useEffect, useCallback } from 'react';
import { Search, X, ChevronDown } from 'lucide-react';
import type { ChatRow } from '../api/client';

interface ChatSelectComboboxProps {
  chats: ChatRow[];
  excludeJid?: string;
  value: string | null | undefined;
  disabled?: boolean;
  onChange: (jid: string | null) => void;
  ariaLabel?: string;
}

export function ChatSelectCombobox({
  chats,
  excludeJid,
  value,
  disabled,
  onChange,
  ariaLabel = 'Select a chat',
}: ChatSelectComboboxProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const available = chats.filter((c) => c.chat_jid !== excludeJid);

  const filtered = query.trim()
    ? available.filter((c) => {
        const q = query.toLowerCase();
        return (
          (c.chat_name ?? '').toLowerCase().includes(q) ||
          c.chat_jid.toLowerCase().includes(q)
        );
      })
    : available;

  const selected = value ? available.find((c) => c.chat_jid === value) : null;

  const shortJid = (jid: string) => jid.split('@')[0];

  const handleSelect = useCallback(
    (jid: string | null) => {
      onChange(jid);
      setOpen(false);
      setQuery('');
    },
    [onChange],
  );

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
        setQuery('');
      }
    }
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  useEffect(() => {
    if (open && inputRef.current) inputRef.current.focus();
  }, [open]);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Escape') {
      setOpen(false);
      setQuery('');
    }
  }

  return (
    <div className="chat-combobox" ref={containerRef} onKeyDown={handleKeyDown}>
      <button
        type="button"
        className="chat-combobox-trigger"
        disabled={disabled}
        onClick={() => setOpen((o) => !o)}
        aria-label={ariaLabel}
        aria-expanded={open}
      >
        {selected ? (
          <span className="chat-combobox-value">
            <span className="chat-combobox-name">{selected.chat_name || shortJid(selected.chat_jid)}</span>
            <span className="chat-combobox-jid">{shortJid(selected.chat_jid)}</span>
          </span>
        ) : (
          <span className="chat-combobox-placeholder">Same chat</span>
        )}
        <ChevronDown size={12} className={`chat-combobox-chevron ${open ? 'open' : ''}`} />
      </button>

      {open && (
        <div className="chat-combobox-dropdown">
          <div className="chat-combobox-search">
            <Search size={12} className="chat-combobox-search-icon" />
            <input
              ref={inputRef}
              type="text"
              className="chat-combobox-search-input"
              placeholder="Search name or JID…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            {query && (
              <button
                type="button"
                className="chat-combobox-search-clear"
                onClick={() => setQuery('')}
                aria-label="Clear search"
              >
                <X size={10} />
              </button>
            )}
          </div>
          <ul className="chat-combobox-list" role="listbox">
            <li
              role="option"
              aria-selected={!value}
              className={`chat-combobox-option ${!value ? 'selected' : ''}`}
              onClick={() => handleSelect(null)}
            >
              <span className="chat-combobox-option-name">Same chat</span>
              <span className="chat-combobox-option-jid">No forwarding</span>
            </li>
            {filtered.map((c) => (
              <li
                key={c.chat_jid}
                role="option"
                aria-selected={c.chat_jid === value}
                className={`chat-combobox-option ${c.chat_jid === value ? 'selected' : ''}`}
                onClick={() => handleSelect(c.chat_jid)}
              >
                <span className="chat-combobox-option-name">{c.chat_name || shortJid(c.chat_jid)}</span>
                <span className="chat-combobox-option-jid">{shortJid(c.chat_jid)}</span>
              </li>
            ))}
            {filtered.length === 0 && query && (
              <li className="chat-combobox-empty">No chats match "{query}"</li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
