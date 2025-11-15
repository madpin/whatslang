import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getSchedules, getSchedule, createSchedule, updateSchedule, deleteSchedule, triggerSchedule } from '@/services/api'
import type { ScheduleCreate, ScheduleUpdate } from '@/types/schedule'
import { toast } from 'sonner'

export const useSchedules = (refetchInterval?: number) => {
  return useQuery({
    queryKey: ['schedules'],
    queryFn: () => getSchedules(),
    refetchInterval,
  })
}

export const useSchedule = (id: string) => {
  return useQuery({
    queryKey: ['schedules', id],
    queryFn: () => getSchedule(id),
    enabled: !!id,
  })
}

export const useCreateSchedule = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (schedule: ScheduleCreate) => createSchedule(schedule),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      toast.success('Schedule created successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create schedule')
    },
  })
}

export const useUpdateSchedule = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, schedule }: { id: string; schedule: ScheduleUpdate }) => updateSchedule(id, schedule),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      queryClient.invalidateQueries({ queryKey: ['schedules', variables.id] })
      toast.success('Schedule updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update schedule')
    },
  })
}

export const useDeleteSchedule = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => deleteSchedule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      toast.success('Schedule deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete schedule')
    },
  })
}

export const useTriggerSchedule = () => {
  return useMutation({
    mutationFn: (id: string) => triggerSchedule(id),
    onSuccess: () => {
      toast.success('Schedule triggered successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to trigger schedule')
    },
  })
}

