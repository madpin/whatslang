import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Plus, Trash2, ChevronUp, ChevronDown } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useChat, useChatBots, useUpdateBotAssignment, useRemoveBot } from '@/hooks/useChats'
import { useBots } from '@/hooks/useBots'
import AssignBotDialog from '@/components/chats/AssignBotDialog'

export default function ChatDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: chat, isLoading: chatLoading } = useChat(id!)
  const { data: assignments, isLoading: assignmentsLoading } = useChatBots(id!)
  const { data: botsData } = useBots()
  const updateAssignment = useUpdateBotAssignment()
  const removeBot = useRemoveBot()

  const [showDialog, setShowDialog] = useState(false)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const availableBots = botsData?.bots.filter(bot =>
    !assignments?.some(a => a.bot_id === bot.id)
  ) || []

  const sortedAssignments = assignments?.slice().sort((a, b) => a.priority - b.priority) || []

  const handleToggleEnabled = (botId: string, enabled: boolean) => {
    if (!id) return
    updateAssignment.mutate({
      chatId: id,
      botId,
      assignment: { enabled: !enabled }
    })
  }

  const handleDelete = () => {
    if (!id || !deleteId) return
    removeBot.mutate(
      { chatId: id, botId: deleteId },
      {
        onSuccess: () => setDeleteId(null)
      }
    )
  }

  const handlePriorityChange = (botId: string, delta: number) => {
    if (!id) return
    const assignment = assignments?.find(a => a.bot_id === botId)
    if (!assignment) return

    const newPriority = Math.max(1, assignment.priority + delta)
    updateAssignment.mutate({
      chatId: id,
      botId,
      assignment: { priority: newPriority }
    })
  }

  if (chatLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!chat) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold mb-2">Chat not found</h2>
        <Button onClick={() => navigate('/chats')}>
          Back to Chats
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/chats')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">{chat.name}</h1>
          <p className="text-muted-foreground">
            <code className="text-sm">{chat.jid}</code>
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Chat Information</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div>
            <Label className="text-muted-foreground">Type</Label>
            <Badge className="mt-1">{chat.chat_type}</Badge>
          </div>
          <div>
            <Label className="text-muted-foreground">Created</Label>
            <p className="mt-1 text-sm">
              {new Date(chat.created_at).toLocaleString()}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Assigned Bots</CardTitle>
              <CardDescription>
                Bots attached to this chat (ordered by priority)
              </CardDescription>
            </div>
            <Button onClick={() => setShowDialog(true)} disabled={availableBots.length === 0}>
              <Plus className="mr-2 h-4 w-4" />
              Assign Bot
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {assignmentsLoading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : sortedAssignments.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground mb-4">No bots assigned yet</p>
              <Button onClick={() => setShowDialog(true)} disabled={availableBots.length === 0}>
                <Plus className="mr-2 h-4 w-4" />
                Assign Bot
              </Button>
              <Button variant="link" asChild>
                <Link to="/bot-attribution">
                  Open Bot Attribution workspace
                </Link>
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Priority</TableHead>
                  <TableHead>Bot</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedAssignments.map((assignment) => {
                  const bot = botsData?.bots.find(b => b.id === assignment.bot_id)
                  return (
                    <TableRow key={assignment.id}>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Badge variant="outline">{assignment.priority}</Badge>
                          <div className="flex flex-col">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-4 w-4"
                              onClick={() => handlePriorityChange(assignment.bot_id, -1)}
                              disabled={assignment.priority === 1}
                            >
                              <ChevronUp className="h-3 w-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-4 w-4"
                              onClick={() => handlePriorityChange(assignment.bot_id, 1)}
                            >
                              <ChevronDown className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{bot?.name || 'Unknown Bot'}</div>
                          <div className="text-sm text-muted-foreground">
                            {bot?.type}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={assignment.enabled ? 'default' : 'secondary'}>
                          {assignment.enabled ? 'Enabled' : 'Disabled'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Switch
                            checked={assignment.enabled}
                            onCheckedChange={() => handleToggleEnabled(assignment.bot_id, assignment.enabled)}
                          />
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setDeleteId(assignment.bot_id)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <AssignBotDialog
        chatId={chat.id}
        open={showDialog}
        onOpenChange={setShowDialog}
        availableBots={availableBots}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove Bot</DialogTitle>
            <DialogDescription>
              Are you sure you want to remove this bot from this chat?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              Remove
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

