import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useState, useCallback } from 'react';
import { postSyncChats } from '../api/client';
import { ToastContainer } from '../components/Toast';
import { toast } from '../components/toastStore';

const CLASSIC = '/static/index.html';

export function Shell() {
  const [syncing, setSyncing] = useState(false);
  const navigate = useNavigate();

  const onSync = useCallback(async () => {
    setSyncing(true);
    try {
      const r = await postSyncChats();
      toast(r.message, 'success');
      navigate(0);
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Sync failed', 'error');
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
        </div>
        <nav className="nav">
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
            Overview
          </NavLink>
          <NavLink to="/bots" className={({ isActive }) => (isActive ? 'active' : '')}>
            Bots
          </NavLink>
          <NavLink to="/chats" className={({ isActive }) => (isActive ? 'active' : '')}>
            Chats
          </NavLink>
        </nav>
        <div className="actions">
          <button type="button" className="btn secondary" onClick={() => window.location.assign(CLASSIC)}>
            Classic UI
          </button>
          <button type="button" className="btn secondary" onClick={onLogout}>
            Log out
          </button>
          <button type="button" className="btn primary" onClick={onSync} disabled={syncing}>
            {syncing ? 'Syncing...' : 'Sync'}
          </button>
        </div>
      </header>
      <main className="main">
        <Outlet />
      </main>
      <ToastContainer />
    </div>
  );
}
