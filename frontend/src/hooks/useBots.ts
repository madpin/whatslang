import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getBots, getBot, createBot, updateBot, deleteBot, getBotTypes } from '@/services/api'
import type { BotCreate, BotUpdate } from '@/types/bot'
import { toast } from 'sonner'

export const useBots = (refetchInterval?: number) => {
  return useQuery({
    queryKey: ['bots'],
    queryFn: () => getBots(),
    refetchInterval,
  })
}

export const useBot = (id: string) => {
  return useQuery({
    queryKey: ['bots', id],
    queryFn: () => getBot(id),
    enabled: !!id,
  })
}

export const useBotTypes = () => {
  return useQuery({
    queryKey: ['bot-types'],
    queryFn: () => getBotTypes(),
  })
}

export const useCreateBot = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (bot: BotCreate) => createBot(bot),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] })
      toast.success('Bot created successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create bot')
    },
  })
}

export const useUpdateBot = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, bot }: { id: string; bot: BotUpdate }) => updateBot(id, bot),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['bots'] })
      queryClient.invalidateQueries({ queryKey: ['bots', variables.id] })
      toast.success('Bot updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update bot')
    },
  })
}

export const useDeleteBot = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => deleteBot(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots'] })
      toast.success('Bot deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete bot')
    },
  })
}

