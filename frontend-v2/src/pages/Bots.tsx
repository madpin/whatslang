import { useEffect, useState, useCallback } from 'react';
import {
  ChevronDown, Bot, Zap, ZapOff, PlayCircle,
  ScrollText, ChevronUp,
} from 'lucide-react';
import {
  fetchBotTypes, fetchRunningBots, fetchChats,
  stopBot as apiStopBot, startBot as apiStartBot,
  type BotType, type BotInfo, type ChatRow,
} from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { BotLogsModal } from '../components/BotLogsModal';
import { toast } from '../components/toastStore';

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

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
        const params = new URLSearchParams({ per_page: '100', page: '1', sort: 'chat_name', order: 'asc' });
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
      toast(`Started ${botName} in ${selectedJid.split('@')[0]}`, 'success');
      onStarted(selectedJid);
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Failed to start bot', 'error');
    } finally {
      setStarting(false);
    }
  }

  if (loading) return <p className="muted" style={{ fontSize: '0.8rem', padding: '0.25rem 0' }}>Loading chats…</p>;

  if (chats.length === 0) {
    return <p className="muted" style={{ fontSize: '0.8rem', padding: '0.25rem 0' }}>No available chats (all chats already have this bot).</p>;
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

export function Bots() {
  const [types, setTypes] = useState<BotType[]>([]);
  const [running, setRunning] = useState<BotInfo[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [togglingKey, setTogglingKey] = useState<string | null>(null);
  const [showStartPanel, setShowStartPanel] = useState<Set<string>>(new Set());

  const [logsTarget, setLogsTarget] = useState<{ botName: string; displayName: string; chatJid: string } | null>(null);

  const load = useCallback(async () => {
    try {
      const [t, r] = await Promise.all([fetchBotTypes(), fetchRunningBots()]);
      setTypes(t);
      setRunning(r);
      setErr(null);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load bots');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

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
      toast(`Stopped ${botName} in ${chatJid.split('@')[0]}`, 'success');
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Failed to stop bot', 'error');
    } finally {
      setTogglingKey(null);
    }
  }

  function handleBotStarted(_botName: string, _chatJid: string) {
    load();
    setShowStartPanel((prev) => { const n = new Set(prev); n.delete(_botName); return n; });
  }

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
          {types.length} type{types.length !== 1 ? 's' : ''} · {running.length} running
        </span>
      </div>

      <div className="bot-types-grid">
        {types.map((bt) => {
          const instances = instancesOf(bt.name);
          const isExpanded = expanded.has(bt.name);
          const isStartPanelOpen = showStartPanel.has(bt.name);

          return (
            <div key={bt.name} className="bot-type-card">
              <div className="bot-type-header" onClick={() => toggleExpand(bt.name)}>
                <div className="bot-type-title">
                  <Bot size={18} className="bot-type-icon" />
                  <span className="bot-type-name">{bt.display_name}</span>
                  <span className="prefix-badge">{bt.prefix}</span>
                </div>
                <div className="bot-type-meta">
                  <span className={`instance-count ${instances.length > 0 ? 'has-instances' : ''}`}>
                    {instances.length} running
                  </span>
                  {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>
              </div>

              <p className="bot-type-description">{bt.description}</p>

              {isExpanded && (
                <div className="bot-type-expanded">
                  {bt.system_prompt && (
                    <div className="prompt-section">
                      <h4 className="prompt-label">System Prompt</h4>
                      <pre className="prompt-block">{bt.system_prompt}</pre>
                    </div>
                  )}

                  {instances.length > 0 && (
                    <div className="instances-section">
                      <h4 className="instances-label">Running Instances ({instances.length})</h4>
                      <ul className="instances-list">
                        {instances.map((inst) => {
                          const key = `${inst.name}:${inst.chat_jid}`;
                          return (
                            <li key={key} className="instance-row">
                              <div className="instance-info">
                                <span className="instance-chat">{inst.chat_jid.split('@')[0]}</span>
                                <StatusBadge status={inst.status} />
                                {inst.uptime_seconds != null && (
                                  <span className="instance-uptime">{formatUptime(inst.uptime_seconds)}</span>
                                )}
                              </div>
                              <div className="instance-actions">
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
                                  <ScrollText size={14} />
                                </button>
                                <button
                                  type="button"
                                  className="btn-icon btn-stop"
                                  disabled={togglingKey === key}
                                  onClick={(e) => { e.stopPropagation(); handleStop(inst.name, inst.chat_jid); }}
                                  aria-label="Stop bot"
                                >
                                  <ZapOff size={14} />
                                </button>
                              </div>
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
                        <><PlayCircle size={13} /><Zap size={13} /> Start in a chat…</>
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
    </div>
  );
}
