import { Link } from 'react-router-dom'
import { Bot, MessageSquare, Clock, Mail, Plus, ArrowRight, Share2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useBots } from '@/hooks/useBots'
import { useChats } from '@/hooks/useChats'
import { useSchedules } from '@/hooks/useSchedules'
import { useMessages } from '@/hooks/useMessages'
import { formatDate } from '@/lib/utils'
import GuideHint from '@/components/ui/guide-hint'

export default function Dashboard() {
  const { data: botsData, isLoading: botsLoading } = useBots(10000)
  const { data: chatsData, isLoading: chatsLoading } = useChats(10000)
  const { data: schedulesData, isLoading: schedulesLoading } = useSchedules(10000)
  const { data: messagesData, isLoading: messagesLoading } = useMessages(5000)

  const stats = [
    {
      title: 'Total Bots',
      value: botsData?.total || 0,
      icon: Bot,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      link: '/bots',
      loading: botsLoading,
    },
    {
      title: 'Active Chats',
      value: chatsData?.total || 0,
      icon: MessageSquare,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      link: '/chats',
      loading: chatsLoading,
    },
    {
      title: 'Schedules',
      value: schedulesData?.schedules.filter(s => s.enabled).length || 0,
      icon: Clock,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      link: '/schedules',
      loading: schedulesLoading,
    },
    {
      title: 'Recent Messages',
      value: messagesData?.total || 0,
      icon: Mail,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
      link: '/messages',
      loading: messagesLoading,
    },
  ]

  const recentMessages = messagesData?.messages.slice(0, 10) || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your WhatsApp bot platform
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              {stat.loading ? (
                <Skeleton className="h-8 w-20" />
              ) : (
                <div className="text-2xl font-bold">{stat.value}</div>
              )}
              <Link 
                to={stat.link}
                className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1 mt-2"
              >
                View all <ArrowRight className="h-3 w-3" />
              </Link>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common tasks to get you started
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-3">
          <Button asChild>
            <Link to="/bots/new">
              <Plus className="mr-2 h-4 w-4" />
              Create Bot
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to="/chats">
              <Plus className="mr-2 h-4 w-4" />
              Register Chat
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to="/schedules">
              <Plus className="mr-2 h-4 w-4" />
              Schedule Message
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to="/bot-attribution">
              <Share2 className="mr-2 h-4 w-4" />
              Assign Bots
            </Link>
          </Button>
          <GuideHint
            hintKey="dashboard.quickActions"
            title="Need a guided start?"
            description="Use Assign Bots to jump into the new Bot Attribution workspace and configure automation without leaving the dashboard."
          />
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Messages</CardTitle>
          <CardDescription>
            Last 10 processed messages
          </CardDescription>
        </CardHeader>
        <CardContent>
          {messagesLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : recentMessages.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No messages yet. Messages will appear here as they are processed.
            </p>
          ) : (
            <div className="space-y-3">
              {recentMessages.map((message) => (
                <div
                  key={message.id}
                  className="flex items-start justify-between p-3 border rounded-lg hover:bg-accent transition-colors"
                >
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {message.chat_jid}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(message.timestamp, 'MMM d, HH:mm')}
                      </span>
                    </div>
                    <p className="text-sm line-clamp-2">
                      {message.content || 'No content'}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      From: {message.sender_jid}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Active Bots Overview */}
      {botsData && botsData.bots.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Bots</CardTitle>
            <CardDescription>
              Your configured bot instances
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {botsData.bots
                .filter(bot => bot.enabled)
                .slice(0, 6)
                .map((bot) => (
                  <div
                    key={bot.id}
                    className="border rounded-lg p-4 hover:border-primary transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3 className="font-medium">{bot.name}</h3>
                        <p className="text-xs text-muted-foreground">
                          {bot.type}
                        </p>
                      </div>
                      <Badge variant="default" className="text-xs">
                        Active
                      </Badge>
                    </div>
                    {bot.description && (
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {bot.description}
                      </p>
                    )}
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

