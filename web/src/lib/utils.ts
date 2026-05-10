import clsx, { type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return 'never';
  const ts = new Date(iso).getTime();
  if (Number.isNaN(ts)) return 'unknown';
  const diff = Date.now() - ts;
  const sec = Math.round(diff / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.round(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.round(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const d = Math.round(hr / 24);
  if (d < 7) return `${d}d ago`;
  const w = Math.round(d / 7);
  if (w < 5) return `${w}w ago`;
  return new Date(iso).toLocaleDateString();
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString();
}

export function formatJid(jid: string): string {
  const at = jid.indexOf('@');
  return at >= 0 ? jid.slice(0, at) : jid;
}

export function chatTypeLabel(jid: string): 'group' | 'individual' {
  return jid.endsWith('@g.us') ? 'group' : 'individual';
}

export function shortenJid(jid: string, length = 18): string {
  if (jid.length <= length) return jid;
  return `${jid.slice(0, length - 3)}…`;
}

export function pluralize(n: number, singular: string, plural?: string): string {
  if (n === 1) return `${n} ${singular}`;
  return `${n} ${plural ?? `${singular}s`}`;
}

/** Best display name for a chat-like value. */
export function chatDisplayName(
  chat: { chat_name?: string | null; chat_jid: string } | null | undefined,
): string {
  if (!chat) return '—';
  const name = (chat.chat_name ?? '').trim();
  if (!name || name === chat.chat_jid) {
    return formatJid(chat.chat_jid);
  }
  return name;
}

/** Human-readable file size. */
export function formatBytes(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n) || n < 0) return '—';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let v = n;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i += 1;
  }
  return `${v < 10 && i > 0 ? v.toFixed(1) : Math.round(v)} ${units[i]}`;
}

/** Tiny debounced value hook (no useEffect arg edge cases). */
export function debounce<T extends (...args: unknown[]) => void>(fn: T, delay = 250): T {
  let t: ReturnType<typeof setTimeout> | null = null;
  return ((...args: unknown[]) => {
    if (t) clearTimeout(t);
    t = setTimeout(() => fn(...args), delay);
  }) as T;
}
