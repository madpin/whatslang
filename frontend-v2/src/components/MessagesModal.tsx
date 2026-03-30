import { useEffect, useState, useCallback, useRef } from 'react';
import { RefreshCw, AlertCircle, Search, X, Image, Video, Mic, FileText, ArrowDown } from 'lucide-react';
import { fetchChatMessages, messageText, messageIsMe, isMediaMessage, type ChatMessage } from '../api/client';
import { Modal } from './Modal';

interface MessagesModalProps {
  isOpen: boolean;
  onClose: () => void;
  chatJid: string;
  chatName: string;
}

const LIMIT_OPTIONS = [30, 50, 100, 200];

function formatMsgTime(ts: string | number | undefined): string {
  if (!ts) return '';
  try {
    const d = typeof ts === 'number' ? new Date(ts * 1000) : new Date(ts);
    return d.toLocaleString('en-US', {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit', hour12: false,
    });
  } catch {
    return '';
  }
}

function MediaBadge({ msg }: { msg: ChatMessage }) {
  const type = msg.media_type ?? msg.mimetype?.split('/')[0] ?? msg.type ?? '';
  if (!type || ['text', 'conversation', 'extendedTextMessage'].includes(type)) return null;

  const icons: Record<string, React.ReactNode> = {
    image: <Image size={11} />,
    video: <Video size={11} />,
    audio: <Mic size={11} />,
    document: <FileText size={11} />,
    ptt: <Mic size={11} />,
  };

  const icon = icons[type] ?? <FileText size={11} />;
  return (
    <span className="media-badge">
      {icon} {type}
    </span>
  );
}

export function MessagesModal({ isOpen, onClose, chatJid, chatName }: MessagesModalProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [limit, setLimit] = useState(50);
  const [msgSearch, setMsgSearch] = useState('');
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async (l?: number) => {
    if (!isOpen) return;
    setLoading(true);
    setErr(null);
    try {
      const msgs = await fetchChatMessages(chatJid, l ?? limit);
      setMessages(msgs);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load messages');
    } finally {
      setLoading(false);
    }
  }, [isOpen, chatJid, limit]);

  useEffect(() => {
    if (isOpen) load();
  }, [isOpen, load]);

  function handleLimitChange(newLimit: number) {
    setLimit(newLimit);
    load(newLimit);
  }

  function scrollToBottom() {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }

  function handleScroll() {
    const el = listRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
    setShowScrollBtn(!atBottom);
  }

  // Scroll to bottom on new messages
  useEffect(() => {
    if (messages.length > 0 && !loading) {
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'instant' }), 50);
    }
  }, [messages, loading]);

  const filteredMessages = msgSearch.trim()
    ? messages.filter((m) => {
        const text = messageText(m).toLowerCase();
        const sender = (m.sender ?? m.from ?? '').toLowerCase();
        return text.includes(msgSearch.toLowerCase()) || sender.includes(msgSearch.toLowerCase());
      })
    : messages;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Messages — ${chatName}`}
      size="md"
      footer={
        <div className="modal-footer-row">
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span className="muted" style={{ fontSize: '0.73rem' }}>Show</span>
            <div className="limit-picker">
              {LIMIT_OPTIONS.map((l) => (
                <button
                  key={l}
                  type="button"
                  className={`limit-option ${limit === l ? 'limit-option-active' : ''}`}
                  onClick={() => handleLimitChange(l)}
                  disabled={loading}
                >
                  {l}
                </button>
              ))}
            </div>
            <span className="muted" style={{ fontSize: '0.73rem' }}>messages</span>
          </div>
          <button type="button" className="btn secondary btn-sm" onClick={() => load()} disabled={loading}>
            <RefreshCw size={13} className={loading ? 'spin' : ''} />
            {loading ? 'Loading…' : 'Refresh'}
          </button>
        </div>
      }
    >
      {/* Search bar */}
      <div className="msg-search-bar">
        <Search size={14} className="msg-search-icon" />
        <input
          type="text"
          className="msg-search-input"
          placeholder="Search messages…"
          value={msgSearch}
          onChange={(e) => setMsgSearch(e.target.value)}
        />
        {msgSearch && (
          <button type="button" className="search-clear" onClick={() => setMsgSearch('')} aria-label="Clear search">
            <X size={13} />
          </button>
        )}
      </div>

      {msgSearch && filteredMessages.length !== messages.length && (
        <div className="msg-search-info">
          {filteredMessages.length} of {messages.length} messages match
        </div>
      )}

      {err ? (
        <div className="logs-error">
          <AlertCircle size={16} />
          <span>{err}</span>
        </div>
      ) : loading && messages.length === 0 ? (
        <p className="muted">Loading messages…</p>
      ) : filteredMessages.length === 0 ? (
        <p className="muted">
          {msgSearch ? 'No messages match your search.' : 'No messages found for this chat.'}
        </p>
      ) : (
        <div
          className="messages-list"
          ref={listRef}
          onScroll={handleScroll}
          style={{ position: 'relative' }}
        >
          {filteredMessages.map((msg, i) => {
            const isMe = messageIsMe(msg);
            const text = messageText(msg);
            const isMedia = isMediaMessage(msg);
            const sender = msg.sender ?? msg.from ?? msg.sender_jid;
            return (
              <div key={msg.id ?? i} className={`message-bubble ${isMe ? 'message-me' : 'message-them'}`}>
                {!isMe && sender && (
                  <div className="message-sender">{sender.split('@')[0]}</div>
                )}
                {isMedia && <MediaBadge msg={msg} />}
                <div className={`message-text ${isMedia && !text.startsWith('[') ? 'message-text-media' : ''}`}>
                  {text}
                </div>
                {msg.timestamp && (
                  <div className="message-time">{formatMsgTime(msg.timestamp)}</div>
                )}
              </div>
            );
          })}
          <div ref={bottomRef} />
        </div>
      )}

      {showScrollBtn && (
        <button
          type="button"
          className="scroll-to-bottom"
          onClick={scrollToBottom}
          aria-label="Scroll to latest"
          title="Scroll to latest messages"
        >
          <ArrowDown size={14} />
        </button>
      )}
    </Modal>
  );
}
