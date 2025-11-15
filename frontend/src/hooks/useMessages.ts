import { useQuery, useMutation } from '@tanstack/react-query'
import { getMessages, sendMessage } from '@/services/api'
import type { SendMessageRequest } from '@/types/message'
import { toast } from 'sonner'

export const useMessages = (refetchInterval?: number) => {
  return useQuery({
    queryKey: ['messages'],
    queryFn: () => getMessages(),
    refetchInterval,
  })
}

export const useSendMessage = () => {
  return useMutation({
    mutationFn: (message: SendMessageRequest) => sendMessage(message),
    onSuccess: () => {
      toast.success('Message sent successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to send message')
    },
  })
}

