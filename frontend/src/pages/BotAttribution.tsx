import { useMemo, useState } from 'react'
import { ChevronDown, ChevronUp, Layers, ListPlus, Plus, Shuffle, Trash2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Switch } from '@/components/ui/switch'
import { useBots } from '@/hooks/useBots'
import { useChats, useChatAssignmentsMap, useUpdateBotAssignment, useRemoveBot } from '@/hooks/useChats'
import AssignBotDialog from '@/components/chats/AssignBotDialog'
import GuideHint from '@/components/ui/guide-hint'
import type { ChatBotAssignment } from '@/types/chat'
import type { Bot } from '@/types/bot'

const statCards = [
  {
    key: 'missing',
    title: 'Chats needing bots',
    description: 'Chats without any bot attribution',
    icon: ListPlus,
  },
  {
    key: 'assignments',
    title: 'Total assignments',
    description: 'Combined chat → bot mappings',
    icon: Layers,
  },
  {
    key: 'activeBots',
    title: 'Active bots',
    description: 'Enabled bots ready to assign',
    icon: Shuffle,
  },
]

const sortAssignments = (assignments: ChatBotAssignment[]) =>
  assignments.slice().sort((a, b) => a.priority - b.priority)

export default function BotAttribution() {
  const { data: chatsData, isLoading: chatsLoading } = useChats(20000)
  const { data: botsData, isLoading: botsLoading } = useBots(20000)
  const chatIds = chatsData?.chats.map((chat) => chat.id) ?? []
  const { assignmentsByChat, isLoading: assignmentsLoading } = useChatAssignmentsMap(chatIds)

  const updateAssignment = useUpdateBotAssignment()
  const removeBot = useRemoveBot()

  const [search, setSearch] = useState('')
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<{ chatId: string; botId: string } | null>(null)

  const chats = chatsData?.chats ?? []
  const bots = botsData?.bots ?? []

  const botsById = useMemo(
    () =>
      bots.reduce<Record<string, Bot>>((acc, bot) => {
        acc[bot.id] = bot
        return acc
      }, {}),
    [bots],
  )

  const filteredChats = useMemo(() => {
    if (!search.trim()) {
      return chats
    }
    return chats.filter(
      (chat) =>
        chat.name.toLowerCase().includes(search.toLowerCase()) ||
        chat.jid.toLowerCase().includes(search.toLowerCase()),
    )
  }, [chats, search])

  const totals = useMemo(() => {
    const assignmentsCount = chats.reduce((sum, chat) => sum + (assignmentsByChat[chat.id]?.length ?? 0), 0)
    const chatsNeedingBots = chats.filter((chat) => (assignmentsByChat[chat.id]?.length ?? 0) === 0).length
    const activeBots = bots.filter((bot) => bot.enabled).length

    return {
      assignmentsCount,
      chatsNeedingBots,
      activeBots,
    }
  }, [assignmentsByChat, bots, chats])

  const isTableLoading = chatsLoading || assignmentsLoading

  const handlePriorityChange = (chatId: string, botId: string, delta: number) => {
    const assignments = assignmentsByChat[chatId] ?? []
    const target = assignments.find((assignment) => assignment.bot_id === botId)
    if (!target) return

    const newPriority = Math.max(1, target.priority + delta)
    updateAssignment.mutate({
      chatId,
      botId,
      assignment: { priority: newPriority },
    })
  }

  const handleToggle = (chatId: string, botId: string) => {
    const assignments = assignmentsByChat[chatId] ?? []
    const target = assignments.find((assignment) => assignment.bot_id === botId)
    if (!target) return

    updateAssignment.mutate({
      chatId,
      botId,
      assignment: { enabled: !target.enabled },
    })
  }

  const handleDelete = () => {
    if (!deleteTarget) return
    removeBot.mutate(deleteTarget, {
      onSuccess: () => setDeleteTarget(null),
    })
  }

  const getAvailableBots = (chatId: string) => {
    const assignedIds = new Set((assignmentsByChat[chatId] ?? []).map((assignment) => assignment.bot_id))
    return bots.filter((bot) => !assignedIds.has(bot.id))
  }

  const availableBotsForSelected = selectedChatId ? getAvailableBots(selectedChatId) : []

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Bot Attribution</h1>
          <p className="text-muted-foreground">
            Map bots to chats from a single workspace. Assign, reorder, and toggle automations without leaving this page.
          </p>
        </div>
        <GuideHint
          hintKey="bot-attribution.overview"
          title="Need to attach a bot quickly?"
          description="Pick a chat from the table and click Assign Bot. You can reorder bots with the arrows and pause automation with the toggle."
        />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {statCards.map((card) => {
          const Icon = card.icon
          const value =
            card.key === 'missing'
              ? totals.chatsNeedingBots
              : card.key === 'assignments'
                ? totals.assignmentsCount
                : totals.activeBots

          const loading = chatsLoading || botsLoading || assignmentsLoading

          return (
            <Card key={card.key}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
                <Icon className="h-4 w-4 text-primary" aria-hidden="true" />
              </CardHeader>
              <CardContent>
                {loading ? <Skeleton className="h-8 w-16" /> : <div className="text-2xl font-bold">{value}</div>}
                <p className="text-xs text-muted-foreground mt-1">{card.description}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <Card>
        <CardHeader className="space-y-4">
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle>Chat Bot Mapping</CardTitle>
              <CardDescription>Review every chat, the bots attached to it, and adjust priorities in seconds.</CardDescription>
            </div>
            <GuideHint
              hintKey="bot-attribution.table"
              title="Pro tip"
              description="Use the search box to focus on a single chat, then assign or reorder bots without opening the chat detail view."
            />
          </div>
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <Input
              placeholder="Search chats by name or JID..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              className="md:max-w-sm"
            />
            <p className="text-xs text-muted-foreground">
              Showing {filteredChats.length} of {chats.length} chats
            </p>
          </div>
        </CardHeader>
        <CardContent>
          {isTableLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, index) => (
                <Skeleton key={index} className="h-20 w-full" />
              ))}
            </div>
          ) : filteredChats.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground mb-2">No chats match your search.</p>
              <p className="text-xs text-muted-foreground">Try adjusting the filters or register a new chat.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Chat</TableHead>
                  <TableHead>Assigned bots</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredChats.map((chat) => {
                  const assignments = sortAssignments(assignmentsByChat[chat.id] ?? [])
                  const availableBots = getAvailableBots(chat.id)
                  return (
                    <TableRow key={chat.id}>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">{chat.name}</span>
                            {assignments.length === 0 && <Badge variant="secondary">Needs bot</Badge>}
                          </div>
                          <p className="text-xs text-muted-foreground">
                            <code>{chat.jid}</code>
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        {assignments.length === 0 ? (
                          <p className="text-sm text-muted-foreground">No bots assigned</p>
                        ) : (
                          <div className="space-y-2">
                            {assignments.map((assignment) => {
                              const bot = botsById[assignment.bot_id]
                              return (
                                <div
                                  key={assignment.id}
                                  className="rounded-md border border-border p-3 space-y-2"
                                >
                                  <div className="flex items-center justify-between gap-2">
                                    <div>
                                      <p className="text-sm font-medium">{bot?.name ?? 'Unknown bot'}</p>
                                      <p className="text-xs text-muted-foreground">
                                        Priority {assignment.priority} • {bot?.type ?? 'N/A'}
                                      </p>
                                    </div>
                                    <Badge variant={assignment.enabled ? 'default' : 'secondary'}>
                                      {assignment.enabled ? 'Enabled' : 'Paused'}
                                    </Badge>
                                  </div>
                                  <div className="flex items-center justify-between gap-3">
                                    <div className="flex items-center gap-1">
                                      <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-7 w-7"
                                        onClick={() => handlePriorityChange(chat.id, assignment.bot_id, -1)}
                                        disabled={assignment.priority === 1 || updateAssignment.isPending}
                                        aria-label="Increase priority"
                                      >
                                        <ChevronUp className="h-4 w-4" />
                                      </Button>
                                      <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-7 w-7"
                                        onClick={() => handlePriorityChange(chat.id, assignment.bot_id, 1)}
                                        disabled={updateAssignment.isPending}
                                        aria-label="Decrease priority"
                                      >
                                        <ChevronDown className="h-4 w-4" />
                                      </Button>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <Switch
                                        checked={assignment.enabled}
                                        onCheckedChange={() => handleToggle(chat.id, assignment.bot_id)}
                                        disabled={updateAssignment.isPending}
                                        aria-label="Toggle bot"
                                      />
                                      <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => setDeleteTarget({ chatId: chat.id, botId: assignment.bot_id })}
                                      >
                                        <Trash2 className="h-4 w-4 text-destructive" />
                                      </Button>
                                    </div>
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <p className="text-sm font-medium">{assignments.length} bot(s)</p>
                          <p className="text-xs text-muted-foreground">
                            {assignments.filter((assignment) => assignment.enabled).length} active
                          </p>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setSelectedChatId(chat.id)}
                            disabled={availableBots.length === 0}
                          >
                            <Plus className="mr-2 h-4 w-4" />
                            Assign Bot
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

      {selectedChatId && (
        <AssignBotDialog
          chatId={selectedChatId}
          open
          onOpenChange={(open) => {
            if (!open) {
              setSelectedChatId(null)
            }
          }}
          availableBots={availableBotsForSelected}
        />
      )}

      <Dialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove bot assignment</DialogTitle>
            <DialogDescription>Are you sure you want to detach this bot from the chat?</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={removeBot.isPending}>
              Remove
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}


