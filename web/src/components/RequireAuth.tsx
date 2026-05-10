import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { FullPageSpinner } from '@/components/Spinner';

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { loading, status } = useAuth();
  const location = useLocation();

  if (loading) {
    return <FullPageSpinner label="Loading…" />;
  }
  if (status?.auth_required && !status.user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <>{children}</>;
}
