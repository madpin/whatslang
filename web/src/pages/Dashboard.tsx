import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  Bot,
  Boxes,
  ExternalLink,
  Hash,
  MessagesSquare,
  Plus,
  ServerCrash,
  Sparkles,
} from 'lucide-react';
import { Link } from 'react-router-dom';

import { Bots, Chats, System } from '@/api/endpoints';
import { Badge } from '@/components/ui/Badge';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';
import { Button } from '@/components/ui/Button';
import { PageHeader } from '@/components/PageHeader';
import { StatCard } from '@/components/StatCard';
import { chatDisplayName, chatTypeLabel, formatRelative, pluralize } from '@/lib/utils';

export function DashboardPage() {
  const stats = useQuery({
    queryKey: ['stats'],
    queryFn: () => System.stats(),
    refetchInterval: 15_000,
  });
  const running = useQuery({
    queryKey: ['bots', 'running'],
    queryFn: () => Bots.running(),
    refetchInterval: 15_000,
  });
  const recentChats = useQuery({
    queryKey: ['chats', 'recent'],
    queryFn: () =>
      Chats.list({ page: 1, per_page: 6, sort: 'last_message_time', order: 'desc' }),
    refetchInterval: 15_000,
  });

  const errored = stats.isError || running.isError || recentChats.isError;

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="A snapshot of your WhatsApp bot activity."
        actions={
          <>
            <Link to="/chats">
              <Button variant="outline" size="sm" leftIcon={<Plus size={14} />}>
                Add chat
              </Button>
            </Link>
            <Link to="/bots">
              <Button size="sm" leftIcon={<Bot size={14} />}>
                Manage bots
              </Button>
            </Link>
          </>
        }
      />

      {errored ? (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800 dark:border-amber-900 dark:bg-amber-900/20 dark:text-amber-200">
          <ServerCrash size={18} className="mt-0.5" />
          <div className="text-sm">
            <p className="font-medium">Some data could not be loaded.</p>
            <p className="text-xs opacity-80">
              The backend or WhatsApp service may be unreachable. Refresh and try again.
            </p>
          </div>
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Tracked chats"
          value={stats.data?.total_chats ?? 0}
          loading={stats.isLoading}
          tone="brand"
          icon={<MessagesSquare size={18} />}
          hint="Across groups & DMs"
        />
        <StatCard
          label="Running bots"
          value={stats.data?.running_bots ?? 0}
          loading={stats.isLoading}
          tone="green"
          icon={<Bot size={18} />}
          hint="Live across chats"
        />
        <StatCard
          label="Active 24h"
          value={stats.data?.active_chats_24h ?? 0}
          loading={stats.isLoading}
          tone="violet"
          icon={<Activity size={18} />}
          hint="Chats with recent traffic"
        />
        <StatCard
          label="Bot types"
          value={stats.data?.available_bot_types ?? 0}
          loading={stats.isLoading}
          tone="blue"
          icon={<Boxes size={18} />}
          hint="Available to deploy"
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <div>
              <CardTitle>Recent chats</CardTitle>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                Most recently active chats with bot assignments.
              </p>
            </div>
            <Link
              to="/chats"
              className="flex items-center gap-1 text-xs font-medium text-brand-600 hover:underline dark:text-brand-400"
            >
              View all <ExternalLink size={12} />
            </Link>
          </CardHeader>
          <CardBody className="px-0 py-0">
            {recentChats.isLoading ? (
              <div className="space-y-3 p-5">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div
                    key={i}
                    className="flex animate-pulse items-center justify-between rounded-lg border border-zinc-100 px-3 py-2 dark:border-zinc-800"
                  >
                    <div className="h-4 w-1/3 rounded bg-zinc-100 dark:bg-zinc-800" />
                    <div className="h-4 w-16 rounded bg-zinc-100 dark:bg-zinc-800" />
                  </div>
                ))}
              </div>
            ) : !recentChats.data?.chats.length ? (
              <EmptyState
                icon={<MessagesSquare size={20} />}
                title="No chats yet"
                description="Sync your WhatsApp chats or add one manually to get started."
                action={
                  <Link to="/chats">
                    <Button size="sm" leftIcon={<Plus size={14} />}>
                      Add chat
                    </Button>
                  </Link>
                }
                className="m-5"
              />
            ) : (
              <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {recentChats.data.chats.map((chat) => {
                  const runningBots = chat.bots.filter((b) => b.status === 'running');
                  return (
                    <li key={chat.chat_jid}>
                      <Link
                        to={`/chats/${encodeURIComponent(chat.chat_jid)}`}
                        className="flex items-center gap-4 px-5 py-3 transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
                      >
                        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">
                          {chat.is_group ? <Hash size={16} /> : <MessagesSquare size={16} />}
                        </span>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <p className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-100">
                              {chatDisplayName(chat)}
                            </p>
                            <Badge tone={chat.is_group ? 'blue' : 'gray'}>
                              {chatTypeLabel(chat.chat_jid)}
                            </Badge>
                          </div>
                          <p className="mt-0.5 truncate text-xs text-zinc-500 dark:text-zinc-400">
                            {chat.message_count
                              ? `${pluralize(chat.message_count, 'msg')} · last ${formatRelative(chat.last_message_time)}`
                              : 'No tracked messages yet'}
                          </p>
                        </div>
                        <div className="flex shrink-0 items-center gap-1">
                          {runningBots.length ? (
                            <Badge tone="green" dot>
                              {runningBots.length} running
                            </Badge>
                          ) : (
                            <Badge tone="gray">No bots</Badge>
                          )}
                        </div>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>Active bots</CardTitle>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                Bots running right now.
              </p>
            </div>
            <Link
              to="/bots"
              className="flex items-center gap-1 text-xs font-medium text-brand-600 hover:underline dark:text-brand-400"
            >
              View all <ExternalLink size={12} />
            </Link>
          </CardHeader>
          <CardBody className="px-0 py-0">
            {running.isLoading ? (
              <div className="space-y-3 p-5">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div
                    key={i}
                    className="flex animate-pulse items-center justify-between rounded-lg border border-zinc-100 px-3 py-2 dark:border-zinc-800"
                  >
                    <div className="h-4 w-2/3 rounded bg-zinc-100 dark:bg-zinc-800" />
                    <div className="h-4 w-12 rounded bg-zinc-100 dark:bg-zinc-800" />
                  </div>
                ))}
              </div>
            ) : !running.data?.length ? (
              <EmptyState
                icon={<Sparkles size={20} />}
                title="No bots running"
                description="Pick a chat and assign a bot to start automating responses."
                action={
                  <Link to="/bots">
                    <Button size="sm" leftIcon={<Bot size={14} />}>
                      Manage bots
                    </Button>
                  </Link>
                }
                className="m-5"
              />
            ) : (
              <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {running.data.map((bot) => (
                  <li
                    key={`${bot.name}:${bot.chat_jid}`}
                    className="flex items-center gap-3 px-5 py-3"
                  >
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300">
                      <span className="text-base">{bot.emoji}</span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-100">
                          {bot.label}
                        </p>
                        <Badge tone="green" dot>
                          live
                        </Badge>
                      </div>
                      <p className="mt-0.5 truncate text-xs text-zinc-500 dark:text-zinc-400">
                        {bot.chat_jid}
                      </p>
                    </div>
                    <Link
                      to={`/chats/${encodeURIComponent(bot.chat_jid)}`}
                      className="text-xs text-brand-600 hover:underline dark:text-brand-400"
                    >
                      Open
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </div>
    </>
  );
}
