import { useEffect, useState, useCallback, useRef } from 'react';
import {
  ChevronDown, Bot, Zap, ZapOff, PlayCircle,
  ScrollText, ChevronUp, Search, RefreshCw, Copy, Check,
  MessageSquare, Loader2, X,
} from 'lucide-react';
import {
  fetchBotTypes, fetchRunningBots, fetchChats,
  stopBot as apiStopBot, startBot as apiStartBot,
  updateBotSettings,
  type BotType, type BotInfo, type ChatRow, type ChatsListResponse,
} from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { BotLogsModal } from '../components/BotLogsModal';
import { MessagesModal } from '../components/MessagesModal';
import { Toggle } from '../components/Toggle';
import { toast } from '../components/toastStore';

const REFRESH_INTERVAL_MS = 30_000;

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

/* ---- Copy Button ---- */

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast('Failed to copy to clipboard', 'error');
    }
  }

  return (
    <button
      type="button"
      className={`btn-icon copy-btn ${copied ? 'copy-btn-done' : ''}`}
      onClick={handleCopy}
      title={copied ? 'Copied!' : 'Copy to clipboard'}
      aria-label="Copy system prompt"
    >
      {copied ? <Check size={12} /> : <Copy size={12} />}
    </button>
  );
}

/* ---- Bot Instance Settings ---- */

interface BotInstanceSettingsProps {
  bot: BotInfo;
  allChats: ChatRow[];
  onUpdate: (botName: string, chatJid: string, updates: Partial<BotInfo>) => void;
}

