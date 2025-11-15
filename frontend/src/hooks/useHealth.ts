import { useQuery } from '@tanstack/react-query'
import { getHealth } from '@/services/api'

export const useHealth = (refetchInterval = 30000) => {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => getHealth(),
    refetchInterval,
  })
}

