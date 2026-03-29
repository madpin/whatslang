export type ToastItem = {
  id: number;
  message: string;
  type: 'success' | 'error';
};

let nextId = 0;

type Listener = (toasts: ToastItem[]) => void;
let toasts: ToastItem[] = [];
const listeners: Set<Listener> = new Set();

function emit() {
  listeners.forEach((fn) => fn([...toasts]));
}

export function toast(message: string, type: 'success' | 'error' = 'success') {
  const id = ++nextId;
  toasts = [...toasts, { id, message, type }];
  emit();
  setTimeout(() => {
    toasts = toasts.filter((t) => t.id !== id);
    emit();
  }, 4000);
}

export function dismissToast(id: number) {
  toasts = toasts.filter((t) => t.id !== id);
  emit();
}

export function subscribe(fn: Listener) {
  listeners.add(fn);
  return () => { listeners.delete(fn); };
}
