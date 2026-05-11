import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Database,
  Eye,
  FileText,
  Image as ImageIcon,
  Mic,
  MessageSquare,
  Music,
  Package,
  RefreshCw,
  Server,
  ServerCrash,
  Sticker,
  Type,
  Video,
  Wifi,
  WifiOff,
  XCircle,
} from 'lucide-react';

import { System } from '@/api/endpoints';
import type {
  Diagnostics,
  InboundMediaType,
  InboundObservation,
  LlmSurface,
  LlmSurfaceActivity,
} from '@/api/types';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { PageHeader } from '@/components/PageHeader';
import {
  STALENESS_TONE,
  chatDisplayName,
  formatBytes,
  formatRelative,
  pluralize,
  shortenJid,
  staleness,
} from '@/lib/utils';

export function DiagnosticsPage() {
  const qc = useQueryClient();
  const diagQ = useQuery({
    queryKey: ['diagnostics'],
    queryFn: () => System.diagnostics(),
    refetchInterval: 10_000,
  });
  const data = diagQ.data;

  return (
    <>
      <PageHeader
        title="Diagnostics"
        description="Live health of the WhatsApp gateway, LLM, database and bot runtime."
        actions={
          <Button
            variant="outline"
            size="sm"
            leftIcon={<RefreshCw size={14} className={diagQ.isFetching ? 'animate-spin' : ''} />}
            onClick={() => qc.invalidateQueries({ queryKey: ['diagnostics'] })}
            loading={diagQ.isFetching && !diagQ.data}
          >
            Refresh
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <GatewayCard data={data} loading={diagQ.isLoading} />
        <DatabaseCard data={data} loading={diagQ.isLoading} />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4">
        <ModelActivityCard data={data} loading={diagQ.isLoading} />
        <InboundTrafficCard data={data} loading={diagQ.isLoading} />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <BotsCard data={data} loading={diagQ.isLoading} />
        <RecentErrorsCard data={data} loading={diagQ.isLoading} />
      </div>
    </>
  );
}

function StateBadge({
  ok,
  okLabel,
  failLabel,
  unknown,
}: {
  ok: boolean;
  okLabel: string;
  failLabel: string;
  unknown?: boolean;
}) {
  if (unknown) return <Badge tone="gray">…</Badge>;
  return ok ? (
    <Badge tone="green" dot>
      {okLabel}
    </Badge>
  ) : (
    <Badge tone="red" dot>
      {failLabel}
    </Badge>
  );
}

function Row({
  icon,
  label,
  value,
}: {
  icon?: React.ReactNode;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-zinc-100 pb-2 last:border-b-0 last:pb-0 dark:border-zinc-800">
      <span className="flex items-center gap-2 text-xs uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
        {icon}
        {label}
      </span>
      <span className="text-right text-sm text-zinc-800 dark:text-zinc-100">{value}</span>
    </div>
  );
}

function GatewayCard({ data, loading }: { data?: Diagnostics; loading: boolean }) {
  const gw = data?.gateway;
  const ok = !!gw?.reachable && !!gw?.is_connected && !!gw?.is_logged_in;
  return (
    <Card>
      <CardHeader>
        <CardTitle>WhatsApp gateway</CardTitle>
        {loading ? (
          <Badge tone="gray">Checking…</Badge>
        ) : ok ? (
          <Badge tone="green" dot>
            Online
          </Badge>
        ) : gw?.reachable ? (
          <Badge tone="amber" dot>
            Reachable, not logged in
          </Badge>
        ) : (
          <Badge tone="red" dot>
            Offline
          </Badge>
        )}
      </CardHeader>
      <CardBody className="space-y-3">
        <Row
          icon={<Server size={14} />}
          label="API"
          value={
            <code className="text-xs">{gw?.base_url ?? '—'}</code>
          }
        />
        <Row
          icon={gw?.reachable ? <Wifi size={14} /> : <WifiOff size={14} />}
          label="Reachable"
          value={
            <span className="inline-flex items-center gap-1.5">
              <StateBadge
                ok={!!gw?.reachable}
                okLabel="Yes"
                failLabel="No"
                unknown={loading}
              />
              {gw?.latency_ms != null ? (
                <span className="text-xs text-zinc-500 dark:text-zinc-400">
                  {gw.latency_ms}ms
                </span>
              ) : null}
            </span>
          }
        />
        <Row
          icon={
            gw?.is_connected ? (
              <CheckCircle2 size={14} className="text-emerald-500" />
            ) : (
              <ServerCrash size={14} className="text-red-500" />
            )
          }
          label="Socket connected"
          value={
            <StateBadge
              ok={!!gw?.is_connected}
              okLabel="Connected"
              failLabel="Disconnected"
              unknown={loading}
            />
          }
        />
        <Row
          icon={
            gw?.is_logged_in ? (
              <CheckCircle2 size={14} className="text-emerald-500" />
            ) : (
              <ServerCrash size={14} className="text-red-500" />
            )
          }
          label="Logged in"
          value={
            <StateBadge
              ok={!!gw?.is_logged_in}
              okLabel="Yes"
              failLabel="No"
              unknown={loading}
            />
          }
        />
        <Row
          label="Device ID"
          value={<code className="text-xs">{gw?.device_id ?? '—'}</code>}
        />
        <Row
          label="Calls / errors"
          value={
            <span>
              <span className="text-zinc-700 dark:text-zinc-200">
                {gw?.call_count ?? 0}
              </span>
              <span className="mx-1.5 text-zinc-400">/</span>
              <span className={(gw?.error_count ?? 0) > 0 ? 'text-red-500' : 'text-zinc-700 dark:text-zinc-200'}>
                {gw?.error_count ?? 0}
              </span>
            </span>
          }
        />
        <Row
          label="Last call"
          value={<span className="text-xs text-zinc-500">{formatRelative(gw?.last_call_at ?? null)}</span>}
        />
        <Row
          label="Last error"
          value={
            <span className="text-xs text-zinc-500">
              {formatRelative(gw?.last_error_at ?? null)}
            </span>
          }
        />
      </CardBody>
    </Card>
  );
}

const SURFACE_LABEL: Record<LlmSurface, string> = {
  text: 'Text',
  vision: 'Vision',
  audio: 'Audio (Whisper)',
  video: 'Video → Audio',
};

const SURFACE_ICON: Record<LlmSurface, React.ReactNode> = {
  text: <Type size={14} />,
  vision: <Eye size={14} />,
  audio: <Mic size={14} />,
  video: <Video size={14} />,
};

function ModelActivityCard({
  data,
  loading,
}: {
  data?: Diagnostics;
  loading: boolean;
}) {
  const llm = data?.llm;
  const surfaces = llm?.surfaces ?? [];
  const totalCalls = surfaces.reduce((acc, s) => acc + s.call_count, 0);
  const totalErrors = surfaces.reduce((acc, s) => acc + s.error_count, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Model activity</CardTitle>
        {loading ? (
          <Badge tone="gray">…</Badge>
        ) : !llm?.api_key_set ? (
          <Badge tone="red" dot>
            No API key
          </Badge>
        ) : (
          <span className="flex items-center gap-2">
            <Badge tone="gray">
              {pluralize(totalCalls, 'call')}
            </Badge>
            <Badge tone={totalErrors > 0 ? 'amber' : 'green'} dot>
              {pluralize(totalErrors, 'error')}
            </Badge>
          </span>
        )}
      </CardHeader>
      <CardBody className="space-y-2 px-0 py-0">
        {!llm ? (
          <p className="px-5 py-4 text-sm text-zinc-500">Loading…</p>
        ) : (
          <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {surfaces.map((s) => (
              <SurfaceRow key={s.surface} surface={s} />
            ))}
            {surfaces.length === 0 ? (
              <li className="px-5 py-4 text-sm text-zinc-500">
                No model calls yet. Send a message to a chat with a bot enabled.
              </li>
            ) : null}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}

function SurfaceRow({ surface }: { surface: LlmSurfaceActivity }) {
  const sLast = staleness(surface.last_success_at);
  const successHasHappened = surface.success_count > 0;
  const errorRate =
    surface.call_count > 0
      ? Math.round((surface.error_count / surface.call_count) * 100)
      : 0;

  return (
    <li className="grid grid-cols-12 gap-3 px-5 py-3 text-sm">
      <div className="col-span-12 flex items-center gap-2 sm:col-span-3">
        <span className="text-zinc-500">{SURFACE_ICON[surface.surface]}</span>
        <span className="font-medium text-zinc-800 dark:text-zinc-100">
          {SURFACE_LABEL[surface.surface]}
        </span>
        {surface.model ? (
          <code className="ml-1 truncate text-xs text-zinc-500">{surface.model}</code>
        ) : null}
      </div>

      <div className="col-span-12 flex items-center gap-2 sm:col-span-3">
        <Badge tone={successHasHappened ? STALENESS_TONE[sLast] : 'gray'} dot>
          {successHasHappened ? `last ok ${formatRelative(surface.last_success_at)}` : 'never served'}
        </Badge>
      </div>

      <div className="col-span-12 sm:col-span-3">
        {surface.last_error_at ? (
          <span
            className="inline-flex max-w-full items-center gap-1.5 truncate text-xs text-red-600 dark:text-red-400"
            title={surface.last_error_message ?? undefined}
          >
            <XCircle size={12} className="shrink-0" />
            <span className="truncate">
              error {formatRelative(surface.last_error_at)}
            </span>
          </span>
        ) : (
          <span className="text-xs text-zinc-400">no errors</span>
        )}
      </div>

      <div className="col-span-12 flex items-center justify-end gap-3 text-xs sm:col-span-3">
        <span className="tabular-nums text-zinc-700 dark:text-zinc-200">
          {surface.success_count} ok
        </span>
        <span className="text-zinc-400">/</span>
        <span
          className={
            surface.error_count > 0
              ? 'tabular-nums text-red-500'
              : 'tabular-nums text-zinc-400'
          }
        >
          {surface.error_count} err
        </span>
        {errorRate > 0 ? (
          <Badge tone={errorRate > 20 ? 'red' : 'amber'}>{errorRate}%</Badge>
        ) : null}
        {surface.last_latency_ms != null ? (
          <span className="text-zinc-400">{surface.last_latency_ms}ms</span>
        ) : null}
      </div>
    </li>
  );
}

const MEDIA_LABEL: Record<InboundMediaType, string> = {
  text: 'Text',
  image: 'Image',
  audio: 'Audio / Voice note',
  video: 'Video',
  document: 'Document',
  sticker: 'Sticker',
  other: 'Other',
};

const MEDIA_ICON: Record<InboundMediaType, React.ReactNode> = {
  text: <MessageSquare size={14} />,
  image: <ImageIcon size={14} />,
  audio: <Music size={14} />,
  video: <Video size={14} />,
  document: <FileText size={14} />,
  sticker: <Sticker size={14} />,
  other: <Package size={14} />,
};

function InboundTrafficCard({
  data,
  loading,
}: {
  data?: Diagnostics;
  loading: boolean;
}) {
  const inbound = data?.inbound ?? [];
  const totalSeen = inbound.reduce((acc, i) => acc + i.total_count, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Inbound traffic by type</CardTitle>
        {loading ? (
          <Badge tone="gray">…</Badge>
        ) : (
          <Badge tone={totalSeen > 0 ? 'brand' : 'gray'}>
            {pluralize(totalSeen, 'message')} observed
          </Badge>
        )}
      </CardHeader>
      <CardBody className="px-0 py-0">
        {!inbound.length ? (
          <p className="px-5 py-4 text-sm text-zinc-500">Loading…</p>
        ) : (
          <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {inbound.map((row) => (
              <InboundRow key={row.media_type} obs={row} />
            ))}
          </ul>
        )}
        <p className="border-t border-zinc-100 px-5 py-3 text-xs text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
          Counts only include messages from chats with at least one bot
          enabled (those are the chats we actively poll). If a type you
          know just arrived isn&apos;t showing as <em>fresh</em>, the
          gateway, the bot poll loop, or the database write is stuck.
        </p>
      </CardBody>
    </Card>
  );
}

function InboundRow({ obs }: { obs: InboundObservation }) {
  const tone = obs.last_seen_at ? STALENESS_TONE[staleness(obs.last_seen_at)] : 'gray';
  const chatLabel = obs.last_chat_jid
    ? chatDisplayName({
        chat_jid: obs.last_chat_jid,
        chat_name: obs.last_chat_name,
      })
    : null;

  return (
    <li className="grid grid-cols-12 gap-3 px-5 py-3 text-sm">
      <div className="col-span-12 flex items-center gap-2 sm:col-span-3">
        <span className="text-zinc-500">{MEDIA_ICON[obs.media_type]}</span>
        <span className="font-medium text-zinc-800 dark:text-zinc-100">
          {MEDIA_LABEL[obs.media_type]}
        </span>
      </div>

      <div className="col-span-12 flex items-center gap-2 sm:col-span-3">
        <Badge tone={tone} dot>
          {obs.last_seen_at ? formatRelative(obs.last_seen_at) : 'never seen'}
        </Badge>
      </div>

      <div className="col-span-12 truncate text-xs text-zinc-600 dark:text-zinc-300 sm:col-span-4">
        {chatLabel ? (
          <span title={obs.last_chat_jid ?? undefined}>
            from <span className="font-medium">{chatLabel}</span>
            {obs.last_sender ? (
              <span className="ml-1 text-zinc-400">
                ({shortenJid(obs.last_sender, 16)})
              </span>
            ) : null}
          </span>
        ) : (
          <span className="text-zinc-400">—</span>
        )}
      </div>

      <div className="col-span-12 text-right text-xs tabular-nums text-zinc-600 dark:text-zinc-400 sm:col-span-2">
        {obs.total_count} total
      </div>
    </li>
  );
}

function DatabaseCard({ data, loading }: { data?: Diagnostics; loading: boolean }) {
  const db = data?.database;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Database</CardTitle>
        {loading ? (
          <Badge tone="gray">…</Badge>
        ) : (
          <Badge tone="gray">{formatBytes(db?.size_bytes ?? 0)}</Badge>
        )}
      </CardHeader>
      <CardBody className="space-y-3">
        <Row
          icon={<Database size={14} />}
          label="Path"
          value={<code className="text-xs break-all">{db?.path ?? '—'}</code>}
        />
        <Row label="Tracked chats" value={db?.chats ?? '—'} />
        <Row label="Bot assignments" value={db?.assignments ?? '—'} />
        <Row label="Processed messages" value={db?.processed_messages ?? '—'} />
      </CardBody>
    </Card>
  );
}

function BotsCard({ data, loading }: { data?: Diagnostics; loading: boolean }) {
  const bots = data?.bots;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Bot runtime</CardTitle>
        {loading ? (
          <Badge tone="gray">…</Badge>
        ) : (
          <Badge tone="brand">
            {bots ? pluralize(bots.running, 'running bot') : '—'}
          </Badge>
        )}
      </CardHeader>
      <CardBody className="space-y-3">
        <Row
          icon={<Activity size={14} />}
          label="Catalog size"
          value={bots?.catalog_size ?? '—'}
        />
        <Row label="Currently running" value={bots?.running ?? '—'} />
        <Row
          label="Poll interval"
          value={bots ? `${bots.poll_interval}s` : '—'}
        />
      </CardBody>
    </Card>
  );
}

function RecentErrorsCard({
  data,
  loading,
}: {
  data?: Diagnostics;
  loading: boolean;
}) {
  const errors = data?.recent_errors ?? [];
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent gateway errors</CardTitle>
        <Badge tone={errors.length ? 'red' : 'green'} dot>
          {loading ? '…' : pluralize(errors.length, 'error')}
        </Badge>
      </CardHeader>
      <CardBody className="px-0 py-0">
        {loading ? (
          <p className="px-5 py-4 text-sm text-zinc-500">Loading…</p>
        ) : !errors.length ? (
          <p className="px-5 py-4 text-sm text-zinc-500 dark:text-zinc-400">
            <CheckCircle2 size={14} className="mr-1.5 inline text-emerald-500" />
            No recent errors. Things look healthy.
          </p>
        ) : (
          <ul className="max-h-96 overflow-auto divide-y divide-zinc-100 dark:divide-zinc-800">
            {errors
              .slice()
              .reverse()
              .map((e, i) => (
                <li
                  key={i}
                  className="grid grid-cols-12 gap-3 px-5 py-3 text-sm"
                >
                  <span className="col-span-3 truncate text-xs text-zinc-500 dark:text-zinc-400">
                    {e.timestamp.replace('T', ' ')}
                  </span>
                  <code className="col-span-3 truncate text-xs text-zinc-700 dark:text-zinc-200">
                    {e.where}
                  </code>
                  <span className="col-span-1 text-xs text-zinc-500">
                    {e.status ?? '—'}
                  </span>
                  <span className="col-span-5 flex items-start gap-1.5 text-zinc-700 dark:text-zinc-200">
                    <AlertTriangle
                      size={12}
                      className="mt-0.5 shrink-0 text-amber-500"
                    />
                    <span className="break-words">{e.message}</span>
                  </span>
                </li>
              ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}
