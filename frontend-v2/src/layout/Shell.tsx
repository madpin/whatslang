import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useState, useCallback } from 'react';
import { postSyncChats } from '../api/client';

const CLASSIC = '/static/index.html';

export function Shell() {
  const [syncMsg, setSyncMsg] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const navigate = useNavigate();

  const onSync = useCallback(async () => {
    setSyncMsg(null);
    setSyncing(true);
    try {
      const r = await postSyncChats();
      setSyncMsg(r.message);
      navigate(0);
    } catch (e) {
      setSyncMsg(e instanceof Error ? e.message : 'Sync failed');
    } finally {
      setSyncing(false);
    }
  }, [navigate]);

  function onLogout() {
    if (!window.confirm('Log out of the dashboard?')) return;
    sessionStorage.removeItem('auth_token');
    sessionStorage.removeItem('redirect_after_login');
    window.location.replace('/static/login.html');
  }

  return (
    <div className="app-shell">
      <header className="top">
        <div className="brand">
          <span className="brand-mark">WhatsLang</span>
          <span className="brand-badge">beta</span>
        </div>
        <nav className="nav">
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
            Overview
          </NavLink>
          <NavLink to="/chats" className={({ isActive }) => (isActive ? 'active' : '')}>
            Chats
          </NavLink>
        </nav>
        <div className="actions">
          <button type="button" className="btn secondary" onClick={() => window.location.assign(CLASSIC)}>
            Classic dashboard
          </button>
          <button type="button" className="btn secondary" onClick={onLogout}>
            Log out
          </button>
          <button type="button" className="btn primary" onClick={onSync} disabled={syncing}>
            {syncing ? 'Syncing…' : 'Sync from WhatsApp'}
          </button>
        </div>
      </header>
      {syncMsg ? <div className="banner">{syncMsg}</div> : null}
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
