export type ChatType = "group" | "private"

export interface Chat {
  id: string
  jid: string
  name: string
  chat_type: ChatType
  chat_metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface ChatCreate {
  jid: string
  name: string
  chat_type: ChatType
  chat_metadata?: Record<string, unknown>
}

export interface ChatUpdate {
  name?: string
  chat_type?: ChatType
  chat_metadata?: Record<string, unknown>
}

export interface ChatListResponse {
  chats: Chat[]
  total: number
}

export interface ChatBotAssignment {
  id: string
  chat_id: string
  bot_id: string
  config_override: Record<string, unknown>
  enabled: boolean
  priority: number
  created_at: string
}

export interface ChatBotAssignmentCreate {
  bot_id: string
  config_override?: Record<string, unknown>
  enabled?: boolean
  priority?: number
}

export interface ChatBotAssignmentUpdate {
  config_override?: Record<string, unknown>
  enabled?: boolean
  priority?: number
}

