export type ScheduleType = "once" | "cron"

export interface Schedule {
  id: string
  chat_id: string
  message: string
  schedule_type: ScheduleType
  schedule_expression: string
  timezone: string
  enabled: boolean
  last_run_at: string | null
  next_run_at: string | null
  schedule_metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface ScheduleCreate {
  chat_id: string
  message: string
  schedule_type: ScheduleType
  schedule_expression: string
  timezone?: string
  enabled?: boolean
  schedule_metadata?: Record<string, unknown>
}

export interface ScheduleUpdate {
  message?: string
  schedule_type?: ScheduleType
  schedule_expression?: string
  timezone?: string
  enabled?: boolean
  schedule_metadata?: Record<string, unknown>
}

export interface ScheduleListResponse {
  schedules: Schedule[]
  total: number
}

export interface ScheduleRunResponse {
  success: boolean
  message?: string
  error?: string
}

