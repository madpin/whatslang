import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  Bot,
  Cog,
  Database,
  Lock,
  Server,
} from 'lucide-react';
import { Link } from 'react-router-dom';

import { System } from '@/api/endpoints';
import { Badge } from '@/components/ui/Badge';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { PageHeader } from '@/components/PageHeader';
import { useTheme } from '@/lib/theme';

export function SettingsPage() {
  const sysQ = useQuery({ queryKey: ['system'], queryFn: () => System.info() });
  const { theme, setTheme } = useTheme();

  return (
    <>
      <PageHeader
        title="Settings"
        description="Server configuration. Live health & errors live in Diagnostics."
      />

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Configuration</CardTitle>
          <Badge tone={sysQ.data?.environment === 'production' ? 'amber' : 'gray'}>
            {sysQ.data?.environment ?? '—'}
          </Badge>
        </CardHeader>
        <CardBody className="space-y-3">
          <Row
            icon={<Cog size={14} />}
            label="Version"
            value={sysQ.data?.version ?? '—'}
          />
          <Row
            icon={<Lock size={14} />}
            label="Authentication"
            value={
              sysQ.data?.auth_required ? (
                <Badge tone="green" dot>
                  Required
                </Badge>
              ) : (
                <Badge tone="amber">Disabled</Badge>
              )
            }
          />
          <Row
            icon={<Server size={14} />}
            label="WhatsApp API"
            value={
              sysQ.data?.whatsapp_base_url ? (
                <code className="text-xs">{sysQ.data.whatsapp_base_url}</code>
              ) : (
                '—'
              )
            }
          />
          <Row
            icon={<Bot size={14} />}
            label="LLM model"
            value={<code className="text-xs">{sysQ.data?.openai_model ?? '—'}</code>}
          />
          <Row
            icon={<Bot size={14} />}
            label="Vision model"
            value={<code className="text-xs">{sysQ.data?.openai_vision_model ?? '—'}</code>}
          />
          <Row
            icon={<Bot size={14} />}
            label="Audio model"
            value={<code className="text-xs">{sysQ.data?.openai_audio_model ?? '—'}</code>}
          />
          <Row
            icon={<Activity size={14} />}
            label="Poll interval"
            value={sysQ.data ? `${sysQ.data.poll_interval}s` : '—'}
          />
          <Row
            icon={<Database size={14} />}
            label="Database"
            value={<code className="text-xs">{sysQ.data?.db_path ?? '—'}</code>}
          />
        </CardBody>
      </Card>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Theme preferences are stored locally in this browser.
          </p>
        </CardHeader>
        <CardBody>
          <div className="flex flex-wrap gap-2">
            {(['light', 'dark', 'system'] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setTheme(mode)}
                className={`rounded-lg border px-4 py-2 text-sm capitalize transition-colors ${
                  theme === mode
                    ? 'border-brand-500 bg-brand-50 text-brand-700 dark:border-brand-400 dark:bg-brand-900/20 dark:text-brand-300'
                    : 'border-zinc-200 bg-white text-zinc-700 hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-200'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Need to debug?</CardTitle>
        </CardHeader>
        <CardBody>
          <p className="text-sm text-zinc-600 dark:text-zinc-300">
            Live health, gateway connectivity and recent gateway errors moved to{' '}
            <Link
              to="/diagnostics"
              className="font-medium text-brand-600 hover:underline dark:text-brand-300"
            >
              Diagnostics
            </Link>
            .
          </p>
        </CardBody>
      </Card>

      <p className="mt-6 text-center text-xs text-zinc-400">
        Whatslang Console · v3.0
      </p>
    </>
  );
}

function Row({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-zinc-100 pb-2 last:border-b-0 last:pb-0 dark:border-zinc-800">
      <span className="flex items-center gap-2 text-xs uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
        {icon}
        {label}
      </span>
      <span className="text-right text-sm font-medium text-zinc-800 dark:text-zinc-100">
        {value}
      </span>
    </div>
  );
}
