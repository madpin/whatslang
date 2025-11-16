import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Eye, RefreshCw, Download, Trash2 } from 'lucide-react'
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
import { useChats, useCreateChat, useSyncChat, useDeleteChat, useBulkDeleteUnassignedChats } from '@/hooks/useChats'
import { formatDate } from '@/lib/utils'
import type { ChatCreate, ChatType } from '@/types/chat'
import ImportChatsDialog from '@/components/chats/ImportChatsDialog'

export default function Chats() {
  const { data, isLoading } = useChats(30000)
  const createChat = useCreateChat()
  const syncChat = useSyncChat()
  const deleteChat = useDeleteChat()
  const bulkDeleteUnassigned = useBulkDeleteUnassignedChats()
  
  const [search, setSearch] = useState('')
  const [showDialog, setShowDialog] = useState(false)
  const [showImportDialog, setShowImportDialog] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false)
  const [chatToDelete, setChatToDelete] = useState<string | null>(null)
  
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

  const handleDeleteClick = (id: string, botCount: number) => {
    if (botCount > 0) {
      return // Button should be disabled, but double check
    }
    setChatToDelete(id)
    setShowDeleteConfirm(true)
  }

  const handleDeleteConfirm = () => {
    if (!chatToDelete) return
    deleteChat.mutate(chatToDelete, {
      onSuccess: () => {
        setShowDeleteConfirm(false)
        setChatToDelete(null)
      }
    })
  }

  const handleBulkDeleteClick = () => {
    const unassignedCount = data?.chats.filter(chat => (chat.bot_count ?? 0) === 0).length ?? 0
    if (unassignedCount === 0) {
      return
    }
    setShowBulkDeleteConfirm(true)
  }

  const handleBulkDeleteConfirm = () => {
    bulkDeleteUnassigned.mutate(undefined, {
      onSuccess: () => {
        setShowBulkDeleteConfirm(false)
      }
    })
  }

  const unassignedCount = data?.chats.filter(chat => (chat.bot_count ?? 0) === 0).length ?? 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Chats</h1>
          <p className="text-muted-foreground">
            Manage your WhatsApp chats and group assignments
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={() => setShowImportDialog(true)}
            variant="outline"
          >
            <Download className="mr-2 h-4 w-4" />
            Import from WhatsApp
          </Button>
          <Button
            onClick={handleBulkDeleteClick}
            variant="outline"
            disabled={unassignedCount === 0 || bulkDeleteUnassigned.isPending}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete All Unassigned ({unassignedCount})
          </Button>
          <Button onClick={() => setShowDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Register Chat
          </Button>
        </div>
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
                  <TableHead>Bots</TableHead>
                  <TableHead>Last Activity</TableHead>
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
                    <TableCell>
                      <Badge variant="outline">
                        {chat.bot_count ?? 0} bot{(chat.bot_count ?? 0) !== 1 ? 's' : ''}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {chat.last_message_at 
                        ? formatDate(chat.last_message_at, 'MMM d, yyyy HH:mm')
                        : formatDate(chat.created_at, 'MMM d, yyyy')}
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
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDeleteClick(chat.id, chat.bot_count ?? 0)}
                          disabled={(chat.bot_count ?? 0) > 0}
                          title={(chat.bot_count ?? 0) > 0 ? 'Remove bots before deleting' : 'Delete chat'}
                          className="text-destructive hover:text-destructive hover:bg-destructive/10 disabled:opacity-50"
                        >
                          <Trash2 className="h-4 w-4" />
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

      {/* Import Chats Dialog */}
      <ImportChatsDialog 
        open={showImportDialog} 
        onOpenChange={setShowImportDialog}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Chat?</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this chat? This action cannot be undone.
              All messages associated with this chat will also be deleted.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setShowDeleteConfirm(false)}
              disabled={deleteChat.isPending}
            >
              Cancel
            </Button>
            <Button 
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={deleteChat.isPending}
            >
              {deleteChat.isPending ? 'Deleting...' : 'Delete Chat'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Delete Confirmation Dialog */}
      <Dialog open={showBulkDeleteConfirm} onOpenChange={setShowBulkDeleteConfirm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete All Unassigned Chats?</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete all {unassignedCount} chat{unassignedCount !== 1 ? 's' : ''} without bot assignments? 
              This action cannot be undone. All messages associated with these chats will also be deleted.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setShowBulkDeleteConfirm(false)}
              disabled={bulkDeleteUnassigned.isPending}
            >
              Cancel
            </Button>
            <Button 
              variant="destructive"
              onClick={handleBulkDeleteConfirm}
              disabled={bulkDeleteUnassigned.isPending}
            >
              {bulkDeleteUnassigned.isPending ? 'Deleting...' : `Delete ${unassignedCount} Chat${unassignedCount !== 1 ? 's' : ''}`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

