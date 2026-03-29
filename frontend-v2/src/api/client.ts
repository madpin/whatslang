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

/* ---- Types ---- */

export type StatsResponse = {
  total_chats: number;
  running_bots: number;
  stopped_bots: number;
  available_bot_types: number;
};

export type BotInfo = {
  name: string;
  chat_jid: string;
  display_name: string;
  prefix: string;
  status: string;
  uptime_seconds?: number;
  answer_owner_messages?: boolean;
  context_message_count?: number;
};

export type BotType = {
  name: string;
  display_name: string;
  prefix: string;
  description: string;
  system_prompt: string;
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

/* ---- Stats ---- */

export async function fetchStats(): Promise<StatsResponse> {
  const r = await apiFetch('/stats');
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

/* ---- Chats ---- */

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

/* ---- Bot Types ---- */

export async function fetchBotTypes(): Promise<BotType[]> {
  const r = await apiFetch('/bots/types');
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

/* ---- Bot Instances (running) ---- */

export async function fetchRunningBots(): Promise<BotInfo[]> {
  const r = await apiFetch('/bots');
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

/* ---- Per-chat bots ---- */

export async function fetchBotsForChat(chatJid: string): Promise<BotInfo[]> {
  const r = await apiFetch(`/chats/${encodeURIComponent(chatJid)}/bots`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

/* ---- Start / Stop ---- */

export async function startBot(botName: string, chatJid: string): Promise<{ message: string }> {
  const r = await apiFetch(
    `/bots/${encodeURIComponent(botName)}/start?chat_jid=${encodeURIComponent(chatJid)}`,
    { method: 'POST' },
  );
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

export async function stopBot(botName: string, chatJid: string): Promise<{ message: string }> {
  const r = await apiFetch(
    `/bots/${encodeURIComponent(botName)}/stop?chat_jid=${encodeURIComponent(chatJid)}`,
    { method: 'POST' },
  );
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
