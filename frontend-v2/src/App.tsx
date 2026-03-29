import { HashRouter, Routes, Route } from 'react-router-dom';
import { AuthGate } from './auth/AuthGate';
import { Shell } from './layout/Shell';
import { Overview } from './pages/Overview';
import { Chats } from './pages/Chats';
import { Bots } from './pages/Bots';

export default function App() {
  return (
    <HashRouter>
      <AuthGate>
        <Routes>
          <Route path="/" element={<Shell />}>
            <Route index element={<Overview />} />
            <Route path="chats" element={<Chats />} />
            <Route path="bots" element={<Bots />} />
          </Route>
        </Routes>
      </AuthGate>
    </HashRouter>
  );
}
