import { RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useHealth } from '@/hooks/useHealth'
import { useQueryClient } from '@tanstack/react-query'
import { Switch } from '@/components/ui/switch'
import useOnboardingHints from '@/hooks/useOnboardingHints'

export default function Header() {
  const { data: health, isLoading } = useHealth(30000)
  const queryClient = useQueryClient()
  const { hintsEnabled, setHintsEnabled, resetAllHints } = useOnboardingHints()

  const handleRefresh = () => {
    queryClient.invalidateQueries()
  }

  const handleToggleHints = (checked: boolean) => {
    if (checked) {
      resetAllHints()
    }
    setHintsEnabled(checked)
  }

  return (
    <header className="border-b border-border bg-card">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-semibold">WhatsApp Bot Management</h2>
          {!isLoading && health && (
            <Badge variant={health.status === 'healthy' ? 'default' : 'destructive'}>
              {health.status === 'healthy' ? '🟢 Online' : '🔴 Offline'}
            </Badge>
          )}
        </div>
        
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            className="gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          <div className="flex items-center gap-2 rounded-md border border-border px-3 py-1.5">
            <Switch
              id="tips-toggle"
              checked={hintsEnabled}
              onCheckedChange={handleToggleHints}
              className="scale-90"
            />
            <label htmlFor="tips-toggle" className="text-xs text-muted-foreground">
              Show tips
            </label>
          </div>
        </div>
      </div>
    </header>
  )
}

