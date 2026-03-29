import { useEffect, useState, useCallback } from 'react';
import { RefreshCw, AlertCircle } from 'lucide-react';
import { fetchChatMessages, type ChatMessage } from '../api/client';
import { Modal } from './Modal';

interface MessagesModalProps {
  isOpen: boolean;
  onClose: () => void;
  chatJid: string;
  chatName: string;
}

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

function getMessageText(msg: ChatMessage): string {
  return msg.text ?? msg.body ?? '[media or unsupported message]';
}

export function MessagesModal({ isOpen, onClose, chatJid, chatName }: MessagesModalProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!isOpen) return;
    setLoading(true);
    setErr(null);
    try {
      const msgs = await fetchChatMessages(chatJid, 30);
      setMessages(msgs);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load messages');
    } finally {
      setLoading(false);
    }
  }, [isOpen, chatJid]);

  useEffect(() => {
    if (isOpen) load();
  }, [isOpen, load]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Recent messages — ${chatName}`}
      size="md"
      footer={
        <div className="modal-footer-row">
          <span className="muted" style={{ fontSize: '0.75rem' }}>Last 30 messages</span>
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
      ) : loading && messages.length === 0 ? (
        <p className="muted">Loading messages…</p>
      ) : messages.length === 0 ? (
        <p className="muted">No messages found for this chat.</p>
      ) : (
        <div className="messages-list">
          {messages.map((msg, i) => {
            const isMe = msg.from_me === true;
            return (
              <div key={i} className={`message-bubble ${isMe ? 'message-me' : 'message-them'}`}>
                {!isMe && msg.sender && (
                  <div className="message-sender">{msg.sender}</div>
                )}
                <div className="message-text">{getMessageText(msg)}</div>
                {msg.timestamp && (
                  <div className="message-time">{formatMsgTime(msg.timestamp)}</div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </Modal>
  );
}
