export interface Message {
  id: string
  chat_jid: string
  sender_jid: string
  content: string
  timestamp: string
  message_type: string
  metadata: Record<string, unknown>
}

export interface MessageListResponse {
  messages: Message[]
  total: number
}

export interface SendMessageRequest {
  chat_jid: string
  message: string
}

export interface SendMessageResponse {
  success: boolean
  message_id?: string
  error?: string
}

