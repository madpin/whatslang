import { useState } from 'react'
import { Plus, Edit, Trash2, Play, Power, PowerOff } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
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
import { useSchedules, useCreateSchedule, useUpdateSchedule, useDeleteSchedule, useTriggerSchedule } from '@/hooks/useSchedules'
import { useChats } from '@/hooks/useChats'
import { formatDate } from '@/lib/utils'
import cronstrue from 'cronstrue'
import type { ScheduleCreate, ScheduleType } from '@/types/schedule'

export default function Schedules() {
  const { data, isLoading } = useSchedules(30000)
  const { data: chatsData } = useChats()
  const createSchedule = useCreateSchedule()
  const updateSchedule = useUpdateSchedule()
  const deleteSchedule = useDeleteSchedule()
  const triggerSchedule = useTriggerSchedule()

  const [showDialog, setShowDialog] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [formData, setFormData] = useState<ScheduleCreate>({
    chat_id: '',
    message: '',
    schedule_type: 'once',
    schedule_expression: '',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    enabled: true,
  })

  const filteredSchedules = data?.schedules.filter(schedule => {
    const chat = chatsData?.chats.find(c => c.id === schedule.chat_id)
    return (
      schedule.message.toLowerCase().includes(search.toLowerCase()) ||
      chat?.name.toLowerCase().includes(search.toLowerCase())
    )
  }) || []

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (editId) {
      updateSchedule.mutate(
        { id: editId, schedule: formData },
        {
          onSuccess: () => {
            setShowDialog(false)
            setEditId(null)
            resetForm()
          }
        }
      )
    } else {
      createSchedule.mutate(formData, {
        onSuccess: () => {
          setShowDialog(false)
          resetForm()
        }
      })
    }
  }

  const resetForm = () => {
    setFormData({
      chat_id: '',
      message: '',
      schedule_type: 'once',
      schedule_expression: '',
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      enabled: true,
    })
  }

  const handleEdit = (schedule: any) => {
    setEditId(schedule.id)
    setFormData({
      chat_id: schedule.chat_id,
      message: schedule.message,
      schedule_type: schedule.schedule_type,
      schedule_expression: schedule.schedule_expression,
      timezone: schedule.timezone,
      enabled: schedule.enabled,
    })
    setShowDialog(true)
  }

  const handleDelete = () => {
    if (deleteId) {
      deleteSchedule.mutate(deleteId, {
        onSuccess: () => setDeleteId(null)
      })
    }
  }

  const handleTrigger = (id: string) => {
    triggerSchedule.mutate(id)
  }

  const handleToggleEnabled = (id: string, enabled: boolean) => {
    updateSchedule.mutate({ id, schedule: { enabled: !enabled } })
  }

  const getCronDescription = (expression: string) => {
    try {
      return cronstrue.toString(expression)
    } catch {
      return 'Invalid cron expression'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Schedules</h1>
          <p className="text-muted-foreground">
            Schedule messages to be sent automatically
          </p>
        </div>
        <Button onClick={() => { setEditId(null); resetForm(); setShowDialog(true) }}>
          <Plus className="mr-2 h-4 w-4" />
          Create Schedule
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Schedules</CardTitle>
          <CardDescription>
            {data?.total || 0} schedule{data?.total !== 1 ? 's' : ''} configured
          </CardDescription>
          <div className="mt-4">
            <Input
              placeholder="Search schedules..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="max-w-sm"
            />
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : filteredSchedules.length === 0 ? (
            <div className="text-center py-12">
              <h3 className="text-lg font-semibold mb-2">No schedules found</h3>
              <p className="text-muted-foreground mb-4">
                {search ? 'Try adjusting your search' : 'Get started by creating your first schedule'}
              </p>
              {!search && (
                <Button onClick={() => { resetForm(); setShowDialog(true) }}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Schedule
                </Button>
              )}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Chat</TableHead>
                  <TableHead>Message</TableHead>
                  <TableHead>Schedule</TableHead>
                  <TableHead>Next Run</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredSchedules.map((schedule) => {
                  const chat = chatsData?.chats.find(c => c.id === schedule.chat_id)
                  return (
                    <TableRow key={schedule.id}>
                      <TableCell>
                        <div className="font-medium">{chat?.name || 'Unknown'}</div>
                      </TableCell>
                      <TableCell>
                        <div className="max-w-xs truncate">
                          {schedule.message}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <Badge variant="outline">
                            {schedule.schedule_type}
                          </Badge>
                          {schedule.schedule_type === 'cron' && (
                            <p className="text-xs text-muted-foreground">
                              {getCronDescription(schedule.schedule_expression)}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {schedule.next_run_at
                          ? formatDate(schedule.next_run_at, 'MMM d, HH:mm')
                          : 'N/A'}
                      </TableCell>
                      <TableCell>
                        <Badge variant={schedule.enabled ? 'default' : 'secondary'}>
                          {schedule.enabled ? 'Enabled' : 'Disabled'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleTrigger(schedule.id)}
                            title="Trigger now"
                          >
                            <Play className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleToggleEnabled(schedule.id, schedule.enabled)}
                            title={schedule.enabled ? 'Disable' : 'Enable'}
                          >
                            {schedule.enabled ? (
                              <PowerOff className="h-4 w-4" />
                            ) : (
                              <Power className="h-4 w-4" />
                            )}
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleEdit(schedule)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setDeleteId(schedule.id)}
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

      {/* Create/Edit Schedule Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-2xl">
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>{editId ? 'Edit Schedule' : 'Create Schedule'}</DialogTitle>
              <DialogDescription>
                Schedule a message to be sent automatically
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="chat_id">Chat *</Label>
                <Select
                  id="chat_id"
                  value={formData.chat_id}
                  onChange={(e) => setFormData(prev => ({ ...prev, chat_id: e.target.value }))}
                  required
                >
                  <option value="">Select a chat</option>
                  {chatsData?.chats.map((chat) => (
                    <option key={chat.id} value={chat.id}>
                      {chat.name}
                    </option>
                  ))}
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="message">Message *</Label>
                <Textarea
                  id="message"
                  placeholder="Enter your message..."
                  value={formData.message}
                  onChange={(e) => setFormData(prev => ({ ...prev, message: e.target.value }))}
                  rows={4}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="schedule_type">Schedule Type *</Label>
                <Select
                  id="schedule_type"
                  value={formData.schedule_type}
                  onChange={(e) => {
                    const type = e.target.value as ScheduleType
                    setFormData(prev => ({
                      ...prev,
                      schedule_type: type,
                      schedule_expression: ''
                    }))
                  }}
                  required
                >
                  <option value="once">One-time</option>
                  <option value="cron">Recurring (Cron)</option>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="schedule_expression">
                  {formData.schedule_type === 'once' ? 'Date & Time *' : 'Cron Expression *'}
                </Label>
                {formData.schedule_type === 'once' ? (
                  <Input
                    id="schedule_expression"
                    type="datetime-local"
                    value={formData.schedule_expression}
                    onChange={(e) => setFormData(prev => ({ ...prev, schedule_expression: e.target.value }))}
                    required
                  />
                ) : (
                  <>
                    <Input
                      id="schedule_expression"
                      placeholder="0 9 * * MON-FRI"
                      value={formData.schedule_expression}
                      onChange={(e) => setFormData(prev => ({ ...prev, schedule_expression: e.target.value }))}
                      required
                    />
                    {formData.schedule_expression && (
                      <p className="text-xs text-muted-foreground">
                        {getCronDescription(formData.schedule_expression)}
                      </p>
                    )}
                    <div className="text-xs text-muted-foreground space-y-1">
                      <p>Examples:</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li><code>0 9 * * *</code> - Daily at 9:00 AM</li>
                        <li><code>0 9 * * MON-FRI</code> - Weekdays at 9:00 AM</li>
                        <li><code>0 */2 * * *</code> - Every 2 hours</li>
                        <li><code>30 14 * * 1</code> - Every Monday at 2:30 PM</li>
                      </ul>
                    </div>
                  </>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="timezone">Timezone</Label>
                <Input
                  id="timezone"
                  placeholder="America/New_York"
                  value={formData.timezone}
                  onChange={(e) => setFormData(prev => ({ ...prev, timezone: e.target.value }))}
                />
                <p className="text-xs text-muted-foreground">
                  Current: {Intl.DateTimeFormat().resolvedOptions().timeZone}
                </p>
              </div>

              <div className="flex items-center justify-between pt-4 border-t">
                <div>
                  <Label htmlFor="enabled">Enable Schedule</Label>
                  <p className="text-sm text-muted-foreground">
                    Schedule will start running immediately
                  </p>
                </div>
                <Switch
                  id="enabled"
                  checked={formData.enabled}
                  onCheckedChange={(checked) => setFormData(prev => ({ ...prev, enabled: checked }))}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => { setShowDialog(false); setEditId(null) }}>
                Cancel
              </Button>
              <Button type="submit" disabled={createSchedule.isPending || updateSchedule.isPending}>
                {editId ? 'Update Schedule' : 'Create Schedule'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Schedule</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this schedule? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

