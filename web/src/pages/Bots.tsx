import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Bot,
  Hash,
  MessagesSquare,
  Pause,
  Play,
  Search,
  Sparkles,
} from 'lucide-react';

import { Bots as BotsAPI, Chats as ChatsAPI } from '@/api/endpoints';
import { ApiError } from '@/api/client';
import type { BotStatus, BotType, ChatBrief } from '@/api/types';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Select } from '@/components/ui/Select';
import { PageHeader } from '@/components/PageHeader';
import { useToast } from '@/lib/toast';
import { chatTypeLabel } from '@/lib/utils';

export function BotsPage() {
  const [search, setSearch] = useState('');
  const typesQ = useQuery({
    queryKey: ['bots', 'types'],
    queryFn: () => BotsAPI.types(),
  });
  const runningQ = useQuery({
    queryKey: ['bots', 'running'],
    queryFn: () => BotsAPI.running(),
    refetchInterval: 10_000,
  });
  const allChatsQ = useQuery({
    queryKey: ['chats', 'all'],
    queryFn: () => ChatsAPI.all(),
  });

  const types = useMemo(() => {
    const list = typesQ.data ?? [];
    if (!search.trim()) return list;
    const q = search.toLowerCase();
    return list.filter(
      (t) =>
        t.label.toLowerCase().includes(q) ||
        t.name.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q) ||
        t.prefix.toLowerCase().includes(q),
    );
  }, [typesQ.data, search]);

  const runningByName = useMemo(() => {
    const map: Record<string, BotStatus[]> = {};
    for (const s of runningQ.data ?? []) {
      (map[s.name] ??= []).push(s);
    }
    return map;
  }, [runningQ.data]);

  return (
    <>
      <PageHeader
        title="Bots"
        description="Browse the bot catalog and manage running instances."
        actions={
          <div className="w-64">
            <Input
              leftIcon={<Search size={14} />}
              placeholder="Search bots…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        }
      />

      <Card className="mb-4">
        <CardHeader>
          <div>
            <CardTitle>Currently running</CardTitle>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Live bot instances across all chats.
            </p>
          </div>
          <Badge tone="green" dot>
            {runningQ.data?.length ?? 0} active
          </Badge>
        </CardHeader>
        <CardBody className="px-0 py-0">
          {runningQ.isLoading ? (
            <div className="p-5">
              <div className="h-6 w-1/3 animate-pulse rounded bg-zinc-100 dark:bg-zinc-800" />
            </div>
          ) : !runningQ.data?.length ? (
            <EmptyState
              icon={<Sparkles size={20} />}
              title="No bots running yet"
              description="Pick a bot below and assign it to one of your chats."
              className="m-5"
            />
          ) : (
            <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {runningQ.data.map((bot) => (
                <li
                  key={`${bot.name}:${bot.chat_jid}`}
                  className="flex items-center gap-3 px-5 py-3"
                >
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-50 text-lg dark:bg-emerald-900/30">
                    {bot.emoji}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-100">
                      {bot.label}
                    </p>
                    <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">
                      {bot.chat_jid.endsWith('@g.us') ? <Hash size={10} className="inline" /> : <MessagesSquare size={10} className="inline" />}{' '}
                      {bot.chat_jid}
                    </p>
                  </div>
                  <Badge tone={bot.chat_jid.endsWith('@g.us') ? 'blue' : 'gray'}>
                    {chatTypeLabel(bot.chat_jid)}
                  </Badge>
                  <Link
                    to={`/chats/${encodeURIComponent(bot.chat_jid)}`}
                    className="text-xs font-medium text-brand-600 hover:underline dark:text-brand-400"
                  >
                    Open chat
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {typesQ.isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-48 animate-pulse rounded-xl bg-zinc-100 dark:bg-zinc-800/40"
            />
          ))
        ) : !types.length ? (
          <Card className="sm:col-span-2 lg:col-span-3">
            <CardBody>
              <EmptyState
                icon={<Bot size={20} />}
                title="No bots match your search"
                description="Try a different keyword."
              />
            </CardBody>
          </Card>
        ) : (
          types.map((type) => (
            <BotCatalogCard
              key={type.name}
              type={type}
              running={runningByName[type.name] ?? []}
              chats={allChatsQ.data ?? []}
            />
          ))
        )}
      </div>
    </>
  );
}

function BotCatalogCard({
  type,
  running,
  chats,
}: {
  type: BotType;
  running: BotStatus[];
  chats: ChatBrief[];
}) {
  const qc = useQueryClient();
  const toast = useToast();
  const [openAssign, setOpenAssign] = useState(false);
  const [target, setTarget] = useState('');

  const start = useMutation({
    mutationFn: (jid: string) => BotsAPI.start(type.name, jid),
    onSuccess: () => {
      toast.show({ title: `Started ${type.label}`, tone: 'success' });
      qc.invalidateQueries({ queryKey: ['bots'] });
      qc.invalidateQueries({ queryKey: ['chat'] });
      qc.invalidateQueries({ queryKey: ['chats'] });
      qc.invalidateQueries({ queryKey: ['stats'] });
      setOpenAssign(false);
      setTarget('');
    },
    onError: (e: unknown) =>
      toast.show({
        title: 'Could not start bot',
        description: e instanceof ApiError ? e.message : undefined,
        tone: 'error',
      }),
  });
  const stop = useMutation({
    mutationFn: (jid: string) => BotsAPI.stop(type.name, jid),
    onSuccess: () => {
      toast.show({ title: `Stopped ${type.label}`, tone: 'success' });
      qc.invalidateQueries({ queryKey: ['bots'] });
      qc.invalidateQueries({ queryKey: ['chat'] });
      qc.invalidateQueries({ queryKey: ['chats'] });
      qc.invalidateQueries({ queryKey: ['stats'] });
    },
    onError: (e: unknown) =>
      toast.show({
        title: 'Could not stop bot',
        description: e instanceof ApiError ? e.message : undefined,
        tone: 'error',
      }),
  });

  return (
    <>
      <div className="flex flex-col rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="flex items-start gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-2xl dark:bg-brand-900/30">
            {type.emoji}
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h3 className="truncate text-base font-semibold text-zinc-900 dark:text-zinc-100">
                {type.label}
              </h3>
              {running.length ? (
                <Badge tone="green" dot>
                  {running.length}
                </Badge>
              ) : null}
            </div>
            <p className="mt-0.5 text-xs text-zinc-500 dark:text-zinc-400">
              Trigger:{' '}
              <code className="rounded bg-zinc-100 px-1 py-0.5 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
                {type.prefix}
              </code>
            </p>
          </div>
        </div>
        <p className="mt-3 line-clamp-3 text-xs text-zinc-600 dark:text-zinc-300">
          {type.description}
        </p>
        <div className="mt-3 flex flex-wrap gap-1">
          {type.supports.text ? <Badge tone="brand">Text</Badge> : null}
          {type.supports.image ? <Badge tone="violet">Image</Badge> : null}
          {type.supports.audio ? <Badge tone="blue">Audio</Badge> : null}
          {type.supports.video ? <Badge tone="amber">Video</Badge> : null}
        </div>
        {running.length > 0 ? (
          <div className="mt-4 space-y-1.5">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Active in
            </p>
            <ul className="space-y-1">
              {running.slice(0, 3).map((b) => (
                <li
                  key={b.chat_jid}
                  className="flex items-center justify-between gap-2 rounded-md bg-zinc-50 px-2 py-1.5 text-xs dark:bg-zinc-800/50"
                >
                  <Link
                    to={`/chats/${encodeURIComponent(b.chat_jid)}`}
                    className="truncate text-zinc-700 hover:text-brand-600 dark:text-zinc-200 dark:hover:text-brand-400"
                  >
                    {b.chat_jid}
                  </Link>
                  <button
                    type="button"
                    className="text-zinc-400 hover:text-red-500"
                    title="Stop in this chat"
                    onClick={() => stop.mutate(b.chat_jid)}
                  >
                    <Pause size={12} />
                  </button>
                </li>
              ))}
              {running.length > 3 ? (
                <li className="text-[11px] text-zinc-400">
                  +{running.length - 3} more
                </li>
              ) : null}
            </ul>
          </div>
        ) : null}
        <div className="mt-4 flex items-center justify-between">
          <p className="text-[11px] text-zinc-400">{type.name}</p>
          <Button
            size="sm"
            leftIcon={<Play size={14} />}
            onClick={() => setOpenAssign(true)}
          >
            Assign to chat
          </Button>
        </div>
      </div>

      <Modal
        open={openAssign}
        onClose={() => setOpenAssign(false)}
        title={`Assign ${type.label}`}
        description="Pick a chat where this bot will run."
        footer={
          <>
            <Button variant="ghost" onClick={() => setOpenAssign(false)}>
              Cancel
            </Button>
            <Button
              disabled={!target}
              loading={start.isPending}
              onClick={() => start.mutate(target)}
            >
              Start bot
            </Button>
          </>
        }
      >
        <Select
          label="Target chat"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
        >
          <option value="">— Select a chat —</option>
          {chats.map((c) => (
            <option key={c.chat_jid} value={c.chat_jid}>
              {c.chat_name} ({c.chat_jid})
            </option>
          ))}
        </Select>
        <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">
          Tip: open the chat afterward to fine-tune context size, self-answer, and reply destination.
        </p>
      </Modal>
    </>
  );
}
