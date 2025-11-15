import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Bot,
  MessageSquare,
  Clock,
  Mail,
  Share2,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Bots', href: '/bots', icon: Bot },
  { name: 'Chats', href: '/chats', icon: MessageSquare },
  { name: 'Bot Attribution', href: '/bot-attribution', icon: Share2 },
  { name: 'Schedules', href: '/schedules', icon: Clock },
  { name: 'Messages', href: '/messages', icon: Mail },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <div className="w-64 bg-card border-r border-border flex flex-col">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-primary">WhatSlang</h1>
        <p className="text-sm text-muted-foreground">Bot Platform</p>
      </div>
      
      <nav className="flex-1 px-4 space-y-1">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href || 
            (item.href !== '/' && location.pathname.startsWith(item.href))
          
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>

      <div className="p-4 border-t border-border">
        <p className="text-xs text-muted-foreground">
          WhatsApp Bot Platform v1.0
        </p>
      </div>
    </div>
  )
}

