import { useEffect, useState, useCallback, useRef } from 'react';
import { RefreshCw, AlertCircle, Search, X, Download } from 'lucide-react';
import { fetchBotLogs, type LogEntry } from '../api/client';
import { Modal } from './Modal';

interface BotLogsModalProps {
  isOpen: boolean;
  onClose: () => void;
  botName: string;
  botDisplayName: string;
  chatJid: string;
}

const LEVEL_CLASS: Record<string, string> = {
  INFO: 'log-level-info',
  WARNING: 'log-level-warning',
  WARN: 'log-level-warning',
  ERROR: 'log-level-error',
  DEBUG: 'log-level-debug',
  CRITICAL: 'log-level-critical',
};

const LEVEL_COLORS: Record<string, string> = {
  INFO: '#60a5fa',
  WARNING: '#fbbf24',
  ERROR: '#f87171',
  DEBUG: '#a78bfa',
  CRITICAL: '#fca5a5',
};

const LEVEL_OPTIONS = ['', 'INFO', 'WARNING', 'ERROR', 'DEBUG', 'CRITICAL'];

function formatLogTime(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return ts;
  }
}

export function BotLogsModal({ isOpen, onClose, botName, botDisplayName, chatJid }: BotLogsModalProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [lastFetched, setLastFetched] = useState<Date | null>(null);
  const [levelFilter, setLevelFilter] = useState('');
  const [logSearch, setLogSearch] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [logLimit, setLogLimit] = useState(200);
  const bottomRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    if (!isOpen) return;
    setLoading(true);
    setErr(null);
    try {
      const data = await fetchBotLogs(botName, chatJid, logLimit);
      setLogs(data.logs);
      setLastFetched(new Date());
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load logs');
    } finally {
      setLoading(false);
    }
  }, [isOpen, botName, chatJid, logLimit]);

  useEffect(() => {
    if (isOpen) load();
  }, [isOpen, load]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh || !isOpen) return;
    const id = setInterval(() => load(), 5000);
    return () => clearInterval(id);
  }, [autoRefresh, isOpen, load]);

  // Scroll to bottom on new logs when auto-refreshing
  useEffect(() => {
    if (autoRefresh && logs.length > 0) {
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    }
  }, [logs, autoRefresh]);

  const chatLabel = chatJid.split('@')[0];

  // Count by level for filter badges
  const levelCounts = logs.reduce<Record<string, number>>((acc, e) => {
    const lvl = (e.level ?? 'INFO').toUpperCase();
    acc[lvl] = (acc[lvl] ?? 0) + 1;
    return acc;
  }, {});

  const filteredLogs = logs
    .filter((entry) => !levelFilter || (entry.level ?? 'INFO').toUpperCase() === levelFilter)
    .filter((entry) => !logSearch || entry.message?.toLowerCase().includes(logSearch.toLowerCase()));

  function downloadLogs() {
    const content = filteredLogs
      .map((e) => `[${e.timestamp}] [${e.level}] ${e.message}`)
      .join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${botName}-${chatLabel}-logs.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Logs — ${botDisplayName} in ${chatLabel}`}
      size="lg"
      footer={
        <div className="modal-footer-row">
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            {lastFetched && (
              <span className="log-fetched-time">
                Updated {lastFetched.toLocaleTimeString()}
              </span>
            )}
            <button
              type="button"
              className={`btn secondary btn-sm ${autoRefresh ? 'auto-refresh-active' : ''}`}
              onClick={() => setAutoRefresh((v) => !v)}
              title={autoRefresh ? 'Disable auto-refresh (5s)' : 'Enable auto-refresh (5s)'}
            >
              {autoRefresh ? '⏸ Auto' : '▶ Auto'}
            </button>
            <select
              className="filter-select"
              value={logLimit}
              onChange={(e) => setLogLimit(Number(e.target.value))}
              style={{ fontSize: '0.73rem' }}
              aria-label="Log limit"
            >
              {[100, 200, 500].map((n) => (
                <option key={n} value={n}>{n} entries</option>
              ))}
            </select>
          </div>
          <div style={{ display: 'flex', gap: '0.4rem' }}>
            {filteredLogs.length > 0 && (
              <button type="button" className="btn secondary btn-sm" onClick={downloadLogs} title="Download logs">
                <Download size={13} />
              </button>
            )}
            <button type="button" className="btn secondary btn-sm" onClick={load} disabled={loading}>
              <RefreshCw size={13} className={loading ? 'spin' : ''} />
              {loading ? 'Loading…' : 'Refresh'}
            </button>
          </div>
        </div>
      }
    >
      {/* Level filter pills */}
      {logs.length > 0 && (
        <div className="log-filter-bar">
          {LEVEL_OPTIONS.map((lvl) => {
            const count = lvl ? (levelCounts[lvl] ?? 0) : logs.length;
            if (lvl && count === 0) return null;
            const color = lvl ? LEVEL_COLORS[lvl] : 'var(--text-muted)';
            return (
              <button
                key={lvl || 'all'}
                type="button"
                className={`level-pill ${levelFilter === lvl ? 'level-pill-active' : ''}`}
                style={{ '--pill-color': color } as React.CSSProperties}
                onClick={() => setLevelFilter(lvl)}
              >
                {lvl || 'All'} <span className="level-pill-count">{count}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Log search */}
      <div className="log-search-bar">
        <Search size={14} className="log-search-icon" />
        <input
          type="text"
          className="log-search-input"
          placeholder="Filter log messages…"
          value={logSearch}
          onChange={(e) => setLogSearch(e.target.value)}
        />
        {logSearch && (
          <button type="button" className="search-clear" onClick={() => setLogSearch('')} aria-label="Clear search">
            <X size={13} />
          </button>
        )}
      </div>

      {logSearch && filteredLogs.length !== logs.length && (
        <div className="msg-search-info" style={{ marginBottom: '0.5rem' }}>
          {filteredLogs.length} of {logs.length} entries match
        </div>
      )}

      {err ? (
        <div className="logs-error">
          <AlertCircle size={16} />
          <span>{err}</span>
        </div>
      ) : loading && logs.length === 0 ? (
        <p className="muted">Loading logs…</p>
      ) : filteredLogs.length === 0 ? (
        <p className="muted">
          {logs.length === 0
            ? 'No logs available. The bot may not have run yet or logs have expired.'
            : 'No logs match the current filter.'}
        </p>
      ) : (
        <div className="logs-container">
          {filteredLogs.map((entry, i) => {
            const lvl = (entry.level ?? 'INFO').toUpperCase();
            const cls = LEVEL_CLASS[lvl] ?? 'log-level-info';
            return (
              <div key={i} className="log-entry">
                <span className="log-time">{formatLogTime(entry.timestamp)}</span>
                <span className={`log-level ${cls}`}>{lvl.slice(0, 4)}</span>
                <span className="log-message">{entry.message}</span>
              </div>
            );
          })}
          <div ref={bottomRef} />
        </div>
      )}
    </Modal>
  );
}
