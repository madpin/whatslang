import { useEffect, useState } from 'react';
import { fetchChats, type ChatRow, type ChatsListResponse } from '../api/client';

function normalizeChats(data: ChatsListResponse | ChatRow[]): ChatRow[] {
  if (Array.isArray(data)) return data;
  return data.chats ?? [];
}

export function Chats() {
  const [chats, setChats] = useState<ChatRow[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const params = new URLSearchParams();
        params.set('per_page', '100');
        params.set('page', '1');
        const data = await fetchChats(params);
        if (!cancelled) setChats(normalizeChats(data));
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : 'Failed to load chats');
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

  if (chats.length === 0) {
    return (
      <div className="empty-state">
        <p>No chats yet. Use <strong>Sync from WhatsApp</strong> on this page or open the classic dashboard for full tools.</p>
      </div>
    );
  }

  return (
    <ul className="chat-list">
      {chats.map((c) => (
        <li key={c.chat_jid} className="chat-row">
          <div className="chat-row-main">
            <span className="chat-name">{c.chat_name}</span>
            <span className="chat-jid">{c.chat_jid}</span>
          </div>
          <div className="chat-row-meta">
            {c.bots?.length ?? 0} bot{(c.bots?.length ?? 0) !== 1 ? 's' : ''}
            {c.message_count != null ? ` · ${c.message_count} messages` : ''}
          </div>
        </li>
      ))}
    </ul>
  );
}
