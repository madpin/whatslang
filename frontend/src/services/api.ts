import axios from 'axios'
import type { Bot, BotCreate, BotUpdate, BotListResponse, BotTypeInfo } from '@/types/bot'
import type { Chat, ChatCreate, ChatUpdate, ChatListResponse, ChatBotAssignment, ChatBotAssignmentCreate, ChatBotAssignmentUpdate } from '@/types/chat'
import type { Schedule, ScheduleCreate, ScheduleUpdate, ScheduleListResponse, ScheduleRunResponse } from '@/types/schedule'
import type { MessageListResponse, SendMessageRequest, SendMessageResponse } from '@/types/message'
import type { HealthResponse } from '@/types/common'

// In production (Docker), API is proxied through Nginx at the same origin
// In development, use VITE_API_BASE_URL or default to localhost:8000
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '')

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Health
export const getHealth = async (): Promise<HealthResponse> => {
  const { data } = await api.get('/health')
  return data
}

// Bots
export const getBots = async (skip = 0, limit = 100): Promise<BotListResponse> => {
  const { data } = await api.get('/api/bots', { params: { skip, limit } })
  return data
}

export const getBot = async (id: string): Promise<Bot> => {
  const { data } = await api.get(`/api/bots/${id}`)
  return data
}

export const createBot = async (bot: BotCreate): Promise<Bot> => {
  const { data } = await api.post('/api/bots', bot)
  return data
}

export const updateBot = async (id: string, bot: BotUpdate): Promise<Bot> => {
  const { data } = await api.put(`/api/bots/${id}`, bot)
  return data
}

export const deleteBot = async (id: string): Promise<void> => {
  await api.delete(`/api/bots/${id}`)
}

export const getBotTypes = async (): Promise<BotTypeInfo[]> => {
  const { data } = await api.get('/api/bots/types')
  return data
}

// Chats
export const getChats = async (skip = 0, limit = 100): Promise<ChatListResponse> => {
  const { data } = await api.get('/api/chats', { params: { skip, limit } })
  return data
}

export const getChat = async (id: string): Promise<Chat> => {
  const { data } = await api.get(`/api/chats/${id}`)
  return data
}

export const createChat = async (chat: ChatCreate): Promise<Chat> => {
  const { data } = await api.post('/api/chats', chat)
  return data
}

export const updateChat = async (id: string, chat: ChatUpdate): Promise<Chat> => {
  const { data } = await api.put(`/api/chats/${id}`, chat)
  return data
}

export const syncChat = async (id: string): Promise<Chat> => {
  const { data } = await api.post(`/api/chats/${id}/sync`)
  return data
}

export const syncAllChats = async (): Promise<{ message: string; created: number; updated: number; total: number }> => {
  const { data } = await api.post('/api/chats/sync-all')
  return data
}

// Chat Bot Assignments
export const getChatBots = async (chatId: string): Promise<ChatBotAssignment[]> => {
  const { data } = await api.get(`/api/chats/${chatId}/bots`)
  return data
}

export const assignBotToChat = async (
  chatId: string,
  assignment: ChatBotAssignmentCreate
): Promise<ChatBotAssignment> => {
  const { data } = await api.post(`/api/chats/${chatId}/bots`, assignment)
  return data
}

export const updateChatBotAssignment = async (
  chatId: string,
  botId: string,
  assignment: ChatBotAssignmentUpdate
): Promise<ChatBotAssignment> => {
  const { data } = await api.put(`/api/chats/${chatId}/bots/${botId}`, assignment)
  return data
}

export const removeBotFromChat = async (chatId: string, botId: string): Promise<void> => {
  await api.delete(`/api/chats/${chatId}/bots/${botId}`)
}

// Schedules
export const getSchedules = async (skip = 0, limit = 100): Promise<ScheduleListResponse> => {
  const { data } = await api.get('/api/schedules', { params: { skip, limit } })
  return data
}

export const getSchedule = async (id: string): Promise<Schedule> => {
  const { data } = await api.get(`/api/schedules/${id}`)
  return data
}

export const createSchedule = async (schedule: ScheduleCreate): Promise<Schedule> => {
  const { data } = await api.post('/api/schedules', schedule)
  return data
}

export const updateSchedule = async (id: string, schedule: ScheduleUpdate): Promise<Schedule> => {
  const { data } = await api.put(`/api/schedules/${id}`, schedule)
  return data
}

export const deleteSchedule = async (id: string): Promise<void> => {
  await api.delete(`/api/schedules/${id}`)
}

export const triggerSchedule = async (id: string): Promise<ScheduleRunResponse> => {
  const { data } = await api.post(`/api/schedules/${id}/run`)
  return data
}

// Messages
export const getMessages = async (skip = 0, limit = 100): Promise<MessageListResponse> => {
  const { data } = await api.get('/api/messages', { params: { skip, limit } })
  return data
}

export const sendMessage = async (message: SendMessageRequest): Promise<SendMessageResponse> => {
  const { data } = await api.post('/api/messages/send', message)
  return data
}

export default api

