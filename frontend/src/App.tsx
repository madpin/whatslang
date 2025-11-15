import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { queryClient } from '@/lib/queryClient'
import ErrorBoundary from '@/components/ErrorBoundary'
import AppLayout from '@/components/layout/AppLayout'
import Dashboard from '@/pages/Dashboard'
import Bots from '@/pages/Bots'
import BotForm from '@/pages/BotForm'
import Chats from '@/pages/Chats'
import ChatDetail from '@/pages/ChatDetail'
import Schedules from '@/pages/Schedules'
import Messages from '@/pages/Messages'
import BotAttribution from '@/pages/BotAttribution'

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <Router>
          <AppLayout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/bots" element={<Bots />} />
              <Route path="/bots/new" element={<BotForm />} />
              <Route path="/bots/:id/edit" element={<BotForm />} />
              <Route path="/chats" element={<Chats />} />
              <Route path="/chats/:id" element={<ChatDetail />} />
              <Route path="/schedules" element={<Schedules />} />
              <Route path="/messages" element={<Messages />} />
              <Route path="/bot-attribution" element={<BotAttribution />} />
            </Routes>
          </AppLayout>
        </Router>
        <Toaster position="top-right" richColors />
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App

