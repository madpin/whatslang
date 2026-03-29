interface StatusBadgeProps {
  status: 'running' | 'stopped' | string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const isRunning = status === 'running';
  return (
    <span className={`status-badge ${isRunning ? 'status-running' : 'status-stopped'}`}>
      <span className="status-dot" />
      {status}
    </span>
  );
}
