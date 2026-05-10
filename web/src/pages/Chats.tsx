import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowDownAZ,
  ArrowUpAZ,
  Hash,
  MessagesSquare,
  Play,
  Plus,
  RefreshCw,
  Search,
  Square,
  Trash2,
} from 'lucide-react';
import { Link } from 'react-router-dom';

import { Chats as ChatsAPI } from '@/api/endpoints';
import type { ChatWithBots } from '@/api/types';
import { ApiError } from '@/api/client';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Select } from '@/components/ui/Select';
import { PageHeader } from '@/components/PageHeader';
import { PaginationBar } from '@/components/Pagination';
import { useToast } from '@/lib/toast';
import { chatDisplayName, chatTypeLabel, formatRelative, pluralize } from '@/lib/utils';

type SortField = 'last_message_time' | 'chat_name' | 'message_count' | 'added_at';
type SortOrder = 'asc' | 'desc';

export function ChatsPage() {
  const qc = useQueryClient();
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [search, setSearch] = useState('');
  const [chatType, setChatType] = useState<'' | 'group' | 'individual'>('');
  const [activity, setActivity] = useState<'' | 'active' | 'recent' | 'idle'>('');
  const [botStatus, setBotStatus] = useState<'' | 'running' | 'none'>('');
  const [sortField, setSortField] = useState<SortField>('last_message_time');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [showAdd, setShowAdd] = useState(false);
  const [newJid, setNewJid] = useState('');
  const [newName, setNewName] = useState('');

  const params = {
    page,
    per_page: perPage,
    sort: sortField,
    order: sortOrder,
    activity,
    bot_status: botStatus,
    chat_type: chatType,
    search,
  };

  const chats = useQuery({
    queryKey: ['chats', params],
    queryFn: () => ChatsAPI.list(params),
    placeholderData: (prev) => prev,
  });

  const sync = useMutation({
    mutationFn: () => ChatsAPI.sync(),
    onSuccess: () => {
      toast.show({ title: 'Sync complete', tone: 'success' });
      qc.invalidateQueries({ queryKey: ['chats'] });
      qc.invalidateQueries({ queryKey: ['stats'] });
    },
    onError: (e: unknown) =>
      toast.show({
        title: 'Sync failed',
        description: e instanceof ApiError ? e.message : 'Unable to sync chats.',
        tone: 'error',
      }),
  });

  const addChat = useMutation({
    mutationFn: () => ChatsAPI.add(newJid.trim(), newName.trim() || undefined),
    onSuccess: () => {
      toast.show({ title: 'Chat added', tone: 'success' });
      setShowAdd(false);
      setNewJid('');
      setNewName('');
      qc.invalidateQueries({ queryKey: ['chats'] });
    },
    onError: (e: unknown) =>
      toast.show({
        title: 'Could not add chat',
        description: e instanceof ApiError ? e.message : undefined,
        tone: 'error',
      }),
  });

  const bulk = useMutation({
    mutationFn: (action: 'start_bots' | 'stop_bots' | 'delete_chats') =>
      ChatsAPI.bulk(action, [...selected]),
    onSuccess: (_d, action) => {
      toast.show({
        title:
          action === 'delete_chats'
            ? 'Chats deleted'
            : action === 'start_bots'
              ? 'Bots started'
              : 'Bots stopped',
        tone: 'success',
      });
      setSelected(new Set());
      qc.invalidateQueries({ queryKey: ['chats'] });
      qc.invalidateQueries({ queryKey: ['stats'] });
      qc.invalidateQueries({ queryKey: ['bots'] });
    },
    onError: (e: unknown) =>
      toast.show({
        title: 'Bulk action failed',
        description: e instanceof ApiError ? e.message : undefined,
        tone: 'error',
      }),
  });

  const list = chats.data?.chats ?? [];
  const pagination = chats.data?.pagination;
  const allOnPageSelected = list.length > 0 && list.every((c) => selected.has(c.chat_jid));

  const toggleSelect = (jid: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(jid) ? next.delete(jid) : next.add(jid);
      return next;
    });
  };
  const toggleAllOnPage = () => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (allOnPageSelected) {
        list.forEach((c) => next.delete(c.chat_jid));
      } else {
        list.forEach((c) => next.add(c.chat_jid));
      }
      return next;
    });
  };

  const setSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
    setPage(1);
  };

  const onResetFilters = () => {
    setSearch('');
    setChatType('');
    setActivity('');
    setBotStatus('');
    setSortField('last_message_time');
    setSortOrder('desc');
    setPage(1);
  };

  const SortHeader = ({
    field,
    children,
    className = '',
  }: {
    field: SortField;
    children: React.ReactNode;
    className?: string;
  }) => (
    <button
      type="button"
      onClick={() => setSort(field)}
      className={`flex items-center gap-1 text-left text-xs font-medium uppercase tracking-wider text-zinc-500 hover:text-zinc-800 dark:text-zinc-400 dark:hover:text-zinc-200 ${className}`}
    >
      {children}
      {sortField === field ? (
        sortOrder === 'asc' ? (
          <ArrowUpAZ size={12} />
        ) : (
          <ArrowDownAZ size={12} />
        )
      ) : null}
    </button>
  );

  return (
    <>
      <PageHeader
        title="Chats"
        description="All WhatsApp chats and DMs tracked by Whatslang."
        actions={
          <>
            <Button
              variant="outline"
              size="sm"
              leftIcon={<RefreshCw size={14} className={sync.isPending ? 'animate-spin' : ''} />}
              onClick={() => sync.mutate()}
              loading={sync.isPending}
            >
              Sync now
            </Button>
            <Button
              size="sm"
              leftIcon={<Plus size={14} />}
              onClick={() => setShowAdd(true)}
            >
              Add chat
            </Button>
          </>
        }
      />

      <Card className="mb-4">
        <CardBody className="grid grid-cols-1 gap-3 md:grid-cols-12">
          <div className="md:col-span-5">
            <Input
              leftIcon={<Search size={14} />}
              placeholder="Search by name or JID…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </div>
          <div className="md:col-span-2">
            <Select
              value={chatType}
              onChange={(e) => {
                setChatType(e.target.value as typeof chatType);
                setPage(1);
              }}
            >
              <option value="">All types</option>
              <option value="group">Groups</option>
              <option value="individual">DMs</option>
            </Select>
          </div>
          <div className="md:col-span-2">
            <Select
              value={activity}
              onChange={(e) => {
                setActivity(e.target.value as typeof activity);
                setPage(1);
              }}
            >
              <option value="">Any activity</option>
              <option value="active">Active (24h)</option>
              <option value="recent">Recent (7d)</option>
              <option value="idle">Idle</option>
            </Select>
          </div>
          <div className="md:col-span-2">
            <Select
              value={botStatus}
              onChange={(e) => {
                setBotStatus(e.target.value as typeof botStatus);
                setPage(1);
              }}
            >
              <option value="">Any bots</option>
              <option value="running">With running bots</option>
              <option value="none">No bots</option>
            </Select>
          </div>
          <div className="flex items-end justify-end md:col-span-1">
            <Button variant="ghost" size="sm" onClick={onResetFilters}>
              Reset
            </Button>
          </div>
        </CardBody>
      </Card>

      {selected.size > 0 ? (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-brand-200 bg-brand-50 px-4 py-3 dark:border-brand-900 dark:bg-brand-900/20">
          <p className="text-sm text-brand-800 dark:text-brand-200">
            {pluralize(selected.size, 'chat')} selected
          </p>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              leftIcon={<Play size={14} />}
              onClick={() => bulk.mutate('start_bots')}
              loading={bulk.isPending}
              title="Resume previously assigned bots"
            >
              Resume bots
            </Button>
            <Button
              size="sm"
              variant="outline"
              leftIcon={<Square size={14} />}
              onClick={() => bulk.mutate('stop_bots')}
              loading={bulk.isPending}
            >
              Stop all bots
            </Button>
            <Button
              size="sm"
              variant="danger"
              leftIcon={<Trash2 size={14} />}
              onClick={() => {
                if (confirm(`Delete ${selected.size} chat(s)? This stops their bots.`)) {
                  bulk.mutate('delete_chats');
                }
              }}
              loading={bulk.isPending}
            >
              Delete
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setSelected(new Set())}
            >
              Clear
            </Button>
          </div>
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>
            {chats.isLoading
              ? 'Loading chats…'
              : `${pagination?.total ?? 0} chats`}
          </CardTitle>
          {chats.isFetching && !chats.isLoading ? (
            <span className="text-xs text-zinc-400">Refreshing…</span>
          ) : null}
        </CardHeader>
        <CardBody className="px-0 py-0">
          {chats.isError ? (
            <EmptyState
              icon={<MessagesSquare size={20} />}
              title="Could not load chats"
              description={
                chats.error instanceof ApiError ? chats.error.message : 'Try again.'
              }
              className="m-5"
            />
          ) : chats.isLoading ? (
            <div className="space-y-3 p-5">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-12 animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-800"
                />
              ))}
            </div>
          ) : !list.length ? (
            <EmptyState
              icon={<MessagesSquare size={22} />}
              title="No chats match your filters"
              description="Try resetting filters or sync your WhatsApp chats."
              action={
                <Button onClick={onResetFilters} variant="outline" size="sm">
                  Reset filters
                </Button>
              }
              className="m-5"
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-zinc-100 dark:border-zinc-800">
                  <tr>
                    <th className="w-10 px-5 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={allOnPageSelected}
                        onChange={toggleAllOnPage}
                        className="rounded border-zinc-300 dark:border-zinc-700"
                        aria-label="Select all on page"
                      />
                    </th>
                    <th className="px-3 py-3 text-left">
                      <SortHeader field="chat_name">Chat</SortHeader>
                    </th>
                    <th className="hidden px-3 py-3 text-left lg:table-cell">
                      <SortHeader field="message_count">Activity</SortHeader>
                    </th>
                    <th className="hidden px-3 py-3 text-left md:table-cell">
                      <SortHeader field="last_message_time">Last message</SortHeader>
                    </th>
                    <th className="px-3 py-3 text-left">
                      <span className="text-xs font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                        Bots
                      </span>
                    </th>
                    <th className="px-5 py-3" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                  {list.map((chat) => (
                    <ChatRow
                      key={chat.chat_jid}
                      chat={chat}
                      selected={selected.has(chat.chat_jid)}
                      onToggle={() => toggleSelect(chat.chat_jid)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      {pagination ? (
        <PaginationBar
          page={pagination.page}
          perPage={pagination.per_page}
          total={pagination.total}
          totalPages={pagination.total_pages}
          onChange={setPage}
        />
      ) : null}

      <Modal
        open={showAdd}
        onClose={() => setShowAdd(false)}
        title="Add a chat manually"
        description="Enter a WhatsApp JID. Use … @s.whatsapp.net for DMs and … @g.us for groups."
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowAdd(false)}>
              Cancel
            </Button>
            <Button
              loading={addChat.isPending}
              disabled={!newJid.trim()}
              onClick={() => addChat.mutate()}
            >
              Add chat
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <Input
            label="Chat JID"
            placeholder="551199999@s.whatsapp.net"
            value={newJid}
            onChange={(e) => setNewJid(e.target.value)}
            autoFocus
          />
          <Input
            label="Display name (optional)"
            placeholder="Family group"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
          />
        </div>
      </Modal>
    </>
  );
}

function ChatRow({
  chat,
  selected,
  onToggle,
}: {
  chat: ChatWithBots;
  selected: boolean;
  onToggle: () => void;
}) {
  const running = useMemo(
    () => chat.bots.filter((b) => b.status === 'running'),
    [chat.bots],
  );
  return (
    <tr className="transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-800/40">
      <td className="px-5 py-3 align-middle">
        <input
          type="checkbox"
          checked={selected}
          onChange={onToggle}
          className="rounded border-zinc-300 dark:border-zinc-700"
          aria-label="Select chat"
        />
      </td>
      <td className="px-3 py-3 align-middle">
        <Link
          to={`/chats/${encodeURIComponent(chat.chat_jid)}`}
          className="flex items-center gap-3"
        >
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">
            {chat.is_group ? <Hash size={14} /> : <MessagesSquare size={14} />}
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-100">
              {chatDisplayName(chat)}
            </p>
            <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">
              {chat.chat_jid}
            </p>
          </div>
        </Link>
      </td>
      <td className="hidden px-3 py-3 align-middle text-zinc-600 lg:table-cell dark:text-zinc-300">
        <Badge tone={chat.is_group ? 'blue' : 'gray'}>{chatTypeLabel(chat.chat_jid)}</Badge>
        <span className="ml-2 text-xs text-zinc-500 dark:text-zinc-400">
          {pluralize(chat.message_count, 'msg')}
        </span>
      </td>
      <td className="hidden px-3 py-3 align-middle text-xs text-zinc-500 md:table-cell dark:text-zinc-400">
        {formatRelative(chat.last_message_time)}
      </td>
      <td className="px-3 py-3 align-middle">
        {running.length ? (
          <div className="flex flex-wrap gap-1">
            {running.slice(0, 3).map((b) => (
              <Badge key={b.name} tone="green" dot>
                {b.emoji} {b.label}
              </Badge>
            ))}
            {running.length > 3 ? (
              <Badge tone="gray">+{running.length - 3}</Badge>
            ) : null}
          </div>
        ) : (
          <span className="text-xs text-zinc-400">No bots</span>
        )}
      </td>
      <td className="px-5 py-3 text-right">
        <Link
          to={`/chats/${encodeURIComponent(chat.chat_jid)}`}
          className="text-xs font-medium text-brand-600 hover:underline dark:text-brand-400"
        >
          Open
        </Link>
      </td>
    </tr>
  );
}

export { ChatDetailPage } from './ChatDetail';
