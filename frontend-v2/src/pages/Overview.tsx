import { useEffect, useState, useCallback } from 'react';
import { RefreshCw, Bot, MessageSquare, Zap, Database } from 'lucide-react';
import { fetchStats, fetchRunningBots, type StatsResponse, type BotInfo } from '../api/client';

const REFRESH_INTERVAL_MS = 30_000;

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

const STAT_CARDS = [
  { key: 'total_chats', label: 'Total Chats', icon: MessageSquare, color: '#6366f1' },
  { key: 'running_bots', label: 'Bots Running', icon: Zap, color: '#22c55e' },
  { key: 'stopped_bots', label: 'Bots Stopped', icon: Bot, color: '#9ca3af' },
  { key: 'available_bot_types', label: 'Bot Types', icon: Database, color: '#f59e0b' },
] as const;

export function Overview() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [runningBots, setRunningBots] = useState<BotInfo[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const [s, r] = await Promise.all([fetchStats(), fetchRunningBots()]);
      setStats(s);
      setRunningBots(r);
      setErr(null);
      setLastRefreshed(new Date());
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load stats');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(() => load(), REFRESH_INTERVAL_MS);
    return () => clearInterval(id);
  }, [load]);

  if (err && !stats) {
    return (
      <div className="panel error-panel">
        <p>{err}</p>
      </div>
    );
  }

  if (loading && !stats) {
    return <p className="muted">Loading overview…</p>;
  }

  return (
    <div>
      <div className="overview-header">
        <h2>Overview</h2>
        <div className="overview-refresh">
          {lastRefreshed && (
            <span className="refresh-indicator">
              Updated {lastRefreshed.toLocaleTimeString()}
            </span>
          )}
          <button
            type="button"
            className="btn secondary btn-sm"
            onClick={() => load(true)}
            disabled={refreshing}
            aria-label="Refresh stats"
          >
            <RefreshCw size={13} className={refreshing ? 'spin' : ''} />
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      </div>

      <div className="stats-grid">
        {stats && STAT_CARDS.map(({ key, label, icon: Icon, color }) => (
          <div key={key} className="stat-card">
            <div className="stat-card-icon" style={{ color }}>
              <Icon size={20} />
            </div>
            <div className="stat-value">{stats[key]}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>

      {runningBots.length > 0 && (
        <div className="running-bots-section">
          <div className="section-header">
            <h3 className="section-title">Running Bots</h3>
            <span className="muted">{runningBots.length} active instance{runningBots.length !== 1 ? 's' : ''}</span>
          </div>
          <ul className="running-bots-list">
            {runningBots.map((b) => (
              <li key={`${b.name}:${b.chat_jid}`} className="running-bot-row">
                <div className="running-bot-info">
                  <span className="running-bot-indicator" />
                  <span className="running-bot-name">{b.display_name}</span>
                  <span className="prefix-badge">{b.prefix}</span>
                  <span className="running-bot-chat">in {b.chat_jid.split('@')[0]}</span>
                </div>
                {b.uptime_seconds != null && (
                  <span className="instance-uptime">{formatUptime(b.uptime_seconds)}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {runningBots.length === 0 && stats && stats.running_bots === 0 && (
        <div className="overview-hint">
          <Bot size={32} className="hint-icon" />
          <p>No bots are running. Go to <strong>Chats</strong> or <strong>Bots</strong> to start one.</p>
        </div>
      )}
    </div>
  );
}
