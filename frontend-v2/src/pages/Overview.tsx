import { useEffect, useState, useCallback } from 'react';
import { RefreshCw, Bot, MessageSquare, Zap, Database, ZapOff, Activity, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import {
  fetchStats, fetchRunningBots, stopBot as apiStopBot,
  type StatsResponse, type BotInfo,
} from '../api/client';
import { toast } from '../components/toastStore';

const REFRESH_INTERVAL_MS = 30_000;

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

const STAT_CARDS = [
  { key: 'total_chats' as const, label: 'Total Chats', icon: MessageSquare, color: '#6366f1', link: '/chats' },
  { key: 'running_bots' as const, label: 'Bots Running', icon: Zap, color: '#22c55e', link: '/bots' },
  { key: 'stopped_bots' as const, label: 'Bots Stopped', icon: Bot, color: '#9ca3af', link: '/bots' },
  { key: 'available_bot_types' as const, label: 'Bot Types', icon: Database, color: '#f59e0b', link: '/bots' },
];

export function Overview() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [runningBots, setRunningBots] = useState<BotInfo[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [stoppingKey, setStoppingKey] = useState<string | null>(null);

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

  async function handleStop(botName: string, chatJid: string) {
    const key = `${botName}:${chatJid}`;
    setStoppingKey(key);
    try {
      await apiStopBot(botName, chatJid);
      toast(`Stopped ${botName}`, 'success');
      setRunningBots((prev) => prev.filter((b) => !(b.name === botName && b.chat_jid === chatJid)));
      setStats((prev) => prev
        ? { ...prev, running_bots: Math.max(0, prev.running_bots - 1), stopped_bots: prev.stopped_bots + 1 }
        : prev);
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Failed to stop bot', 'error');
    } finally {
      setStoppingKey(null);
    }
  }

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

  // Group running bots by bot type
  const botsByType = runningBots.reduce<Record<string, BotInfo[]>>((acc, b) => {
    if (!acc[b.name]) acc[b.name] = [];
    acc[b.name].push(b);
    return acc;
  }, {});

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
        {stats && STAT_CARDS.map(({ key, label, icon: Icon, color, link }) => (
          <Link key={key} to={link} className="stat-card stat-card-link">
            <div className="stat-card-icon" style={{ color }}>
              <Icon size={20} />
            </div>
            <div className="stat-value">{stats[key]}</div>
            <div className="stat-label">{label}</div>
          </Link>
        ))}
      </div>

      {runningBots.length > 0 && (
        <div className="running-bots-section">
          <div className="section-header">
            <Activity size={16} style={{ color: 'var(--green)' }} />
            <h3 className="section-title">Active Bots</h3>
            <span className="muted">
              {runningBots.length} instance{runningBots.length !== 1 ? 's' : ''}
            </span>
            <Link to="/bots" className="section-link">
              Manage <ArrowRight size={12} />
            </Link>
          </div>

          {Object.entries(botsByType).map(([botName, instances]) => (
            <div key={botName} className="overview-bot-group">
              <div className="overview-bot-group-header">
                <Bot size={14} />
                <span className="overview-bot-group-name">{instances[0].display_name}</span>
                <span className="prefix-badge">{instances[0].prefix}</span>
                <span className="muted" style={{ fontSize: '0.72rem' }}>
                  {instances.length} instance{instances.length !== 1 ? 's' : ''}
                </span>
              </div>
              <ul className="running-bots-list">
                {instances.map((b) => {
                  const key = `${b.name}:${b.chat_jid}`;
                  return (
                    <li key={key} className="running-bot-row">
                      <div className="running-bot-info">
                        <span className="running-bot-indicator" />
                        <span className="running-bot-chat">{b.chat_jid.split('@')[0]}</span>
                        {b.answer_owner_messages === false && (
                          <span className="overview-setting-badge">No owner msgs</span>
                        )}
                        {b.context_message_count != null && b.context_message_count > 0 && (
                          <span className="overview-setting-badge">{b.context_message_count}ctx</span>
                        )}
                      </div>
                      <div className="running-bot-right">
                        {b.uptime_seconds != null && (
                          <span className="instance-uptime">{formatUptime(b.uptime_seconds)}</span>
                        )}
                        <button
                          type="button"
                          className="btn-icon btn-stop"
                          title={`Stop in ${b.chat_jid.split('@')[0]}`}
                          disabled={stoppingKey === key}
                          onClick={() => handleStop(b.name, b.chat_jid)}
                          aria-label={`Stop ${b.display_name}`}
                        >
                          <ZapOff size={13} />
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
      )}

      {runningBots.length === 0 && stats && (
        <div className="overview-hint">
          <Bot size={36} className="hint-icon" />
          <p>No bots are currently running.</p>
          <div className="hint-actions">
            <Link to="/bots" className="btn primary btn-sm">
              <Zap size={13} /> Manage Bots
            </Link>
            <Link to="/chats" className="btn secondary btn-sm">
              <MessageSquare size={13} /> View Chats
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
