export interface AuthStatus {
  auth_required: boolean;
  user: string | null;
}

export interface BotSupports {
  text: boolean;
  image: boolean;
  audio: boolean;
  video: boolean;
}

export interface BotType {
  name: string;
  label: string;
  prefix: string;
  emoji: string;
  description: string;
  supports: BotSupports;
}

export interface BotStatus extends BotType {
  chat_jid: string;
  status: 'running' | 'stopped';
  uptime_seconds: number | null;
  answer_owner_messages: boolean;
  context_message_count: number;
  response_chat_jid: string | null;
  source_device_id: string | null;
  target_device_id: string | null;
}

export interface DeviceInfo {
  id: string;
  label: string;
  is_default: boolean;
}

export interface BotLogEntry {
  timestamp: string;
  level: string;
  message: string;
}

export interface BotLogs {
  bot_name: string;
  chat_jid: string;
  logs: BotLogEntry[];
}

export interface Chat {
  chat_jid: string;
  chat_name: string;
  is_manual: boolean;
  is_group: boolean;
  last_synced: string | null;
  last_message_time: string | null;
  message_count: number;
  added_at: string;
}

export interface ChatWithBots extends Chat {
  bots: BotStatus[];
}

export interface ChatBrief {
  chat_jid: string;
  chat_name: string;
}

export interface Pagination {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface ChatListResponse {
  chats: ChatWithBots[];
  pagination: Pagination;
}

export interface Stats {
  total_chats: number;
  running_bots: number;
  available_bot_types: number;
  active_chats_24h: number;
}

export interface SystemInfo {
  version: string;
  environment: string;
  auth_required: boolean;
  whatsapp_base_url: string | null;
  openai_model: string;
  openai_vision_model: string;
  openai_audio_model: string;
  poll_interval: number;
  db_path: string;
}

export interface BotSettingsUpdate {
  answer_owner_messages?: boolean;
  context_message_count?: number;
  response_chat_jid?: string | null;
  source_device_id?: string | null;
  target_device_id?: string | null;
}

export interface GatewayDiagnostics {
  base_url: string | null;
  reachable: boolean;
  http_status: number | null;
  latency_ms: number | null;
  is_connected: boolean;
  is_logged_in: boolean;
  device_id: string | null;
  error: string | null;
  last_call_at: string | null;
  last_error_at: string | null;
  call_count: number;
  error_count: number;
}

export type LlmSurface = 'text' | 'vision' | 'audio' | 'video';

export interface LlmSurfaceActivity {
  surface: LlmSurface;
  model: string | null;
  call_count: number;
  success_count: number;
  error_count: number;
  last_call_at: string | null;
  last_success_at: string | null;
  last_error_at: string | null;
  last_error_message: string | null;
  last_latency_ms: number | null;
}

export interface LlmDiagnostics {
  base_url: string | null;
  text_model: string;
  vision_model: string;
  audio_model: string;
  api_key_set: boolean;
  surfaces: LlmSurfaceActivity[];
}

export type InboundMediaType =
  | 'text'
  | 'image'
  | 'audio'
  | 'video'
  | 'document'
  | 'sticker'
  | 'other';

export interface InboundObservation {
  media_type: InboundMediaType;
  last_seen_at: string | null;
  last_chat_jid: string | null;
  last_chat_name: string | null;
  last_sender: string | null;
  total_count: number;
}

export interface DatabaseDiagnostics {
  path: string;
  size_bytes: number;
  chats: number;
  assignments: number;
  processed_messages: number;
}

export interface BotsDiagnostics {
  catalog_size: number;
  running: number;
  poll_interval: number;
}

export interface GatewayErrorEntry {
  timestamp: string;
  where: string;
  status: number | null;
  message: string;
}

export interface Diagnostics {
  timestamp: string;
  version: string;
  environment: string;
  gateway: GatewayDiagnostics;
  llm: LlmDiagnostics;
  database: DatabaseDiagnostics;
  bots: BotsDiagnostics;
  inbound: InboundObservation[];
  recent_errors: GatewayErrorEntry[];
}
