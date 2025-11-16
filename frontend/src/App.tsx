import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { queryClient } from '@/lib/queryClient'
import { AuthProvider } from '@/contexts/AuthContext'
import ErrorBoundary from '@/components/ErrorBoundary'
import PrivateRoute from '@/components/auth/PrivateRoute'
import AppLayout from '@/components/layout/AppLayout'
import Dashboard from '@/pages/Dashboard'
import Bots from '@/pages/Bots'
import BotForm from '@/pages/BotForm'
import Chats from '@/pages/Chats'
import ChatDetail from '@/pages/ChatDetail'
import Schedules from '@/pages/Schedules'
import Messages from '@/pages/Messages'
import BotAttribution from '@/pages/BotAttribution'
import Login from '@/pages/Login'
import Register from '@/pages/Register'

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Router>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              
              {/* Protected routes */}
              <Route
                path="/*"
                element={
                  <PrivateRoute>
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
                  </PrivateRoute>
                }
              />
            </Routes>
          </Router>
          <Toaster position="top-right" richColors />
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App

