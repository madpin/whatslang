import { useEffect, useState } from 'react'
import type { Bot } from '@/types/bot'
import type { ChatBotAssignmentCreate } from '@/types/chat'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { useAssignBot } from '@/hooks/useChats'

interface AssignBotDialogProps {
  chatId: string
  open: boolean
  onOpenChange: (open: boolean) => void
  availableBots: Bot[]
  onAssigned?: () => void
}

const defaultForm: ChatBotAssignmentCreate = {
  bot_id: '',
  priority: 1,
  enabled: true,
}

export default function AssignBotDialog({
  chatId,
  open,
  onOpenChange,
  availableBots,
  onAssigned,
}: AssignBotDialogProps) {
  const assignBot = useAssignBot()
  const [formData, setFormData] = useState<ChatBotAssignmentCreate>(defaultForm)

  useEffect(() => {
    if (!open) {
      setFormData(defaultForm)
    }
  }, [open])

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    if (!chatId || !formData.bot_id) {
      return
    }

    assignBot.mutate(
      { chatId, assignment: formData },
      {
        onSuccess: () => {
          setFormData(defaultForm)
          onOpenChange(false)
          onAssigned?.()
        },
      },
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Assign Bot</DialogTitle>
            <DialogDescription>Attach an existing bot to this chat.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="bot-select">Bot *</Label>
              <Select
                id="bot-select"
                required
                value={formData.bot_id}
                onChange={(event) =>
                  setFormData((prev) => ({
                    ...prev,
                    bot_id: event.target.value,
                  }))
                }
                disabled={availableBots.length === 0 || assignBot.isPending}
              >
                <option value="">Select a bot</option>
                {availableBots.map((bot) => (
                  <option key={bot.id} value={bot.id}>
                    {bot.name} ({bot.type})
                  </option>
                ))}
              </Select>
              {availableBots.length === 0 && (
                <p className="text-xs text-muted-foreground">All bots have been assigned to this chat.</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="priority-input">Priority</Label>
              <Input
                id="priority-input"
                type="number"
                min={1}
                value={formData.priority ?? 1}
                onChange={(event) =>
                  setFormData((prev) => ({
                    ...prev,
                    priority: Number(event.target.value),
                  }))
                }
              />
              <p className="text-xs text-muted-foreground">Lower numbers run first.</p>
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="enabled-toggle">Enable Bot</Label>
              <Switch
                id="enabled-toggle"
                checked={formData.enabled ?? true}
                onCheckedChange={(checked) =>
                  setFormData((prev) => ({
                    ...prev,
                    enabled: checked,
                  }))
                }
                disabled={assignBot.isPending}
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={assignBot.isPending || availableBots.length === 0}>
              {assignBot.isPending ? 'Assigning...' : 'Assign Bot'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}


