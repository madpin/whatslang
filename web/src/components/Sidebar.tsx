import { NavLink } from 'react-router-dom';
import {
  Activity,
  Bot,
  LayoutDashboard,
  MessagesSquare,
  Settings,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
}

const NAV: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/chats', label: 'Chats', icon: MessagesSquare },
  { to: '/bots', label: 'Bots', icon: Bot },
  { to: '/diagnostics', label: 'Diagnostics', icon: Activity },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar({
  collapsed,
  onClose,
}: {
  collapsed: boolean;
  onClose?: () => void;
}) {
  return (
    <aside
      className={cn(
        'flex h-full flex-col border-r border-zinc-200 bg-white transition-all duration-200 dark:border-zinc-800 dark:bg-zinc-950',
        collapsed ? 'w-16' : 'w-60',
      )}
    >
      <div className="flex h-16 items-center gap-2 border-b border-zinc-200 px-4 dark:border-zinc-800">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-sm">
          <span className="text-sm font-bold tracking-tight">W</span>
        </div>
        {!collapsed && (
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
              Whatslang
            </span>
            <span className="text-[10px] uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Bot Console
            </span>
          </div>
        )}
      </div>
      <nav className="flex-1 space-y-1 px-2 py-4">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onClose}
            className={({ isActive }) =>
              cn(
                'group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300'
                  : 'text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800 dark:hover:text-zinc-100',
                collapsed && 'justify-center',
              )
            }
            title={collapsed ? label : undefined}
          >
            <Icon size={18} className="shrink-0" />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-zinc-200 px-3 py-3 text-[11px] text-zinc-400 dark:border-zinc-800">
        {!collapsed && (
          <p className="truncate">
            v3.0 ·{' '}
            <span className="text-zinc-500 dark:text-zinc-400">
              built for sleek admin
            </span>
          </p>
        )}
      </div>
    </aside>
  );
}
