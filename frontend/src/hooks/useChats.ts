import { useQuery, useMutation, useQueryClient, useQueries } from '@tanstack/react-query'
import {
  getChats,
  getChat,
  createChat,
  updateChat,
  syncChat,
  syncAllChats,
  previewWhatsAppChats,
  importSelectedChats,
  deleteChat,
  bulkDeleteUnassignedChats,
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
  WhatsAppChatPreview,
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

export const useSyncAllChats = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => syncAllChats(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['chats'] })
      toast.success(`Synced ${data.total} chats (${data.created} new, ${data.updated} updated)`)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to sync chats from WhatsApp')
    },
  })
}

export const usePreviewChats = () => {
  return useQuery<WhatsAppChatPreview[]>({
    queryKey: ['chats', 'preview'],
    queryFn: () => previewWhatsAppChats(),
    enabled: false, // Only fetch when explicitly requested
    staleTime: 0, // Always fetch fresh data
  })
}

export const useImportSelectedChats = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (jids: string[]) => importSelectedChats(jids),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['chats'] })
      toast.success(`Imported ${data.total} chats (${data.created} new, ${data.updated} updated)`)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to import selected chats')
    },
  })
}

export const useDeleteChat = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => deleteChat(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chats'] })
      toast.success('Chat deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete chat')
    },
  })
}

export const useBulkDeleteUnassignedChats = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => bulkDeleteUnassignedChats(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['chats'] })
      toast.success(data.message)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete unassigned chats')
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

