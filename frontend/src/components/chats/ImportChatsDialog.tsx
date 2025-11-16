import { useState, useEffect } from 'react'
import { Download, Loader2 } from 'lucide-react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { usePreviewChats, useImportSelectedChats } from '@/hooks/useChats'
import type { WhatsAppChatPreview } from '@/types/chat'

interface ImportChatsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function ImportChatsDialog({ open, onOpenChange }: ImportChatsDialogProps) {
  const { data: previewChats, isLoading, refetch } = usePreviewChats()
  const importChats = useImportSelectedChats()
  
  const [selectedJids, setSelectedJids] = useState<Set<string>>(new Set())
  const [showOnlyNew, setShowOnlyNew] = useState(false)

  // Fetch preview when dialog opens
  useEffect(() => {
    if (open) {
      refetch()
      setSelectedJids(new Set())
    }
  }, [open, refetch])

  const filteredChats = previewChats?.filter(chat => 
    !showOnlyNew || !chat.exists
  ) || []

  const newChats = previewChats?.filter(chat => !chat.exists) || []
  const existingChats = previewChats?.filter(chat => chat.exists) || []

  const handleToggleSelect = (jid: string) => {
    const newSelected = new Set(selectedJids)
    if (newSelected.has(jid)) {
      newSelected.delete(jid)
    } else {
      newSelected.add(jid)
    }
    setSelectedJids(newSelected)
  }

  const handleSelectAll = () => {
    const jidsToSelect = filteredChats
      .filter(chat => !chat.exists)
      .map(chat => chat.jid)
    setSelectedJids(new Set(jidsToSelect))
  }

  const handleDeselectAll = () => {
    setSelectedJids(new Set())
  }

  const handleImport = () => {
    if (selectedJids.size === 0) return
    
    importChats.mutate(Array.from(selectedJids), {
      onSuccess: () => {
        onOpenChange(false)
        setSelectedJids(new Set())
      }
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Import Chats from WhatsApp</DialogTitle>
          <DialogDescription>
            Select the chats you want to import into the system
          </DialogDescription>
        </DialogHeader>

        <div className="flex items-center justify-between py-2">
          <div className="flex gap-2">
            <Badge variant="outline">
              {newChats.length} new
            </Badge>
            <Badge variant="outline">
              {existingChats.length} already imported
            </Badge>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowOnlyNew(!showOnlyNew)}
            >
              {showOnlyNew ? 'Show All' : 'Show Only New'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleSelectAll}
              disabled={newChats.length === 0}
            >
              Select All New
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDeselectAll}
              disabled={selectedJids.size === 0}
            >
              Deselect All
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-auto border rounded-md">
          {isLoading ? (
            <div className="p-4 space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : filteredChats.length === 0 ? (
            <div className="text-center py-12">
              <h3 className="text-lg font-semibold mb-2">
                {showOnlyNew ? 'No new chats found' : 'No chats found'}
              </h3>
              <p className="text-muted-foreground">
                {showOnlyNew 
                  ? 'All WhatsApp chats are already imported' 
                  : 'Could not fetch chats from WhatsApp'}
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <input
                      type="checkbox"
                      checked={filteredChats.filter(c => !c.exists).every(c => selectedJids.has(c.jid))}
                      onChange={(e) => {
                        if (e.target.checked) {
                          handleSelectAll()
                        } else {
                          handleDeselectAll()
                        }
                      }}
                      disabled={filteredChats.filter(c => !c.exists).length === 0}
                      className="h-4 w-4 cursor-pointer"
                    />
                  </TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>JID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredChats.map((chat) => (
                  <TableRow key={chat.jid}>
                    <TableCell>
                      <input
                        type="checkbox"
                        checked={selectedJids.has(chat.jid)}
                        onChange={() => handleToggleSelect(chat.jid)}
                        disabled={chat.exists}
                        className="h-4 w-4 cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
                      />
                    </TableCell>
                    <TableCell>
                      <div className="font-medium">{chat.name || 'Unknown'}</div>
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
                      {chat.exists ? (
                        <Badge variant="outline" className="bg-muted">
                          Already Imported
                        </Badge>
                      ) : (
                        <Badge variant="default" className="bg-green-500">
                          New
                        </Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>

        <DialogFooter>
          <Button 
            variant="outline" 
            onClick={() => onOpenChange(false)}
            disabled={importChats.isPending}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleImport}
            disabled={selectedJids.size === 0 || importChats.isPending}
          >
            {importChats.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Importing...
              </>
            ) : (
              <>
                <Download className="mr-2 h-4 w-4" />
                Import {selectedJids.size} Chat{selectedJids.size !== 1 ? 's' : ''}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

