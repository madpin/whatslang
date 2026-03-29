import { useEffect, useState, useCallback } from 'react';
import { RefreshCw, AlertCircle } from 'lucide-react';
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

  const load = useCallback(async () => {
    if (!isOpen) return;
    setLoading(true);
    setErr(null);
    try {
      const data = await fetchBotLogs(botName, chatJid, 200);
      setLogs(data.logs);
      setLastFetched(new Date());
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load logs');
    } finally {
      setLoading(false);
    }
  }, [isOpen, botName, chatJid]);

  useEffect(() => {
    if (isOpen) load();
  }, [isOpen, load]);

  const chatLabel = chatJid.split('@')[0];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Logs — ${botDisplayName} in ${chatLabel}`}
      size="lg"
      footer={
        <div className="modal-footer-row">
          {lastFetched && (
            <span className="log-fetched-time">
              Updated {lastFetched.toLocaleTimeString()}
            </span>
          )}
          <button type="button" className="btn secondary btn-sm" onClick={load} disabled={loading}>
            <RefreshCw size={13} className={loading ? 'spin' : ''} />
            {loading ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      }
    >
      {err ? (
        <div className="logs-error">
          <AlertCircle size={16} />
          <span>{err}</span>
        </div>
      ) : loading && logs.length === 0 ? (
        <p className="muted">Loading logs…</p>
      ) : logs.length === 0 ? (
        <p className="muted">No logs available. The bot may not have run yet or logs expired.</p>
      ) : (
        <div className="logs-container">
          {logs.map((entry, i) => {
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
        </div>
      )}
    </Modal>
  );
}
