import { useEffect, useState, useCallback } from 'react';
import { Search, ChevronDown, ChevronRight, Loader2 } from 'lucide-react';
import {
  fetchChats,
  fetchBotsForChat,
  startBot as apiStartBot,
  stopBot as apiStopBot,
  type ChatRow,
  type ChatsListResponse,
  type BotInfo,
} from '../api/client';
import { Toggle } from '../components/Toggle';
import { StatusBadge } from '../components/StatusBadge';
import { toast } from '../components/toastStore';

function normalizeChats(
  data: ChatsListResponse | ChatRow[],
): { chats: ChatRow[]; pagination?: ChatsListResponse['pagination'] } {
  if (Array.isArray(data)) return { chats: data };
  return { chats: data.chats ?? [], pagination: data.pagination };
}

const PER_PAGE_OPTIONS = [20, 50, 100];

export function Chats() {
  const [chats, setChats] = useState<ChatRow[]>([]);
  const [pagination, setPagination] = useState<ChatsListResponse['pagination']>();
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);

  const [expandedJid, setExpandedJid] = useState<string | null>(null);
  const [chatBots, setChatBots] = useState<Record<string, BotInfo[]>>({});
  const [loadingBots, setLoadingBots] = useState<string | null>(null);
  const [togglingKey, setTogglingKey] = useState<string | null>(null);

  const loadChats = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('per_page', String(perPage));
      params.set('page', String(page));
      if (search) params.set('search', search);
      const data = await fetchChats(params);
      const { chats: c, pagination: p } = normalizeChats(data);
      setChats(c);
      setPagination(p);
      setErr(null);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load chats');
    } finally {
      setLoading(false);
    }
  }, [page, perPage, search]);

  useEffect(() => {
    loadChats();
  }, [loadChats]);

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
        toast(e instanceof Error ? e.message : 'Failed to load bots for chat', 'error');
      } finally {
        setLoadingBots(null);
      }
    }
  }

  async function handleToggleBot(botName: string, chatJid: string, currentlyRunning: boolean) {
    const key = `${botName}:${chatJid}`;
    setTogglingKey(key);

    // Optimistic update
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
      // Refresh the real state from server
      const fresh = await fetchBotsForChat(chatJid);
      setChatBots((prev) => ({ ...prev, [chatJid]: fresh }));
    } catch (e) {
      // Rollback on error
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

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
  }

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
      </div>

      <form className="search-bar" onSubmit={handleSearchSubmit}>
        <Search size={16} className="search-icon" />
        <input
          type="text"
          placeholder="Search by name or JID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="search-input"
        />
      </form>

      {loading && chats.length === 0 ? (
        <p className="muted">Loading chats...</p>
      ) : chats.length === 0 ? (
        <div className="empty-state">
          <p>
            No chats found. Use <strong>Sync from WhatsApp</strong> to import your chats.
          </p>
        </div>
      ) : (
        <>
          <ul className="chat-list">
            {chats.map((c) => {
              const isExpanded = expandedJid === c.chat_jid;
              const bots = chatBots[c.chat_jid];
              const isLoadingBots = loadingBots === c.chat_jid;
              const runningCount = c.bots?.filter((b) => b.status === 'running').length ?? 0;

              return (
                <li key={c.chat_jid} className={`chat-row ${isExpanded ? 'chat-row-expanded' : ''}`}>
                  <div className="chat-row-header" onClick={() => toggleChat(c.chat_jid)}>
                    <div className="chat-row-expand">
                      {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    </div>
                    <div className="chat-row-main">
                      <span className="chat-name">{c.chat_name}</span>
                      <span className="chat-jid">{c.chat_jid}</span>
                    </div>
                    <div className="chat-row-meta">
                      {runningCount > 0 && (
                        <span className="running-count">{runningCount} bot{runningCount !== 1 ? 's' : ''} active</span>
                      )}
                      {c.message_count != null && (
                        <span className="msg-count">{c.message_count} msg{c.message_count !== 1 ? 's' : ''}</span>
                      )}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="chat-bots-panel">
                      {isLoadingBots ? (
                        <div className="bots-loading">
                          <Loader2 size={16} className="spin" /> Loading bots...
                        </div>
                      ) : bots && bots.length > 0 ? (
                        <ul className="bots-list">
                          {bots.map((b) => {
                            const isRunning = b.status === 'running';
                            const key = `${b.name}:${c.chat_jid}`;
                            return (
                              <li key={b.name} className="bot-row">
                                <div className="bot-row-info">
                                  <span className="bot-display-name">{b.display_name}</span>
                                  <span className="prefix-badge">{b.prefix}</span>
                                  <StatusBadge status={b.status} />
                                  {isRunning && b.uptime_seconds != null && (
                                    <span className="bot-uptime">{formatUptime(b.uptime_seconds)}</span>
                                  )}
                                </div>
                                <Toggle
                                  checked={isRunning}
                                  disabled={togglingKey === key}
                                  label={`${isRunning ? 'Stop' : 'Start'} ${b.display_name}`}
                                  onChange={() => handleToggleBot(b.name, c.chat_jid, isRunning)}
                                />
                              </li>
                            );
                          })}
                        </ul>
                      ) : bots ? (
                        <p className="muted bots-empty">No bot types available.</p>
                      ) : null}
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
              </span>
              <button
                type="button"
                className="btn secondary btn-sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
              <select
                className="per-page-select"
                value={perPage}
                onChange={(e) => { setPerPage(Number(e.target.value)); setPage(1); }}
              >
                {PER_PAGE_OPTIONS.map((n) => (
                  <option key={n} value={n}>{n} / page</option>
                ))}
              </select>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}
