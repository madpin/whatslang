import { api } from './client';
import type {
  AuthStatus,
  BotLogs,
  BotSettingsUpdate,
  BotStatus,
  BotType,
  Chat,
  ChatBrief,
  ChatListResponse,
  ChatWithBots,
  DeviceInfo,
  Diagnostics,
  Stats,
  SystemInfo,
} from './types';

export const Auth = {
  status: () => api.get<AuthStatus>('/api/auth/status'),
  login: (user: string, password: string) =>
    api.post<{ message: string }>('/api/auth/login', { user, password }),
  logout: () => api.post<{ message: string }>('/api/auth/logout'),
};

export const System = {
  info: () => api.get<SystemInfo>('/api/system'),
  stats: () => api.get<Stats>('/api/stats'),
  health: () => api.get<{ status: string }>('/api/health'),
  diagnostics: () => api.get<Diagnostics>('/api/diagnostics'),
};

export const Devices = {
  list: () => api.get<DeviceInfo[]>('/api/devices'),
};

export const Bots = {
  types: () => api.get<BotType[]>('/api/bots/types'),
  running: () => api.get<BotStatus[]>('/api/bots'),
  start: (name: string, chat_jid: string) =>
    api.post<{ message: string }>(`/api/bots/${name}/start`, undefined, {
      query: { chat_jid },
    }),
  stop: (name: string, chat_jid: string) =>
    api.post<{ message: string }>(`/api/bots/${name}/stop`, undefined, {
      query: { chat_jid },
    }),
  updateSettings: (name: string, chat_jid: string, body: BotSettingsUpdate) =>
    api.put<BotStatus>(`/api/bots/${name}/settings`, body, { query: { chat_jid } }),
  logs: (name: string, chat_jid: string, limit = 100) =>
    api.get<BotLogs>(`/api/bots/${name}/logs`, { query: { chat_jid, limit } }),
};

export interface ListChatsParams {
  page?: number;
  per_page?: number;
  sort?: string;
  order?: 'asc' | 'desc';
  activity?: 'active' | 'recent' | 'idle' | '';
  bot_status?: 'running' | 'none' | '';
  chat_type?: 'group' | 'individual' | '';
  search?: string;
}

export const Chats = {
  list: (params: ListChatsParams = {}) =>
    api.get<ChatListResponse>('/api/chats', { query: params as Record<string, string | number> }),
  all: (limit = 500) => api.get<ChatBrief[]>('/api/chats/all', { query: { limit } }),
  search: (q: string, limit = 30, chat_type: '' | 'group' | 'individual' = '') =>
    api.get<ChatBrief[]>('/api/chats/search', { query: { q, limit, chat_type } }),
  get: (chat_jid: string) => api.get<ChatWithBots>(`/api/chats/${encodeURIComponent(chat_jid)}`),
  add: (chat_jid: string, chat_name?: string) =>
    api.post<Chat>('/api/chats', { chat_jid, chat_name }),
  delete: (chat_jid: string) =>
    api.delete<{ message: string }>(`/api/chats/${encodeURIComponent(chat_jid)}`),
  sync: (device_id = '') =>
    api.post<{ message: string }>('/api/chats/sync', undefined, {
      query: device_id ? { device_id } : {},
    }),
  bulk: (action: 'start_bots' | 'stop_bots' | 'delete_chats', chat_jids: string[]) =>
    api.post<{ message: string }>('/api/chats/bulk', { action, chat_jids }),
  messages: (chat_jid: string, limit = 20) =>
    api.get<{ chat_jid: string; messages: unknown[]; count: number }>(
      `/api/chats/${encodeURIComponent(chat_jid)}/messages`,
      { query: { limit } },
    ),
};
