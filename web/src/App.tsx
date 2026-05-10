import { Route, Routes } from 'react-router-dom';

import { AppShell } from '@/components/AppShell';
import { RequireAuth } from '@/components/RequireAuth';
import { BotsPage } from '@/pages/Bots';
import { ChatDetailPage, ChatsPage } from '@/pages/Chats';
import { DashboardPage } from '@/pages/Dashboard';
import { DiagnosticsPage } from '@/pages/Diagnostics';
import { LoginPage } from '@/pages/Login';
import { NotFoundPage } from '@/pages/NotFound';
import { SettingsPage } from '@/pages/Settings';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="chats" element={<ChatsPage />} />
        <Route path="chats/:chatJid" element={<ChatDetailPage />} />
        <Route path="bots" element={<BotsPage />} />
        <Route path="diagnostics" element={<DiagnosticsPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
