import { useState } from 'react'
import { Send } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
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
import { useMessages, useSendMessage } from '@/hooks/useMessages'
import { useChats } from '@/hooks/useChats'
import { formatDate } from '@/lib/utils'
import type { SendMessageRequest } from '@/types/message'

export default function Messages() {
  const { data, isLoading } = useMessages(5000) // Poll every 5 seconds
  const { data: chatsData } = useChats()
  const sendMessage = useSendMessage()
  const [search, setSearch] = useState('')
  const [showDialog, setShowDialog] = useState(false)
  const [formData, setFormData] = useState<SendMessageRequest>({
    chat_jid: '',
    message: '',
  })

  const filteredMessages = data?.messages.filter(message =>
    message.content.toLowerCase().includes(search.toLowerCase()) ||
    message.chat_jid.toLowerCase().includes(search.toLowerCase()) ||
    message.sender_jid.toLowerCase().includes(search.toLowerCase())
  ) || []

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    sendMessage.mutate(formData, {
      onSuccess: () => {
        setShowDialog(false)
        setFormData({ chat_jid: '', message: '' })
      }
    })
  }

  const getChatName = (jid: string) => {
    const chat = chatsData?.chats.find(c => c.jid === jid)
    return chat?.name || jid
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Messages</h1>
          <p className="text-muted-foreground">
            View processed messages and send new ones
          </p>
        </div>
        <Button onClick={() => setShowDialog(true)}>
          <Send className="mr-2 h-4 w-4" />
          Send Message
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Message History</CardTitle>
              <CardDescription>
                {data?.total || 0} message{data?.total !== 1 ? 's' : ''} processed
              </CardDescription>
            </div>
            <Badge variant="outline" className="gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              Live
            </Badge>
          </div>
          <div className="mt-4">
            <Input
              placeholder="Search messages..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="max-w-sm"
            />
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(10)].map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : filteredMessages.length === 0 ? (
            <div className="text-center py-12">
              <h3 className="text-lg font-semibold mb-2">No messages found</h3>
              <p className="text-muted-foreground mb-4">
                {search
                  ? 'Try adjusting your search'
                  : 'Messages will appear here as they are processed by your bots'}
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Chat</TableHead>
                  <TableHead>Sender</TableHead>
                  <TableHead>Content</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredMessages.map((message) => (
                  <TableRow key={message.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium text-sm">
                          {getChatName(message.chat_jid)}
                        </div>
                        <code className="text-xs text-muted-foreground">
                          {message.chat_jid}
                        </code>
                      </div>
                    </TableCell>
                    <TableCell>
                      <code className="text-xs">{message.sender_jid}</code>
                    </TableCell>
                    <TableCell>
                      <div className="max-w-md">
                        <p className="line-clamp-2 text-sm">
                          {message.content || <span className="text-muted-foreground italic">No content</span>}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {message.message_type || 'text'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground whitespace-nowrap">
                      {formatDate(message.timestamp, 'MMM d, HH:mm:ss')}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Send Message Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>Send Message</DialogTitle>
              <DialogDescription>
                Send a message directly to a WhatsApp chat
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="chat_jid">Chat *</Label>
                <Select
                  id="chat_jid"
                  value={formData.chat_jid}
                  onChange={(e) => setFormData(prev => ({ ...prev, chat_jid: e.target.value }))}
                  required
                >
                  <option value="">Select a chat</option>
                  {chatsData?.chats.map((chat) => (
                    <option key={chat.id} value={chat.jid}>
                      {chat.name} - {chat.jid}
                    </option>
                  ))}
                </Select>
                <p className="text-xs text-muted-foreground">
                  Or enter a JID manually below
                </p>
              </div>

              {!formData.chat_jid && (
                <div className="space-y-2">
                  <Label htmlFor="manual_jid">Manual JID</Label>
                  <Input
                    id="manual_jid"
                    placeholder="120363419538094902@g.us"
                    onChange={(e) => setFormData(prev => ({ ...prev, chat_jid: e.target.value }))}
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="message">Message *</Label>
                <Textarea
                  id="message"
                  placeholder="Enter your message..."
                  value={formData.message}
                  onChange={(e) => setFormData(prev => ({ ...prev, message: e.target.value }))}
                  rows={6}
                  required
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={sendMessage.isPending}>
                <Send className="mr-2 h-4 w-4" />
                Send Message
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

