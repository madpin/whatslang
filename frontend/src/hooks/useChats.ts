import { useQuery, useMutation, useQueryClient, useQueries } from '@tanstack/react-query'
import {
  getChats,
  getChat,
  createChat,
  updateChat,
  syncChat,
  getChatBots,
  assignBotToChat,
  updateChatBotAssignment,
  removeBotFromChat,
} from '@/services/api'
import type {
  ChatCreate,
  ChatUpdate,
  ChatBotAssignmentCreate,
  ChatBotAssignmentUpdate,
  ChatBotAssignment,
} from '@/types/chat'
import { toast } from 'sonner'

export const useChats = (refetchInterval?: number) => {
  return useQuery({
    queryKey: ['chats'],
    queryFn: () => getChats(),
    refetchInterval,
  })
}

export const useChat = (id: string) => {
  return useQuery({
    queryKey: ['chats', id],
    queryFn: () => getChat(id),
    enabled: !!id,
  })
}

export const useCreateChat = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (chat: ChatCreate) => createChat(chat),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chats'] })
      toast.success('Chat registered successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to register chat')
    },
  })
}

export const useUpdateChat = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, chat }: { id: string; chat: ChatUpdate }) => updateChat(id, chat),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chats'] })
      queryClient.invalidateQueries({ queryKey: ['chats', variables.id] })
      toast.success('Chat updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update chat')
    },
  })
}

export const useSyncChat = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => syncChat(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['chats'] })
      queryClient.invalidateQueries({ queryKey: ['chats', id] })
      toast.success('Chat synced successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to sync chat')
    },
  })
}

export const useChatBots = (chatId: string) => {
  return useQuery({
    queryKey: ['chats', chatId, 'bots'],
    queryFn: () => getChatBots(chatId),
    enabled: !!chatId,
  })
}

export const useAssignBot = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ chatId, assignment }: { chatId: string; assignment: ChatBotAssignmentCreate }) =>
      assignBotToChat(chatId, assignment),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chats', variables.chatId, 'bots'] })
      toast.success('Bot assigned successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to assign bot')
    },
  })
}

export const useUpdateBotAssignment = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      chatId,
      botId,
      assignment,
    }: {
      chatId: string
      botId: string
      assignment: ChatBotAssignmentUpdate
    }) => updateChatBotAssignment(chatId, botId, assignment),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chats', variables.chatId, 'bots'] })
      toast.success('Bot assignment updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update bot assignment')
    },
  })
}

export const useRemoveBot = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ chatId, botId }: { chatId: string; botId: string }) => removeBotFromChat(chatId, botId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chats', variables.chatId, 'bots'] })
      toast.success('Bot removed successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to remove bot')
    },
  })
}

export const useChatAssignmentsMap = (chatIds: string[]) => {
  const results = useQueries({
    queries: chatIds.map((chatId) => ({
      queryKey: ['chats', chatId, 'bots'],
      queryFn: () => getChatBots(chatId),
      enabled: !!chatId,
      staleTime: 10000,
    })),
  })

  const assignmentsByChat = chatIds.reduce<Record<string, ChatBotAssignment[]>>((acc, chatId, index) => {
    acc[chatId] = results[index]?.data ?? []
    return acc
  }, {})

  return {
    assignmentsByChat,
    isLoading: results.some((result) => result.isLoading),
    isFetching: results.some((result) => result.isFetching),
  }
}

