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

async function handleError(r: Response): Promise<never> {
  let detail = r.statusText;
  try {
    const j = await r.json();
    detail = j.detail || j.message || detail;
  } catch { /* ignore */ }
  throw new Error(detail);
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
  response_chat_jid?: string | null;
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
  is_manual?: boolean;
  added_at?: string;
  bots: BotInfo[];
};

export type ChatsListResponse = {
  chats: ChatRow[];
  pagination?: { total: number; page: number; per_page: number; total_pages: number };
};

export type LogEntry = {
  timestamp: string;
  level: string;
  message: string;
};

export type BotLogsData = {
  bot_name: string;
  chat_jid: string;
  logs: LogEntry[];
};

export type ChatMessage = {
  id?: string;
  from_me?: boolean;
  is_from_me?: boolean;
  text?: string;
  body?: string;
  content?: string;
  timestamp?: string | number;
  sender?: string;
  sender_jid?: string;
  from?: string;
  type?: string;
  media_type?: string;
  mimetype?: string;
};

export function messageText(msg: ChatMessage): string {
  const t = msg.text ?? msg.body ?? msg.content;
  if (t) return t;
  const mediaType = msg.media_type ?? msg.mimetype?.split('/')[0];
  if (mediaType) return `[${mediaType}]`;
  if (msg.type && !['text', 'conversation', 'extendedTextMessage'].includes(msg.type)) {
    return `[${msg.type}]`;
  }
  return '[message]';
}

export function messageIsMe(msg: ChatMessage): boolean {
  return msg.from_me === true || msg.is_from_me === true;
}

export function isMediaMessage(msg: ChatMessage): boolean {
  const text = msg.text ?? msg.body ?? msg.content;
  if (!text && (msg.media_type || msg.mimetype)) return true;
  if (msg.type && !['text', 'conversation', 'extendedTextMessage'].includes(msg.type ?? '')) return true;
  return false;
}

export type BulkActionResult = {
  success: string[];
  failed: string[];
  total: number;
  message: string;
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

export async function fetchChat(chatJid: string): Promise<ChatRow> {
  const r = await apiFetch(`/chats/${encodeURIComponent(chatJid)}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function postSyncChats(): Promise<{ message: string }> {
  const r = await apiFetch('/chats/sync', { method: 'POST' });
  if (!r.ok) await handleError(r);
  return r.json();
}

export async function addChat(chatJid: string, chatName?: string): Promise<ChatRow> {
  const r = await apiFetch('/chats', {
    method: 'POST',
    body: JSON.stringify({ chat_jid: chatJid, chat_name: chatName }),
  });
  if (!r.ok) await handleError(r);
  return r.json();
}

export async function deleteChat(chatJid: string): Promise<{ message: string }> {
  const r = await apiFetch(`/chats/${encodeURIComponent(chatJid)}`, { method: 'DELETE' });
  if (!r.ok) await handleError(r);
  return r.json();
}

export async function fetchChatMessages(chatJid: string, limit = 30): Promise<ChatMessage[]> {
  const r = await apiFetch(`/chats/${encodeURIComponent(chatJid)}/messages?limit=${limit}`);
  if (!r.ok) throw new Error(await r.text());
  const data = await r.json();
  return data?.results?.messages ?? [];
}

export async function bulkAction(
  chatJids: string[],
  action: string,
  botName?: string,
): Promise<BulkActionResult> {
  const params = new URLSearchParams({ action });
  if (botName) params.set('bot_name', botName);
  const r = await apiFetch(`/chats/bulk-action?${params.toString()}`, {
    method: 'POST',
    body: JSON.stringify(chatJids),
  });
  if (!r.ok) await handleError(r);
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

export async function fetchChatsForBot(botName: string): Promise<ChatRow[]> {
  const r = await apiFetch(`/bots/${encodeURIComponent(botName)}/chats`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

/* ---- Bot Logs ---- */

export async function fetchBotLogs(
  botName: string,
  chatJid: string,
  limit = 100,
): Promise<BotLogsData> {
  const r = await apiFetch(
    `/bots/${encodeURIComponent(botName)}/logs?chat_jid=${encodeURIComponent(chatJid)}&limit=${limit}`,
  );
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

/* ---- Bot Settings ---- */

export async function updateBotSettings(
  botName: string,
  chatJid: string,
  settings: { answer_owner_messages?: boolean; context_message_count?: number; response_chat_jid?: string | null },
): Promise<{ message: string }> {
  const params = new URLSearchParams({ chat_jid: chatJid });
  if (settings.answer_owner_messages !== undefined) {
    params.set('answer_owner_messages', String(settings.answer_owner_messages));
  }
  if (settings.context_message_count !== undefined) {
    params.set('context_message_count', String(settings.context_message_count));
  }
  if (settings.response_chat_jid !== undefined) {
    params.set('response_chat_jid', settings.response_chat_jid ?? '');
  }
  const r = await apiFetch(`/bots/${encodeURIComponent(botName)}/settings?${params.toString()}`, {
    method: 'POST',
  });
  if (!r.ok) await handleError(r);
  return r.json();
}

/* ---- Start / Stop ---- */

export async function startBot(botName: string, chatJid: string): Promise<{ message: string }> {
  const r = await apiFetch(
    `/bots/${encodeURIComponent(botName)}/start?chat_jid=${encodeURIComponent(chatJid)}`,
    { method: 'POST' },
  );
  if (!r.ok) await handleError(r);
  return r.json();
}

export async function stopBot(botName: string, chatJid: string): Promise<{ message: string }> {
  const r = await apiFetch(
    `/bots/${encodeURIComponent(botName)}/stop?chat_jid=${encodeURIComponent(chatJid)}`,
    { method: 'POST' },
  );
  if (!r.ok) await handleError(r);
  return r.json();
}
