import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Eye, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
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
import { useChats, useCreateChat, useSyncChat } from '@/hooks/useChats'
import { formatDate } from '@/lib/utils'
import type { ChatCreate, ChatType } from '@/types/chat'

export default function Chats() {
  const { data, isLoading } = useChats(30000)
  const createChat = useCreateChat()
  const syncChat = useSyncChat()
  const [search, setSearch] = useState('')
  const [showDialog, setShowDialog] = useState(false)
  const [formData, setFormData] = useState<ChatCreate>({
    jid: '',
    name: '',
    chat_type: 'group',
  })

  const filteredChats = data?.chats.filter(chat =>
    chat.name.toLowerCase().includes(search.toLowerCase()) ||
    chat.jid.toLowerCase().includes(search.toLowerCase())
  ) || []

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createChat.mutate(formData, {
      onSuccess: () => {
        setShowDialog(false)
        setFormData({ jid: '', name: '', chat_type: 'group' })
      }
    })
  }

  const handleSync = (id: string) => {
    syncChat.mutate(id)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Chats</h1>
          <p className="text-muted-foreground">
            Manage your WhatsApp chats and group assignments
          </p>
        </div>
        <Button onClick={() => setShowDialog(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Register Chat
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Chats</CardTitle>
          <CardDescription>
            {data?.total || 0} chat{data?.total !== 1 ? 's' : ''} registered
          </CardDescription>
          <div className="mt-4">
            <Input
              placeholder="Search chats by name or JID..."
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
          ) : filteredChats.length === 0 ? (
            <div className="text-center py-12">
              <h3 className="text-lg font-semibold mb-2">No chats found</h3>
              <p className="text-muted-foreground mb-4">
                {search ? 'Try adjusting your search' : 'Get started by registering your first chat'}
              </p>
              {!search && (
                <Button onClick={() => setShowDialog(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Register Chat
                </Button>
              )}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>JID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredChats.map((chat) => (
                  <TableRow key={chat.id}>
                    <TableCell>
                      <div className="font-medium">{chat.name}</div>
                    </TableCell>
                    <TableCell>
                      <code className="text-xs bg-muted px-2 py-1 rounded">
                        {chat.jid}
                      </code>
                    </TableCell>
                    <TableCell>
                      <Badge variant={chat.chat_type === 'group' ? 'default' : 'secondary'}>
                        {chat.chat_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDate(chat.created_at, 'MMM d, yyyy')}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleSync(chat.id)}
                          title="Sync from WhatsApp"
                        >
                          <RefreshCw className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          asChild
                        >
                          <Link to={`/chats/${chat.id}`}>
                            <Eye className="h-4 w-4" />
                          </Link>
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create Chat Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>Register Chat</DialogTitle>
              <DialogDescription>
                Register a WhatsApp chat or group to enable bot features
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="jid">WhatsApp JID *</Label>
                <Input
                  id="jid"
                  placeholder="120363419538094902@g.us"
                  value={formData.jid}
                  onChange={(e) => setFormData(prev => ({ ...prev, jid: e.target.value }))}
                  required
                />
                <p className="text-xs text-muted-foreground">
                  Group: 120xxx@g.us | Private: 55xxx@s.whatsapp.net
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Chat Name *</Label>
                <Input
                  id="name"
                  placeholder="My Group Chat"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="chat_type">Chat Type *</Label>
                <Select
                  id="chat_type"
                  value={formData.chat_type}
                  onChange={(e) => setFormData(prev => ({ ...prev, chat_type: e.target.value as ChatType }))}
                  required
                >
                  <option value="group">Group</option>
                  <option value="private">Private</option>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={createChat.isPending}>
                Register Chat
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

