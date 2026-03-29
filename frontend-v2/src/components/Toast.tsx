import { useEffect, useState, useCallback } from 'react';
import { X } from 'lucide-react';
import { type ToastItem, dismissToast, subscribe } from './toastStore';

export function ToastContainer() {
  const [items, setItems] = useState<ToastItem[]>([]);

  useEffect(() => subscribe(setItems), []);

  const dismiss = useCallback((id: number) => dismissToast(id), []);

  if (items.length === 0) return null;

  return (
    <div className="toast-container">
      {items.map((t) => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          <span>{t.message}</span>
          <button type="button" className="toast-close" onClick={() => dismiss(t.id)} aria-label="Dismiss">
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}
