import { useEffect, useState, useCallback, useRef } from 'react';
import {
  Search, ChevronDown, ChevronRight, Loader2, Plus, Trash2,
  MessageSquare, ScrollText, SlidersHorizontal, X, RefreshCw,
  CheckSquare, Square, Bot, Zap, ZapOff, Activity,
} from 'lucide-react';
import {
  fetchChats,
  fetchBotsForChat,
  addChat as apiAddChat,
  deleteChat as apiDeleteChat,
  startBot as apiStartBot,
  stopBot as apiStopBot,
  updateBotSettings,
  bulkAction as apiBulkAction,
  type ChatRow,
  type ChatsListResponse,
  type BotInfo,
} from '../api/client';
import { Toggle } from '../components/Toggle';
import { StatusBadge } from '../components/StatusBadge';
import { BotLogsModal } from '../components/BotLogsModal';
import { MessagesModal } from '../components/MessagesModal';
import { Modal } from '../components/Modal';
import { toast } from '../components/toastStore';

const REFRESH_INTERVAL_MS = 30_000;

function normalizeChats(
  data: ChatsListResponse | ChatRow[],
): { chats: ChatRow[]; pagination?: ChatsListResponse['pagination'] } {
  if (Array.isArray(data)) return { chats: data };
  return { chats: data.chats ?? [], pagination: data.pagination };
}

const PER_PAGE_OPTIONS = [20, 50, 100];

const SORT_OPTIONS = [
  { value: 'last_message_time', label: 'Last Activity' },
  { value: 'chat_name', label: 'Name' },
  { value: 'message_count', label: 'Messages' },
  { value: 'added_at', label: 'Date Added' },
];

const ACTIVITY_OPTIONS = [
  { value: '', label: 'All Activity' },
  { value: 'active', label: 'Active' },
  { value: 'recent', label: 'Recent' },
  { value: 'idle', label: 'Idle' },
];

const TYPE_OPTIONS = [
  { value: '', label: 'All Types' },
  { value: 'group', label: 'Groups' },
  { value: 'individual', label: 'Individual' },
];

const BOT_STATUS_OPTIONS = [
  { value: '', label: 'All Chats' },
  { value: 'running', label: 'Has Running Bots' },
  { value: 'stopped', label: 'No Running Bots' },
];

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

function formatTime(ts: string | null | undefined): string {
  if (!ts) return '—';
  try {
    const d = new Date(ts);
    const now = new Date();
    const diff = (now.getTime() - d.getTime()) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return d.toLocaleDateString();
  } catch {
    return '—';
  }
}

interface BotSettingsInlineProps {
  bot: BotInfo;
  chatJid: string;
  allChats: ChatRow[];
  onUpdate: (botName: string, updates: Partial<BotInfo>) => void;
}

function BotSettingsInline({ bot, chatJid, allChats, onUpdate }: BotSettingsInlineProps) {
  const [contextVal, setContextVal] = useState(String(bot.context_message_count ?? 0));
  const [saving, setSaving] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  async function saveSettings(patch: { answer_owner_messages?: boolean; context_message_count?: number; response_chat_jid?: string | null }) {
    setSaving(true);
    try {
      await updateBotSettings(bot.name, chatJid, patch);
      onUpdate(bot.name, patch);
      toast('Settings saved', 'success');
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Failed to save settings', 'error');
    } finally {
      setSaving(false);
    }
  }

  function handleContextChange(v: string) {
    setContextVal(v);
    if (timerRef.current) clearTimeout(timerRef.current);
    const num = parseInt(v, 10);
    if (!isNaN(num) && num >= 0) {
      timerRef.current = setTimeout(() => saveSettings({ context_message_count: num }), 800);
    }
  }

  useEffect(() => {
    setContextVal(String(bot.context_message_count ?? 0));
  }, [bot.context_message_count]);

  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current); }, []);

  return (
    <div className="bot-settings-row">
      <span className="setting-label">Settings:</span>
      <label className="setting-item">
        <span className="setting-label">Answer owner</span>
        <Toggle
          checked={bot.answer_owner_messages !== false}
          disabled={saving}
          label="Toggle answer owner messages"
          onChange={(v) => saveSettings({ answer_owner_messages: v })}
        />
      </label>
      <label className="setting-item">
        <span className="setting-label">Context</span>
        <input
          type="number"
          min={0}
          max={100}
          className="setting-input"
          value={contextVal}
          onChange={(e) => handleContextChange(e.target.value)}
          aria-label="Context message count"
          title="Number of previous messages to include as context"
        />
        <span className="setting-label">msgs</span>
      </label>
      <label className="setting-item">
        <span className="setting-label">Forward to</span>
        <select
          className="setting-input"
          value={bot.response_chat_jid ?? ''}
          disabled={saving}
          onChange={(e) => {
            const val = e.target.value || null;
            saveSettings({ response_chat_jid: val });
          }}
          aria-label="Forward response to another chat"
          title="Forward original message and bot response to another chat"
        >
          <option value="">Same chat</option>
          {allChats
            .filter((c) => c.chat_jid !== chatJid)
            .map((c) => (
              <option key={c.chat_jid} value={c.chat_jid}>
                {c.chat_name || c.chat_jid.split('@')[0]}
              </option>
            ))}
        </select>
      </label>
      {saving && <Loader2 size={12} className="spin muted" />}
    </div>
  );
}

