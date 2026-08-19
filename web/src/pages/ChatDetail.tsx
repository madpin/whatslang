import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Bot as BotIcon,
  Hash,
  Loader2,
  MessagesSquare,
  Pause,
  Play,
  Settings as SettingsIcon,
  Terminal,
  Trash2,
} from 'lucide-react';

import { Bots, Chats as ChatsAPI, Devices } from '@/api/endpoints';
import { ApiError } from '@/api/client';
import type { BotStatus, BotType } from '@/api/types';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Select } from '@/components/ui/Select';
import { ChatPicker } from '@/components/ChatPicker';
import { PageHeader } from '@/components/PageHeader';
import { useToast } from '@/lib/toast';
import {
  chatDisplayName,
  chatTypeLabel,
  formatDateTime,
  formatRelative,
} from '@/lib/utils';

export function ChatDetailPage() {
  const { chatJid: encodedJid } = useParams();
  const chatJid = decodeURIComponent(encodedJid ?? '');
  const navigate = useNavigate();
  const qc = useQueryClient();
  const toast = useToast();

  const chatQ = useQuery({
    enabled: !!chatJid,
    queryKey: ['chat', chatJid],
    queryFn: () => ChatsAPI.get(chatJid),
    refetchInterval: 10_000,
  });
  const botTypesQ = useQuery({
    queryKey: ['bots', 'types'],
    queryFn: () => Bots.types(),
  });

  const startBot = useMutation({
    mutationFn: (botName: string) => Bots.start(botName, chatJid),
    onSuccess: (_d, name) => {
      toast.show({ title: `Started ${name}`, tone: 'success' });
      qc.invalidateQueries({ queryKey: ['chat', chatJid] });
      qc.invalidateQueries({ queryKey: ['bots'] });
      qc.invalidateQueries({ queryKey: ['stats'] });
    },
    onError: (e: unknown) =>
      toast.show({
        title: 'Could not start bot',
        description: e instanceof ApiError ? e.message : undefined,
        tone: 'error',
      }),
  });
  const stopBot = useMutation({
    mutationFn: (botName: string) => Bots.stop(botName, chatJid),
    onSuccess: (_d, name) => {
      toast.show({ title: `Stopped ${name}`, tone: 'success' });
      qc.invalidateQueries({ queryKey: ['chat', chatJid] });
      qc.invalidateQueries({ queryKey: ['bots'] });
      qc.invalidateQueries({ queryKey: ['stats'] });
    },
    onError: (e: unknown) =>
      toast.show({
        title: 'Could not stop bot',
        description: e instanceof ApiError ? e.message : undefined,
        tone: 'error',
      }),
  });
  const deleteChat = useMutation({
    mutationFn: () => ChatsAPI.delete(chatJid),
    onSuccess: () => {
      toast.show({ title: 'Chat deleted', tone: 'success' });
      qc.invalidateQueries({ queryKey: ['chats'] });
      qc.invalidateQueries({ queryKey: ['stats'] });
      navigate('/chats');
    },
    onError: (e: unknown) =>
      toast.show({
        title: 'Delete failed',
        description: e instanceof ApiError ? e.message : undefined,
        tone: 'error',
      }),
  });

  if (!chatJid) {
    return (
      <EmptyState
        icon={<MessagesSquare size={20} />}
        title="No chat selected"
        description="Open a chat from the chats list."
        action={
          <Link to="/chats">
            <Button size="sm" variant="outline" leftIcon={<ArrowLeft size={14} />}>
              Back to chats
            </Button>
          </Link>
        }
      />
    );
  }

  if (chatQ.isLoading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-zinc-500">
        <Loader2 className="animate-spin" size={20} />
      </div>
    );
  }
  if (chatQ.isError || !chatQ.data) {
    return (
      <EmptyState
        icon={<MessagesSquare size={20} />}
        title="Chat not found"
        description={
          chatQ.error instanceof ApiError ? chatQ.error.message : 'It may have been deleted.'
        }
        action={
          <Link to="/chats">
            <Button size="sm" variant="outline" leftIcon={<ArrowLeft size={14} />}>
              Back to chats
            </Button>
          </Link>
        }
      />
    );
  }

  const chat = chatQ.data;
  const allBotTypes = botTypesQ.data ?? [];
  const runningBots = chat.bots.filter((b) => b.status === 'running');
  const availableTypes = allBotTypes.filter(
    (t) => !runningBots.some((b) => b.name === t.name),
  );

  return (
    <>
      <PageHeader
        title={chatDisplayName(chat)}
        description={chat.chat_jid}
        actions={
          <>
            <Link to="/chats">
              <Button variant="ghost" size="sm" leftIcon={<ArrowLeft size={14} />}>
                Back
              </Button>
            </Link>
            <Button
              variant="danger"
              size="sm"
              leftIcon={<Trash2 size={14} />}
              loading={deleteChat.isPending}
              onClick={() => {
                if (
                  confirm(
                    'Delete this chat? Running bots will be stopped and assignments cleared.',
                  )
                ) {
                  deleteChat.mutate();
                }
              }}
            >
              Delete chat
            </Button>
          </>
        }
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Chat info</CardTitle>
            <Badge tone={chat.is_group ? 'blue' : 'gray'}>
              {chatTypeLabel(chat.chat_jid)}
            </Badge>
          </CardHeader>
          <CardBody>
            <dl className="grid grid-cols-1 gap-3 text-sm">
              <InfoRow label="Display name" value={chat.chat_name || '—'} />
              <InfoRow
                label="Type"
                value={
                  chat.is_group ? (
                    <span className="inline-flex items-center gap-1.5">
                      <Hash size={12} /> Group
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5">
                      <MessagesSquare size={12} /> Direct message
                    </span>
                  )
                }
              />
              <InfoRow
                label="Source"
                value={
                  <Badge tone={chat.is_manual ? 'amber' : 'gray'}>
                    {chat.is_manual ? 'Manual' : 'Synced'}
                  </Badge>
                }
              />
              <InfoRow label="Tracked messages" value={chat.message_count} />
              <InfoRow
                label="Last message"
                value={formatRelative(chat.last_message_time)}
              />
              <InfoRow label="Last synced" value={formatRelative(chat.last_synced)} />
              <InfoRow label="Added" value={formatDateTime(chat.added_at)} />
            </dl>
          </CardBody>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <div>
              <CardTitle>Bot assignments</CardTitle>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                Start, stop, and tune the bots running in this chat.
              </p>
            </div>
          </CardHeader>
          <CardBody className="px-0 py-0">
            {!chat.bots.length ? (
              <EmptyState
                icon={<BotIcon size={20} />}
                title="No bots assigned yet"
                description="Add a bot to this chat from the catalog below."
                className="m-5"
              />
            ) : (
              <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {chat.bots.map((bot) => (
                  <BotAssignmentRow
                    key={bot.name}
                    bot={bot}
                    chatJid={chatJid}
                    onStart={() => startBot.mutate(bot.name)}
                    onStop={() => stopBot.mutate(bot.name)}
                    busy={startBot.isPending || stopBot.isPending}
                  />
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </div>

      <div className="mt-4">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Add a bot</CardTitle>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                Pick a bot type to deploy to this chat.
              </p>
            </div>
          </CardHeader>
          <CardBody>
            {!availableTypes.length ? (
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                All bot types are already running in this chat.
              </p>
            ) : (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {availableTypes.map((type) => (
                  <BotTypeCard
                    key={type.name}
                    type={type}
                    onStart={() => startBot.mutate(type.name)}
                    busy={startBot.isPending}
                  />
                ))}
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    </>
  );
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <dt className="text-xs uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
        {label}
      </dt>
      <dd className="text-right text-sm text-zinc-800 dark:text-zinc-100">{value}</dd>
    </div>
  );
}

function BotTypeCard({
  type,
  onStart,
  busy,
}: {
  type: BotType;
  onStart: () => void;
  busy: boolean;
}) {
  return (
    <div className="flex flex-col rounded-xl border border-zinc-200 bg-white p-4 transition-colors hover:border-brand-300 dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-brand-700">
      <div className="flex items-start gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-lg dark:bg-brand-900/30">
          {type.emoji}
        </span>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{type.label}</p>
          <p className="mt-0.5 text-xs text-zinc-500 dark:text-zinc-400">
            Trigger: <code className="rounded bg-zinc-100 px-1 py-0.5 dark:bg-zinc-800">{type.prefix}</code>
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
      <div className="mt-4 flex items-center justify-end">
        <Button
          size="sm"
          leftIcon={<Play size={14} />}
          onClick={onStart}
          loading={busy}
        >
          Start in this chat
        </Button>
      </div>
    </div>
  );
}

function BotAssignmentRow({
  bot,
  chatJid,
  onStart,
  onStop,
  busy,
}: {
  bot: BotStatus;
  chatJid: string;
  onStart: () => void;
  onStop: () => void;
  busy: boolean;
}) {
  const [openSettings, setOpenSettings] = useState(false);
  const [openLogs, setOpenLogs] = useState(false);
  const isRunning = bot.status === 'running';
  const uptimeLabel = useMemo(() => {
    if (!bot.uptime_seconds) return null;
    const s = bot.uptime_seconds;
    if (s < 60) return `${Math.round(s)}s`;
    const m = Math.round(s / 60);
    if (m < 60) return `${m}m`;
    const h = Math.floor(m / 60);
    const r = m % 60;
    return `${h}h ${r}m`;
  }, [bot.uptime_seconds]);

  return (
    <li className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 items-start gap-3">
        <span
          className={`flex h-9 w-9 items-center justify-center rounded-lg text-lg ${
            isRunning
              ? 'bg-emerald-50 dark:bg-emerald-900/30'
              : 'bg-zinc-100 dark:bg-zinc-800'
          }`}
        >
          {bot.emoji}
        </span>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{bot.label}</p>
            <Badge tone={isRunning ? 'green' : 'gray'} dot={isRunning}>
              {isRunning ? 'Running' : 'Stopped'}
            </Badge>
            {isRunning && uptimeLabel ? (
              <span className="text-xs text-zinc-500 dark:text-zinc-400">{uptimeLabel}</span>
            ) : null}
          </div>
          <p className="mt-0.5 text-xs text-zinc-500 dark:text-zinc-400">
            Trigger <code className="rounded bg-zinc-100 px-1 py-0.5 dark:bg-zinc-800">{bot.prefix}</code> ·{' '}
            {bot.context_message_count} msg context
            {bot.answer_owner_messages ? ' · self-answer ON' : ''}
            {bot.response_chat_jid ? ' · custom destination' : ''}
            {bot.source_device_id &&
            bot.target_device_id &&
            bot.source_device_id !== bot.target_device_id
              ? ' · cross-device relay'
              : ''}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant="ghost"
          leftIcon={<Terminal size={14} />}
          onClick={() => setOpenLogs(true)}
        >
          Logs
        </Button>
        <Button
          size="sm"
          variant="outline"
          leftIcon={<SettingsIcon size={14} />}
          onClick={() => setOpenSettings(true)}
        >
          Settings
        </Button>
        {isRunning ? (
          <Button
            size="sm"
            variant="outline"
            leftIcon={<Pause size={14} />}
            onClick={onStop}
            loading={busy}
          >
            Stop
          </Button>
        ) : (
          <Button
            size="sm"
            leftIcon={<Play size={14} />}
            onClick={onStart}
            loading={busy}
          >
            Start
          </Button>
        )}
      </div>

      {openSettings ? (
        <BotSettingsModal
          bot={bot}
          chatJid={chatJid}
          onClose={() => setOpenSettings(false)}
        />
      ) : null}
      {openLogs ? (
        <BotLogsModal bot={bot} chatJid={chatJid} onClose={() => setOpenLogs(false)} />
      ) : null}
    </li>
  );
}

function BotSettingsModal({
  bot,
  chatJid,
  onClose,
}: {
  bot: BotStatus;
  chatJid: string;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const toast = useToast();
  const [answerOwner, setAnswerOwner] = useState(bot.answer_owner_messages);
  const [contextCount, setContextCount] = useState(bot.context_message_count);
  const [responseChat, setResponseChat] = useState(bot.response_chat_jid ?? '');
  const [sourceDevice, setSourceDevice] = useState(bot.source_device_id ?? '');
  const [targetDevice, setTargetDevice] = useState(bot.target_device_id ?? '');

  const devicesQ = useQuery({ queryKey: ['devices'], queryFn: () => Devices.list() });
  const devices = devicesQ.data ?? [];
  // Routing pickers are only meaningful once there's more than one account
  // to read from / send with.
  const multiDevice = devices.length >= 2;
  const defaultDevice = devices.find((d) => d.is_default);

  const save = useMutation({
    mutationFn: () =>
      Bots.updateSettings(bot.name, chatJid, {
        answer_owner_messages: answerOwner,
        context_message_count: contextCount,
        response_chat_jid: responseChat || null,
        ...(multiDevice
          ? { source_device_id: sourceDevice || null, target_device_id: targetDevice || null }
          : {}),
      }),
    onSuccess: () => {
      toast.show({ title: 'Settings saved', tone: 'success' });
      qc.invalidateQueries({ queryKey: ['chat', chatJid] });
      qc.invalidateQueries({ queryKey: ['bots'] });
      onClose();
    },
    onError: (e: unknown) =>
      toast.show({
        title: 'Save failed',
        description: e instanceof ApiError ? e.message : undefined,
        tone: 'error',
      }),
  });

  return (
    <Modal
      open
      onClose={onClose}
      title={`Settings · ${bot.label}`}
      description={`Trigger: ${bot.prefix} · ${bot.description}`}
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={() => save.mutate()} loading={save.isPending}>
            Save settings
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <label className="flex items-start gap-3 rounded-lg border border-zinc-200 p-3 text-sm dark:border-zinc-800">
          <input
            type="checkbox"
            className="mt-0.5 rounded border-zinc-300 dark:border-zinc-700"
            checked={answerOwner}
            onChange={(e) => setAnswerOwner(e.target.checked)}
          />
          <span>
            <span className="font-medium text-zinc-900 dark:text-zinc-100">
              Answer my own messages
            </span>
            <span className="block text-xs text-zinc-500 dark:text-zinc-400">
              When enabled, the bot will respond to your own messages too.
            </span>
          </span>
        </label>
        <Input
          type="number"
          label="Context messages"
          hint="How many recent messages to include as conversation history."
          value={contextCount}
          min={0}
          max={50}
          onChange={(e) => setContextCount(parseInt(e.target.value || '0', 10))}
        />
        {multiDevice ? (
          <Select
            label="Read messages from"
            hint="Which WhatsApp account this bot watches this chat on."
            value={sourceDevice}
            onChange={(e) => setSourceDevice(e.target.value)}
          >
            <option value="">Default device ({defaultDevice?.label ?? '—'})</option>
            {devices.map((d) => (
              <option key={d.id} value={d.id}>
                {d.label}
                {d.is_default ? ' (default)' : ''}
              </option>
            ))}
          </Select>
        ) : null}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-zinc-800 dark:text-zinc-100">
            Send replies to
          </label>
          <ChatPicker
            value={responseChat}
            onChange={setResponseChat}
            emptyLabel="Same chat (default)"
            placeholder="Search chats by name or JID…"
          />
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            Optionally redirect responses to a different chat (e.g. yourself).
          </p>
        </div>
        {multiDevice ? (
          <Select
            label="Send replies from"
            hint="Which account sends the reply. Pick another account to read here and write there."
            value={targetDevice}
            onChange={(e) => setTargetDevice(e.target.value)}
          >
            <option value="">Same as read device</option>
            {devices.map((d) => (
              <option key={d.id} value={d.id}>
                {d.label}
                {d.is_default ? ' (default)' : ''}
              </option>
            ))}
          </Select>
        ) : null}
      </div>
    </Modal>
  );
}

function BotLogsModal({
  bot,
  chatJid,
  onClose,
}: {
  bot: BotStatus;
  chatJid: string;
  onClose: () => void;
}) {
  const logsQ = useQuery({
    queryKey: ['bot', 'logs', bot.name, chatJid],
    queryFn: () => Bots.logs(bot.name, chatJid, 200),
    refetchInterval: 3000,
  });
  return (
    <Modal
      open
      onClose={onClose}
      title={`Logs · ${bot.label}`}
      description="Most recent log lines (auto-refreshing)"
      size="lg"
    >
      <div className="max-h-[60vh] overflow-auto rounded-lg border border-zinc-200 bg-zinc-950 p-3 font-mono text-xs text-zinc-200 dark:border-zinc-800">
        {logsQ.isLoading ? (
          <p className="text-zinc-400">Loading logs…</p>
        ) : !logsQ.data?.logs.length ? (
          <p className="text-zinc-500">No log lines yet. Send a message to the chat to trigger activity.</p>
        ) : (
          logsQ.data.logs.map((entry, i) => (
            <div key={i} className="whitespace-pre-wrap">
              <span className="text-zinc-500">{entry.timestamp.replace('T', ' ').split('.')[0]}</span>{' '}
              <span
                className={
                  entry.level === 'ERROR'
                    ? 'text-red-400'
                    : entry.level === 'WARNING'
                      ? 'text-amber-300'
                      : 'text-emerald-300'
                }
              >
                {entry.level}
              </span>{' '}
              <span>{entry.message}</span>
            </div>
          ))
        )}
      </div>
    </Modal>
  );
}
