import { useEffect, useState } from 'react';
import { fetchStats, type StatsResponse } from '../api/client';

export function Overview() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await fetchStats();
        if (!cancelled) setStats(s);
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : 'Failed to load stats');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (err) {
    return (
      <div className="panel error-panel">
        <p>{err}</p>
      </div>
    );
  }

  if (!stats) {
    return <p className="muted">Loading overview…</p>;
  }

  return (
    <div className="stats-grid">
      <div className="stat-card">
        <div className="stat-value">{stats.total_chats}</div>
        <div className="stat-label">Total chats</div>
      </div>
      <div className="stat-card">
        <div className="stat-value">{stats.running_bots}</div>
        <div className="stat-label">Bots running</div>
      </div>
      <div className="stat-card">
        <div className="stat-value">{stats.stopped_bots}</div>
        <div className="stat-label">Bots stopped</div>
      </div>
      <div className="stat-card">
        <div className="stat-value">{stats.available_bot_types}</div>
        <div className="stat-label">Bot types</div>
      </div>
    </div>
  );
}
