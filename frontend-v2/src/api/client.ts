const API_BASE = '';

function authHeaders(): HeadersInit {
  const token = sessionStorage.getItem('auth_token');
  const h: Record<string, string> = { Accept: 'application/json' };
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const base = authHeaders() as Record<string, string>;
  Object.entries(base).forEach(([k, v]) => headers.set(k, v));
  if (!headers.has('Content-Type') && init.body && typeof init.body === 'string') {
    headers.set('Content-Type', 'application/json');
  }
  return fetch(`${API_BASE}${path}`, { ...init, headers });
}

export type StatsResponse = {
  total_chats: number;
  running_bots: number;
  stopped_bots: number;
  available_bot_types: number;
};

export async function fetchStats(): Promise<StatsResponse> {
  const r = await apiFetch('/stats');
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export type BotInfo = {
  name: string;
  display_name: string;
  prefix: string;
  status: string;
  uptime_seconds?: number;
};

export type ChatRow = {
  chat_jid: string;
  chat_name: string;
  message_count?: number;
  last_message_time?: string | null;
  bots: BotInfo[];
};

export type ChatsListResponse = {
  chats: ChatRow[];
  pagination?: { total: number; page: number; per_page: number; total_pages: number };
};

export async function fetchChats(params: URLSearchParams): Promise<ChatsListResponse | ChatRow[]> {
  const r = await apiFetch(`/chats?${params.toString()}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function postSyncChats(): Promise<{ message: string }> {
  const r = await apiFetch('/chats/sync', { method: 'POST' });
  if (!r.ok) {
    let detail = r.statusText;
    try {
      const j = await r.json();
      detail = j.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return r.json();
}
