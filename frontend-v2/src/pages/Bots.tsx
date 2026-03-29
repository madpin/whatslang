import { useEffect, useState } from 'react';
import { ChevronDown, ChevronRight, Bot, Zap, ZapOff } from 'lucide-react';
import { fetchBotTypes, fetchRunningBots, stopBot as apiStopBot, type BotType, type BotInfo } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { toast } from '../components/toastStore';

export function Bots() {
  const [types, setTypes] = useState<BotType[]>([]);
  const [running, setRunning] = useState<BotInfo[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [togglingKey, setTogglingKey] = useState<string | null>(null);

  async function load() {
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
  }

  useEffect(() => {
    load();
  }, []);

  function toggleExpand(name: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
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

  if (loading) return <p className="muted">Loading bots...</p>;

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
        <h2>Bot Types</h2>
        <span className="muted">{types.length} type{types.length !== 1 ? 's' : ''} available</span>
      </div>
      <div className="bot-types-grid">
        {types.map((bt) => {
          const instances = instancesOf(bt.name);
          const isExpanded = expanded.has(bt.name);
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
                  {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
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
                      <h4 className="instances-label">Running Instances</h4>
                      <ul className="instances-list">
                        {instances.map((inst) => (
                          <li key={`${inst.name}-${inst.chat_jid}`} className="instance-row">
                            <div className="instance-info">
                              <span className="instance-chat">{inst.chat_jid.split('@')[0]}</span>
                              <StatusBadge status={inst.status} />
                              {inst.uptime_seconds != null && (
                                <span className="instance-uptime">{formatUptime(inst.uptime_seconds)}</span>
                              )}
                            </div>
                            <button
                              type="button"
                              className="btn-icon btn-stop"
                              disabled={togglingKey === `${inst.name}:${inst.chat_jid}`}
                              onClick={(e) => { e.stopPropagation(); handleStop(inst.name, inst.chat_jid); }}
                              aria-label="Stop bot"
                            >
                              <ZapOff size={14} />
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {instances.length === 0 && (
                    <p className="muted instances-empty">
                      <Zap size={14} /> Not running in any chat. Start it from the Chats page.
                    </p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
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
