import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Edit, Trash2, Power, PowerOff } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
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
import { useBots, useUpdateBot, useDeleteBot } from '@/hooks/useBots'
import { formatDate } from '@/lib/utils'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import GuideHint from '@/components/ui/guide-hint'

export default function Bots() {
  const { data, isLoading } = useBots(30000)
  const updateBot = useUpdateBot()
  const deleteBot = useDeleteBot()
  const [search, setSearch] = useState('')
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const filteredBots = data?.bots.filter(bot =>
    bot.name.toLowerCase().includes(search.toLowerCase()) ||
    bot.type.toLowerCase().includes(search.toLowerCase())
  ) || []

  const handleToggleEnabled = (id: string, enabled: boolean) => {
    updateBot.mutate({ id, bot: { enabled: !enabled } })
  }

  const handleDelete = () => {
    if (deleteId) {
      deleteBot.mutate(deleteId, {
        onSuccess: () => setDeleteId(null)
      })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Bots</h1>
          <p className="text-muted-foreground">
            Manage your bot instances
          </p>
        </div>
        <Button asChild>
          <Link to="/bots/new">
            <Plus className="mr-2 h-4 w-4" />
            Create Bot
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle>All Bots</CardTitle>
              <CardDescription>
                {data?.total || 0} bot{data?.total !== 1 ? 's' : ''} configured
              </CardDescription>
            </div>
            <GuideHint
              hintKey="bots.list"
              title="Keep bots organized"
              description="Use the search to quickly find a bot, then enable/disable it before assigning in the Bot Attribution workspace."
            />
          </div>
          <div className="mt-4">
            <Input
              placeholder="Search bots by name or type..."
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
          ) : filteredBots.length === 0 ? (
            <div className="text-center py-12">
              <Bot className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No bots found</h3>
              <p className="text-muted-foreground mb-4">
                {search ? 'Try adjusting your search' : 'Get started by creating your first bot'}
              </p>
              {!search && (
                <Button asChild>
                  <Link to="/bots/new">
                    <Plus className="mr-2 h-4 w-4" />
                    Create Bot
                  </Link>
                </Button>
              )}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredBots.map((bot) => (
                  <TableRow key={bot.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{bot.name}</div>
                        {bot.description && (
                          <div className="text-sm text-muted-foreground line-clamp-1">
                            {bot.description}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{bot.type}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={bot.enabled ? 'default' : 'secondary'}>
                        {bot.enabled ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDate(bot.created_at, 'MMM d, yyyy')}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleToggleEnabled(bot.id, bot.enabled)}
                          title={bot.enabled ? 'Disable' : 'Enable'}
                        >
                          {bot.enabled ? (
                            <PowerOff className="h-4 w-4" />
                          ) : (
                            <Power className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          asChild
                        >
                          <Link to={`/bots/${bot.id}/edit`}>
                            <Edit className="h-4 w-4" />
                          </Link>
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeleteId(bot.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
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

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Bot</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this bot? This action cannot be undone.
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

function Bot({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M12 8V4H8" />
      <rect width="16" height="12" x="4" y="8" rx="2" />
      <path d="M2 14h2" />
      <path d="M20 14h2" />
      <path d="M15 13v2" />
      <path d="M9 13v2" />
    </svg>
  )
}