function BotInstanceSettings({ bot, allChats, onUpdate }: BotInstanceSettingsProps) {
  const [contextVal, setContextVal] = useState(String(bot.context_message_count ?? 0));
  const [saving, setSaving] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  async function saveSettings(patch: { answer_owner_messages?: boolean; context_message_count?: number; response_chat_jid?: string | null }) {
    setSaving(true);
    try {
      await updateBotSettings(bot.name, bot.chat_jid, patch);
      onUpdate(bot.name, bot.chat_jid, patch);
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
            .filter((c) => c.chat_jid !== bot.chat_jid)
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

/* ---- Start Bot Panel ---- */

interface StartBotPanelProps {
  botName: string;
  existingJids: string[];
  onStarted: (chatJid: string) => void;
}

function StartBotPanel({ botName, existingJids, onStarted }: StartBotPanelProps) {
  const [chats, setChats] = useState<ChatRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJid, setSelectedJid] = useState('');
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const params = new URLSearchParams({ per_page: '200', page: '1', sort: 'chat_name', order: 'asc' });
        const data = await fetchChats(params);
        const list = Array.isArray(data) ? data : (data.chats ?? []);
        setChats(list.filter((c) => !existingJids.includes(c.chat_jid)));
      } catch {
        /* silently fail */
      } finally {
        setLoading(false);
      }
    })();
  }, [existingJids]);

  async function handleStart() {
    if (!selectedJid) return;
    setStarting(true);
    try {
      await apiStartBot(botName, selectedJid);
      const chat = chats.find((c) => c.chat_jid === selectedJid);
      toast(`Started in ${chat?.chat_name || selectedJid.split('@')[0]}`, 'success');
      onStarted(selectedJid);
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Failed to start bot', 'error');
    } finally {
      setStarting(false);
    }
  }

  if (loading) {
    return (
      <p className="muted" style={{ fontSize: '0.8rem', padding: '0.25rem 0', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
        <Loader2 size={12} className="spin" /> Loading chats…
      </p>
    );
  }

  if (chats.length === 0) {
    return (
      <p className="muted" style={{ fontSize: '0.8rem', padding: '0.25rem 0' }}>
        All available chats already have this bot running.
      </p>
    );
  }

  return (
    <div className="start-bot-section">
      <select
        className="chat-selector"
        value={selectedJid}
        onChange={(e) => setSelectedJid(e.target.value)}
        aria-label="Select chat to start bot in"
      >
        <option value="">— Select a chat —</option>
        {chats.map((c) => (
          <option key={c.chat_jid} value={c.chat_jid}>
            {c.chat_name || c.chat_jid.split('@')[0]}
          </option>
        ))}
      </select>
      <button
        type="button"
        className="btn primary btn-sm"
        disabled={!selectedJid || starting}
        onClick={handleStart}
      >
        {starting ? 'Starting…' : 'Start'}
      </button>
    </div>
  );
}

/* ---- Main Bots Page ---- */

export function Bots() {
  const [types, setTypes] = useState<BotType[]>([]);
  const [running, setRunning] = useState<BotInfo[]>([]);
  const [allChats, setAllChats] = useState<ChatRow[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [togglingKey, setTogglingKey] = useState<string | null>(null);
  const [showStartPanel, setShowStartPanel] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);

  const [logsTarget, setLogsTarget] = useState<{ botName: string; displayName: string; chatJid: string } | null>(null);
  const [messagesTarget, setMessagesTarget] = useState<{ chatJid: string; chatName: string } | null>(null);

  const load = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const chatParams = new URLSearchParams({ per_page: '500', page: '1', sort: 'chat_name', order: 'asc' });
      const [t, r, chatData] = await Promise.all([fetchBotTypes(), fetchRunningBots(), fetchChats(chatParams)]);
      setTypes(t);
      setRunning(r);
      const chatList = Array.isArray(chatData) ? chatData : ((chatData as ChatsListResponse).chats ?? []);
      setAllChats(chatList);
      setErr(null);
      setLastRefreshed(new Date());
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load bots');
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

  function toggleExpand(name: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name); else next.add(name);
      return next;
    });
  }

  function toggleStartPanel(name: string) {
    setShowStartPanel((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name); else next.add(name);
      return next;
    });
  }

  function instancesOf(name: string) {
    return running.filter((b) => b.name === name);
  }

  async function handleStop(botName: string, chatJid: string) {
    const key = `${botName}:${chatJid}`;
    setTogglingKey(key);
    try {
      await apiStopBot(botName, chatJid);
      setRunning((prev) => prev.filter((b) => !(b.name === botName && b.chat_jid === chatJid)));
      toast(`Stopped in ${chatJid.split('@')[0]}`, 'success');
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Failed to stop bot', 'error');
    } finally {
      setTogglingKey(null);
    }
  }

  async function handleStart(botName: string, chatJid: string) {
    const key = `${botName}:${chatJid}`;
    setTogglingKey(key);
    try {
      await apiStartBot(botName, chatJid);
      toast(`Started in ${chatJid.split('@')[0]}`, 'success');
      load();
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Failed to start bot', 'error');
    } finally {
      setTogglingKey(null);
    }
  }

  function handleBotStarted(_botName: string, _chatJid: string) {
    load();
    setShowStartPanel((prev) => { const n = new Set(prev); n.delete(_botName); return n; });
  }

  function handleInstanceUpdate(botName: string, chatJid: string, updates: Partial<BotInfo>) {
    setRunning((prev) => prev.map((b) =>
      b.name === botName && b.chat_jid === chatJid ? { ...b, ...updates } : b,
    ));
  }

  const filteredTypes = search.trim()
    ? types.filter((t) =>
        t.display_name.toLowerCase().includes(search.toLowerCase()) ||
        t.name.toLowerCase().includes(search.toLowerCase()) ||
        t.description.toLowerCase().includes(search.toLowerCase()),
      )
    : types;

  const totalRunning = running.length;

  if (loading) return <p className="muted">Loading bots…</p>;

  if (err) {
    return (
      <div className="panel error-panel">
        <p>{err}</p>
      </div>
    );
  }

  if (types.length === 0) {
    return (
      <div className="empty-state">
        <p>No bot types discovered. Make sure bot files exist in the <code>bots/</code> directory.</p>
      </div>
    );
  }

  return (
    <div className="bots-page">
      <div className="page-header">
        <h2>Bots</h2>
        <span className="muted">
          {types.length} type{types.length !== 1 ? 's' : ''} · {totalRunning} running
        </span>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {lastRefreshed && (
            <span className="refresh-indicator">{lastRefreshed.toLocaleTimeString()}</span>
          )}
          <button
            type="button"
            className="btn secondary btn-sm"
            onClick={() => load(true)}
            disabled={refreshing}
          >
            <RefreshCw size={13} className={refreshing ? 'spin' : ''} />
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      </div>

      <div className="search-bar" style={{ marginBottom: '1rem' }}>
        <Search size={16} className="search-icon" />
        <input
          type="text"
          placeholder="Search bot types…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="search-input"
        />
        {search && (
          <button type="button" className="search-clear" onClick={() => setSearch('')} aria-label="Clear search">
            <X size={14} />
          </button>
        )}
      </div>

      {filteredTypes.length === 0 && search && (
        <p className="muted">No bots match "<em>{search}</em>"</p>
      )}

      <div className="bot-types-grid">
        {filteredTypes.map((bt) => {
          const instances = instancesOf(bt.name);
          const isExpanded = expanded.has(bt.name);
          const isStartPanelOpen = showStartPanel.has(bt.name);

          return (
            <div key={bt.name} className={`bot-type-card ${instances.length > 0 ? 'bot-type-has-instances' : ''}`}>
              <div className="bot-type-header" onClick={() => toggleExpand(bt.name)}>
                <div className="bot-type-title">
                  <Bot size={18} className="bot-type-icon" />
                  <span className="bot-type-name">{bt.display_name}</span>
                  <span className="prefix-badge">{bt.prefix}</span>
                </div>
                <div className="bot-type-meta">
                  {instances.length > 0 ? (
                    <span className="instance-count has-instances">
                      {instances.length} running
                    </span>
                  ) : (
                    <span className="instance-count">not running</span>
                  )}
                  {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>
              </div>

              <p className="bot-type-description">{bt.description}</p>

              {isExpanded && (
                <div className="bot-type-expanded">
                  {bt.system_prompt && (
                    <div className="prompt-section">
                      <div className="prompt-header">
                        <h4 className="prompt-label">System Prompt</h4>
                        <CopyButton text={bt.system_prompt} />
                      </div>
                      <pre className="prompt-block">{bt.system_prompt}</pre>
                    </div>
                  )}

                  {instances.length > 0 && (
                    <div className="instances-section">
                      <h4 className="instances-label">
                        Running Instances ({instances.length})
                      </h4>
                      <ul className="instances-list">
                        {instances.map((inst) => {
                          const key = `${inst.name}:${inst.chat_jid}`;
                          const chatLabel = inst.chat_jid.split('@')[0];
                          const isRunning = inst.status === 'running';
                          return (
                            <li key={key} className="instance-item">
                              <div className="instance-row">
                                <div className="instance-info">
                                  <span className="instance-chat">{chatLabel}</span>
                                  <StatusBadge status={inst.status} />
                                  {inst.uptime_seconds != null && (
                                    <span className="instance-uptime">{formatUptime(inst.uptime_seconds)}</span>
                                  )}
                                </div>
                                <div className="instance-actions">
                                  <button
                                    type="button"
                                    className="btn-icon"
                                    title="View messages"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setMessagesTarget({ chatJid: inst.chat_jid, chatName: chatLabel });
                                    }}
                                    aria-label="View messages"
                                  >
                                    <MessageSquare size={13} />
                                  </button>
                                  <button
                                    type="button"
                                    className="btn-icon"
                                    title="View logs"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setLogsTarget({ botName: inst.name, displayName: bt.display_name, chatJid: inst.chat_jid });
                                    }}
                                    aria-label="View bot logs"
                                  >
                                    <ScrollText size={13} />
                                  </button>
                                  {isRunning ? (
                                    <button
                                      type="button"
                                      className="btn-icon btn-stop"
                                      disabled={togglingKey === key}
                                      onClick={(e) => { e.stopPropagation(); handleStop(inst.name, inst.chat_jid); }}
                                      aria-label="Stop bot"
                                      title="Stop bot"
                                    >
                                      {togglingKey === key
                                        ? <Loader2 size={13} className="spin" />
                                        : <ZapOff size={13} />}
                                    </button>
                                  ) : (
                                    <button
                                      type="button"
                                      className="btn-icon btn-start"
                                      disabled={togglingKey === key}
                                      onClick={(e) => { e.stopPropagation(); handleStart(inst.name, inst.chat_jid); }}
                                      aria-label="Start bot"
                                      title="Start bot"
                                    >
                                      {togglingKey === key
                                        ? <Loader2 size={13} className="spin" />
                                        : <Zap size={13} />}
                                    </button>
                                  )}
                                </div>
                              </div>
                              <BotInstanceSettings
                                bot={inst}
                                allChats={allChats}
                                onUpdate={handleInstanceUpdate}
                              />
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  )}

                  <div className="start-bot-panel">
                    <button
                      type="button"
                      className="btn secondary btn-sm"
                      onClick={(e) => { e.stopPropagation(); toggleStartPanel(bt.name); }}
                    >
                      {isStartPanelOpen ? (
                        <><ChevronUp size={13} /> Cancel</>
                      ) : (
                        <><PlayCircle size={13} /> Start in a chat…</>
                      )}
                    </button>
                    {isStartPanelOpen && (
                      <StartBotPanel
                        botName={bt.name}
                        existingJids={instances.map((i) => i.chat_jid)}
                        onStarted={(jid) => handleBotStarted(bt.name, jid)}
                      />
                    )}
                  </div>

                  {instances.length === 0 && !isStartPanelOpen && (
                    <p className="muted instances-empty">
                      <Zap size={14} /> Not running in any chat.
                    </p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

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
    </div>
  );
}
