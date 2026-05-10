import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Activity,
  AlertTriangle,
  Bot,
  CheckCircle2,
  Database,
  RefreshCw,
  Server,
  ServerCrash,
  Wifi,
  WifiOff,
} from 'lucide-react';

import { System } from '@/api/endpoints';
import type { Diagnostics } from '@/api/types';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { PageHeader } from '@/components/PageHeader';
import { formatBytes, formatRelative, pluralize } from '@/lib/utils';

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
        <LlmCard data={data} loading={diagQ.isLoading} />
        <DatabaseCard data={data} loading={diagQ.isLoading} />
        <BotsCard data={data} loading={diagQ.isLoading} />
      </div>

      <div className="mt-4">
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

function LlmCard({ data, loading }: { data?: Diagnostics; loading: boolean }) {
  const llm = data?.llm;
  return (
    <Card>
      <CardHeader>
        <CardTitle>LLM service</CardTitle>
        {loading ? (
          <Badge tone="gray">…</Badge>
        ) : llm?.api_key_set ? (
          <Badge tone="green" dot>
            Key set
          </Badge>
        ) : (
          <Badge tone="red" dot>
            No API key
          </Badge>
        )}
      </CardHeader>
      <CardBody className="space-y-3">
        <Row
          icon={<Server size={14} />}
          label="Endpoint"
          value={<code className="text-xs">{llm?.base_url ?? '—'}</code>}
        />
        <Row
          icon={<Bot size={14} />}
          label="Text model"
          value={<code className="text-xs">{llm?.text_model ?? '—'}</code>}
        />
        <Row
          icon={<Bot size={14} />}
          label="Vision model"
          value={<code className="text-xs">{llm?.vision_model ?? '—'}</code>}
        />
        <Row
          icon={<Bot size={14} />}
          label="Audio model"
          value={<code className="text-xs">{llm?.audio_model ?? '—'}</code>}
        />
      </CardBody>
    </Card>
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
