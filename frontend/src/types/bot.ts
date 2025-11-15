export interface BotInfo {
  type: string
  name: string
  description: string
  config_schema: Record<string, unknown>
  ui_schema?: Record<string, unknown>
}

export interface Bot {
  id: string
  type: string
  name: string
  description: string | null
  config: Record<string, unknown>
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface BotCreate {
  type: string
  name: string
  description?: string
  config?: Record<string, unknown>
  enabled?: boolean
}

export interface BotUpdate {
  name?: string
  description?: string
  config?: Record<string, unknown>
  enabled?: boolean
}

export interface BotListResponse {
  bots: Bot[]
  total: number
}

export interface BotTypeInfo {
  type: string
  info: BotInfo
}