interface AddChatModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdded: () => void;
}

function AddChatModal({ isOpen, onClose, onAdded }: AddChatModalProps) {
  const [jid, setJid] = useState('');
  const [name, setName] = useState('');
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!jid.trim()) return;
    setSaving(true);
    try {
      await apiAddChat(jid.trim(), name.trim() || undefined);
      toast(`Chat "${name || jid}" added`, 'success');
      setJid('');
      setName('');
      onClose();
      onAdded();
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Failed to add chat', 'error');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add Chat Manually" size="sm">
      <form className="add-chat-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label" htmlFor="chat-jid">Chat JID *</label>
          <input
            id="chat-jid"
            type="text"
            className="form-input"
            placeholder="1234567890@s.whatsapp.net"
            value={jid}
            onChange={(e) => setJid(e.target.value)}
            required
            autoFocus
          />
          <span className="form-help">Use @s.whatsapp.net for individuals, @g.us for groups</span>
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="chat-name">Display Name (optional)</label>
          <input
            id="chat-name"
            type="text"
            className="form-input"
            placeholder="My Chat"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div className="form-actions">
          <button type="button" className="btn secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn primary" disabled={saving || !jid.trim()}>
            {saving ? 'Adding…' : 'Add Chat'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export function Chats() {
  const [chats, setChats] = useState<ChatRow[]>([]);
  const [pagination, setPagination] = useState<ChatsListResponse['pagination']>();
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('last_message_time');
  const [order] = useState('desc');
  const [activity, setActivity] = useState('');
  const [chatType, setChatType] = useState('');
  const [botStatusFilter, setBotStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [showFilters, setShowFilters] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);

  // All chats (unfiltered) for "Forward to" dropdown
  const [allChats, setAllChats] = useState<ChatRow[]>([]);

  // Expanded + bots state
  const [expandedJid, setExpandedJid] = useState<string | null>(null);
  const [chatBots, setChatBots] = useState<Record<string, BotInfo[]>>({});
  const [loadingBots, setLoadingBots] = useState<string | null>(null);
  const [togglingKey, setTogglingKey] = useState<string | null>(null);

  // Bulk selection
  const [selectedJids, setSelectedJids] = useState<Set<string>>(new Set());
  const [bulkActioning, setBulkActioning] = useState(false);

  // Modals
  const [logsTarget, setLogsTarget] = useState<{ botName: string; displayName: string; chatJid: string } | null>(null);
  const [messagesTarget, setMessagesTarget] = useState<{ chatJid: string; chatName: string } | null>(null);
  const [showAddChat, setShowAddChat] = useState(false);
  const [deletingJid, setDeletingJid] = useState<string | null>(null);
  const [confirmDeleteJid, setConfirmDeleteJid] = useState<string | null>(null);

  const loadChats = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('per_page', String(perPage));
      params.set('page', String(page));
      params.set('sort', sort);
      params.set('order', order);
      if (search) params.set('search', search);
      if (activity) params.set('activity', activity);
      if (chatType) params.set('chat_type', chatType);
      const data = await fetchChats(params);
      const { chats: c, pagination: p } = normalizeChats(data);
      setChats(c);
      setPagination(p);
      setErr(null);
      setLastRefreshed(new Date());
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load chats');
    } finally {
      setLoading(false);
    }
  }, [page, perPage, search, sort, order, activity, chatType]);

  useEffect(() => {
    loadChats();
  }, [loadChats]);

  // Fetch full (unfiltered) chat list for "Forward to" dropdowns
  useEffect(() => {
    (async () => {
      try {
        const params = new URLSearchParams({ per_page: '500', page: '1', sort: 'chat_name', order: 'asc' });
        const data = await fetchChats(params);
        const list = Array.isArray(data) ? data : ((data as ChatsListResponse).chats ?? []);
        setAllChats(list);
      } catch { /* silently fail -- dropdown will just be empty */ }
    })();
  }, []);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(() => loadChats(), REFRESH_INTERVAL_MS);
    return () => clearInterval(id);
  }, [autoRefresh, loadChats]);

  // Reset to page 1 on filter change
  useEffect(() => { setPage(1); }, [search, sort, activity, chatType, perPage]);
  // Clear selection on data change
  useEffect(() => { setSelectedJids(new Set()); }, [chats]);

  // Client-side bot status filter
  const displayedChats = botStatusFilter === 'running'
    ? chats.filter((c) => c.bots?.some((b) => b.status === 'running'))
    : botStatusFilter === 'stopped'
      ? chats.filter((c) => !c.bots?.some((b) => b.status === 'running'))
      : chats;

  async function toggleChat(jid: string) {
    if (expandedJid === jid) {
      setExpandedJid(null);
      return;
    }
    setExpandedJid(jid);
    if (!chatBots[jid]) {
      setLoadingBots(jid);
      try {
        const bots = await fetchBotsForChat(jid);
        setChatBots((prev) => ({ ...prev, [jid]: bots }));
      } catch (e) {
        toast(e instanceof Error ? e.message : 'Failed to load bots', 'error');
      } finally {
        setLoadingBots(null);
      }
    }
  }

  async function handleToggleBot(botName: string, chatJid: string, currentlyRunning: boolean) {
    const key = `${botName}:${chatJid}`;
    setTogglingKey(key);
    setChatBots((prev) => ({
      ...prev,
      [chatJid]: (prev[chatJid] ?? []).map((b) =>
        b.name === botName ? { ...b, status: currentlyRunning ? 'stopped' : 'running' } : b,
      ),
    }));
    try {
      if (currentlyRunning) {
        await apiStopBot(botName, chatJid);
        toast(`Stopped ${botName}`, 'success');
      } else {
        await apiStartBot(botName, chatJid);
        toast(`Started ${botName}`, 'success');
      }
      const fresh = await fetchBotsForChat(chatJid);
      setChatBots((prev) => ({ ...prev, [chatJid]: fresh }));
    } catch (e) {
      setChatBots((prev) => ({
        ...prev,
        [chatJid]: (prev[chatJid] ?? []).map((b) =>
          b.name === botName ? { ...b, status: currentlyRunning ? 'running' : 'stopped' } : b,
        ),
      }));
      toast(e instanceof Error ? e.message : 'Action failed', 'error');
    } finally {
      setTogglingKey(null);
    }
  }

  function handleBotSettingsUpdate(chatJid: string, botName: string, updates: Partial<BotInfo>) {
    setChatBots((prev) => ({
      ...prev,
      [chatJid]: (prev[chatJid] ?? []).map((b) =>
        b.name === botName ? { ...b, ...updates } : b,
      ),
    }));
  }

  async function handleDeleteChat(jid: string) {
    setDeletingJid(jid);
    try {
      await apiDeleteChat(jid);
      toast('Chat deleted', 'success');
      setConfirmDeleteJid(null);
      if (expandedJid === jid) setExpandedJid(null);
      setChatBots((prev) => { const n = { ...prev }; delete n[jid]; return n; });
      setChats((prev) => prev.filter((c) => c.chat_jid !== jid));
      setSelectedJids((prev) => { const n = new Set(prev); n.delete(jid); return n; });
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Failed to delete chat', 'error');
    } finally {
      setDeletingJid(null);
    }
  }

  // Bulk selection
  function toggleSelectJid(jid: string) {
    setSelectedJids((prev) => {
      const n = new Set(prev);
      if (n.has(jid)) n.delete(jid); else n.add(jid);
      return n;
    });
  }

  function selectAll() {
    setSelectedJids(new Set(displayedChats.map((c) => c.chat_jid)));
  }

  function clearSelection() {
    setSelectedJids(new Set());
  }

  const allSelected = displayedChats.length > 0 && selectedJids.size === displayedChats.length;
  const someSelected = selectedJids.size > 0 && !allSelected;

  async function handleBulkAction(action: string, botName?: string) {
    const jids = Array.from(selectedJids);
    if (!jids.length) return;
    setBulkActioning(true);
    try {
      const result = await apiBulkAction(jids, action, botName);
      toast(result.message || `${action} completed for ${result.success?.length ?? jids.length} chats`, 'success');
      clearSelection();
      loadChats();
      // Invalidate bot caches for affected chats
      setChatBots((prev) => {
        const n = { ...prev };
        jids.forEach((jid) => delete n[jid]);
        return n;
      });
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Bulk action failed', 'error');
    } finally {
      setBulkActioning(false);
    }
  }

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
  }

  const hasActiveFilters = activity || chatType || sort !== 'last_message_time' || botStatusFilter;
  const totalPages = pagination?.total_pages ?? 1;

  if (err && chats.length === 0) {
    return (
      <div className="panel error-panel">
        <p>{err}</p>
      </div>
    );
  }

  return (
    <div className="chats-page">
      <div className="page-header">
        <h2>Chats</h2>
        {pagination && <span className="muted">{pagination.total} total</span>}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          {lastRefreshed && (
            <span className="refresh-indicator">{lastRefreshed.toLocaleTimeString()}</span>
          )}
          <button
            type="button"
            className={`btn secondary btn-sm ${autoRefresh ? 'auto-refresh-active' : ''}`}
            onClick={() => setAutoRefresh((v) => !v)}
            title={autoRefresh ? 'Disable auto-refresh' : 'Enable auto-refresh (30s)'}
          >
            <Activity size={13} className={autoRefresh ? 'spin-slow' : ''} />
            {autoRefresh ? 'Auto' : 'Auto'}
          </button>
          <button
            type="button"
            className="btn secondary btn-sm"
            onClick={() => loadChats()}
            disabled={loading}
          >
            <RefreshCw size={13} className={loading ? 'spin' : ''} />
          </button>
          <button
            type="button"
            className={`btn secondary btn-sm ${hasActiveFilters ? 'filter-active' : ''}`}
            onClick={() => setShowFilters(!showFilters)}
            aria-expanded={showFilters}
          >
            <SlidersHorizontal size={14} />
            Filters
            {hasActiveFilters && <span className="filter-dot" />}
          </button>
          <button
            type="button"
            className="btn primary btn-sm"
            onClick={() => setShowAddChat(true)}
          >
            <Plus size={14} /> Add Chat
          </button>
        </div>
      </div>

      <form className="search-bar" onSubmit={handleSearchSubmit}>
        <Search size={16} className="search-icon" />
        <input
          type="text"
          placeholder="Search by name or JID…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="search-input"
        />
        {search && (
          <button
            type="button"
            className="search-clear"
            onClick={() => setSearch('')}
            aria-label="Clear search"
          >
            <X size={14} />
          </button>
        )}
      </form>

      {showFilters && (
        <div className="filters-bar">
          <div className="filter-group">
            <label className="filter-label">Sort</label>
            <select
              className="filter-select"
              value={sort}
              onChange={(e) => setSort(e.target.value)}
            >
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label className="filter-label">Activity</label>
            <select
              className="filter-select"
              value={activity}
              onChange={(e) => setActivity(e.target.value)}
            >
              {ACTIVITY_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label className="filter-label">Type</label>
            <select
              className="filter-select"
              value={chatType}
              onChange={(e) => setChatType(e.target.value)}
            >
              {TYPE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label className="filter-label">Bots</label>
            <select
              className="filter-select"
              value={botStatusFilter}
              onChange={(e) => setBotStatusFilter(e.target.value)}
            >
              {BOT_STATUS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label className="filter-label">Per page</label>
            <select
              className="filter-select"
              value={perPage}
              onChange={(e) => setPerPage(Number(e.target.value))}
            >
              {PER_PAGE_OPTIONS.map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </div>
          {hasActiveFilters && (
            <button
              type="button"
              className="btn secondary btn-sm"
              onClick={() => { setSort('last_message_time'); setActivity(''); setChatType(''); setBotStatusFilter(''); }}
            >
              Reset
            </button>
          )}
        </div>
      )}

      {loading && chats.length === 0 ? (
        <p className="muted">Loading chats…</p>
      ) : displayedChats.length === 0 ? (
        <div className="empty-state">
          {botStatusFilter ? (
            <p>No chats match the bot status filter. <button type="button" className="link-btn" onClick={() => setBotStatusFilter('')}>Clear filter</button></p>
          ) : (
            <p>
              No chats found. Use <strong>Sync</strong> to import from WhatsApp or{' '}
              <button type="button" className="link-btn" onClick={() => setShowAddChat(true)}>add one manually</button>.
            </p>
          )}
        </div>
      ) : (
        <>
          {/* Select-all row */}
          <div className="select-all-row">
            <button
              type="button"
              className="btn-icon-plain select-all-btn"
              onClick={allSelected ? clearSelection : selectAll}
              aria-label={allSelected ? 'Deselect all' : 'Select all'}
              title={allSelected ? 'Deselect all' : 'Select all visible chats'}
            >
              {allSelected ? (
                <CheckSquare size={16} style={{ color: 'var(--accent)' }} />
              ) : someSelected ? (
                <CheckSquare size={16} style={{ color: 'var(--text-muted)', opacity: 0.6 }} />
              ) : (
                <Square size={16} style={{ color: 'var(--text-muted)' }} />
              )}
            </button>
            <span className="select-all-label">
              {selectedJids.size > 0
                ? `${selectedJids.size} selected`
                : `${displayedChats.length} chat${displayedChats.length !== 1 ? 's' : ''}`}
            </span>
            {selectedJids.size > 0 && (
              <button type="button" className="link-btn" onClick={clearSelection}>
                Clear
              </button>
            )}
          </div>

          <ul className="chat-list">
            {displayedChats.map((c) => {
              const isExpanded = expandedJid === c.chat_jid;
              const bots = chatBots[c.chat_jid];
              const isLoadingBots = loadingBots === c.chat_jid;
              const runningCount = c.bots?.filter((b) => b.status === 'running').length ?? 0;
              const isConfirmingDelete = confirmDeleteJid === c.chat_jid;
              const isSelected = selectedJids.has(c.chat_jid);

              return (
                <li key={c.chat_jid} className={`chat-row ${isExpanded ? 'chat-row-expanded' : ''} ${isSelected ? 'chat-row-selected' : ''}`}>
                  <div className="chat-row-header">
                    <button
                      type="button"
                      className="btn-icon-plain chat-checkbox-btn"
                      onClick={(e) => { e.stopPropagation(); toggleSelectJid(c.chat_jid); }}
                      aria-label={isSelected ? 'Deselect chat' : 'Select chat'}
                    >
                      {isSelected
                        ? <CheckSquare size={15} style={{ color: 'var(--accent)' }} />
                        : <Square size={15} style={{ color: 'var(--text-muted)' }} />}
                    </button>
                    <div
                      className="chat-row-clickable"
                      onClick={() => toggleChat(c.chat_jid)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && toggleChat(c.chat_jid)}
                    >
                      <div className="chat-row-expand">
                        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      </div>
                      <div className="chat-row-main">
                        <span className="chat-name">{c.chat_name}</span>
                        <span className="chat-jid">{c.chat_jid}</span>
                      </div>
                      <div className="chat-row-meta">
                        {runningCount > 0 && (
                          <span className="running-count">
                            {runningCount} bot{runningCount !== 1 ? 's' : ''} active
                          </span>
                        )}
                        {c.last_message_time && (
                          <span className="last-activity">{formatTime(c.last_message_time)}</span>
                        )}
                        {c.message_count != null && c.message_count > 0 && (
                          <span className="msg-count">{c.message_count.toLocaleString()} msgs</span>
                        )}
                        {c.is_manual && (
                          <span className="manual-badge">manual</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="chat-bots-panel">
                      {isLoadingBots ? (
                        <div className="bots-loading">
                          <Loader2 size={16} className="spin" /> Loading bots…
                        </div>
                      ) : bots && bots.length > 0 ? (
                        <ul className="bots-list">
                          {bots.map((b) => {
                            const isRunning = b.status === 'running';
                            const key = `${b.name}:${c.chat_jid}`;
                            return (
                              <li key={b.name} className="bot-row-wrapper">
                                <div className="bot-row">
                                  <div className="bot-row-info">
                                    <span className="bot-display-name">{b.display_name}</span>
                                    <span className="prefix-badge">{b.prefix}</span>
                                    <StatusBadge status={b.status} />
                                    {isRunning && b.uptime_seconds != null && (
                                      <span className="bot-uptime">{formatUptime(b.uptime_seconds)}</span>
                                    )}
                                  </div>
                                  <div className="bot-row-actions">
                                    <button
                                      type="button"
                                      className="btn-icon"
                                      title="View logs"
                                      onClick={() => setLogsTarget({ botName: b.name, displayName: b.display_name, chatJid: c.chat_jid })}
                                      aria-label={`View logs for ${b.display_name}`}
                                    >
                                      <ScrollText size={14} />
                                    </button>
                                    <Toggle
                                      checked={isRunning}
                                      disabled={togglingKey === key}
                                      label={`${isRunning ? 'Stop' : 'Start'} ${b.display_name}`}
                                      onChange={() => handleToggleBot(b.name, c.chat_jid, isRunning)}
                                    />
                                  </div>
                                </div>
                                <BotSettingsInline
                                  bot={b}
                                  chatJid={c.chat_jid}
                                  allChats={allChats}
                                  onUpdate={(botName, updates) => handleBotSettingsUpdate(c.chat_jid, botName, updates)}
                                />
                              </li>
                            );
                          })}
                        </ul>
                      ) : bots ? (
                        <p className="muted bots-empty">No bot types available.</p>
                      ) : null}

                      <div className="chat-row-actions">
                        <button
                          type="button"
                          className="btn secondary btn-sm"
                          onClick={() => setMessagesTarget({ chatJid: c.chat_jid, chatName: c.chat_name })}
                        >
                          <MessageSquare size={13} /> Messages
                        </button>
                        {isConfirmingDelete ? (
                          <div className="inline-confirm">
                            <span>Delete this chat?</span>
                            <button
                              type="button"
                              className="btn btn-sm btn-danger"
                              disabled={deletingJid === c.chat_jid}
                              onClick={() => handleDeleteChat(c.chat_jid)}
                            >
                              {deletingJid === c.chat_jid ? 'Deleting…' : 'Confirm Delete'}
                            </button>
                            <button
                              type="button"
                              className="btn secondary btn-sm"
                              onClick={() => setConfirmDeleteJid(null)}
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button
                            type="button"
                            className="btn secondary btn-sm btn-danger-ghost"
                            onClick={(e) => { e.stopPropagation(); setConfirmDeleteJid(c.chat_jid); }}
                          >
                            <Trash2 size={13} /> Delete
                          </button>
                        )}
                      </div>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                type="button"
                className="btn secondary btn-sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </button>
              <span className="pagination-info">
                Page {page} of {totalPages}
                {pagination && ` · ${pagination.total} chats`}
              </span>
              <button
                type="button"
                className="btn secondary btn-sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {/* Bulk action toolbar */}
      {selectedJids.size > 0 && (
        <div className="bulk-toolbar" role="toolbar" aria-label="Bulk actions">
          <span className="bulk-count">{selectedJids.size} selected</span>
          <div className="bulk-actions">
            <button
              type="button"
              className="btn primary btn-sm"
              disabled={bulkActioning}
              onClick={() => handleBulkAction('start_bots')}
              title="Start all bots in selected chats"
            >
              <Zap size={13} /> Start Bots
            </button>
            <button
              type="button"
              className="btn secondary btn-sm"
              disabled={bulkActioning}
              onClick={() => handleBulkAction('stop_bots')}
              title="Stop all bots in selected chats"
            >
              <ZapOff size={13} /> Stop Bots
            </button>
            <button
              type="button"
              className="btn secondary btn-sm btn-danger-ghost"
              disabled={bulkActioning}
              onClick={() => {
                if (window.confirm(`Delete ${selectedJids.size} chat(s)? This cannot be undone.`)) {
                  handleBulkAction('delete_chats');
                }
              }}
              title="Delete selected chats"
            >
              <Trash2 size={13} /> Delete
            </button>
            <button
              type="button"
              className="btn-icon"
              onClick={clearSelection}
              aria-label="Clear selection"
              title="Clear selection"
            >
              <X size={14} />
            </button>
          </div>
          {bulkActioning && <Loader2 size={14} className="spin muted" />}
        </div>
      )}

      <AddChatModal
        isOpen={showAddChat}
        onClose={() => setShowAddChat(false)}
        onAdded={loadChats}
      />

      {logsTarget && (
        <BotLogsModal
          isOpen={!!logsTarget}
          onClose={() => setLogsTarget(null)}
          botName={logsTarget.botName}
          botDisplayName={logsTarget.displayName}
          chatJid={logsTarget.chatJid}
        />
      )}

      {messagesTarget && (
        <MessagesModal
          isOpen={!!messagesTarget}
          onClose={() => setMessagesTarget(null)}
          chatJid={messagesTarget.chatJid}
          chatName={messagesTarget.chatName}
        />
      )}

      {/* Bot count legend */}
      {chats.length > 0 && (
        <div className="chats-legend">
          <Bot size={12} />
          <span>Expand a chat to manage its bots and settings</span>
        </div>
      )}
    </div>
  );
}
