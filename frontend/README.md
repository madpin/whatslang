# WhatSlang Frontend

Modern React frontend for the WhatSlang WhatsApp bot platform.

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and optimized builds
- **Tailwind CSS** for styling
- **shadcn/ui** for beautiful UI components
- **React Router** for navigation
- **TanStack Query** for data fetching with real-time polling
- **React Hook Form** + **Zod** for form validation
- **Axios** for API communication
- **date-fns** for date formatting
- **cronstrue** for cron expression parsing
- **Sonner** for toast notifications

## Features

- 📊 **Dashboard** - Overview with stats, recent activity, and quick actions
- 🤖 **Bot Management** - Create, edit, and manage bot instances with dynamic forms
- 💬 **Chat Management** - Register chats and assign bots with priority ordering
- ⏰ **Message Scheduling** - Schedule one-time or recurring messages with cron
- 📧 **Message History** - View processed messages with real-time updates
- 🔄 **Live Updates** - Automatic polling for real-time data
- 🎨 **Beautiful UI** - Modern, responsive design with dark mode support
- ✅ **Form Validation** - Real-time validation with helpful error messages
- 🔔 **Notifications** - Toast notifications for all actions
- 💀 **Loading States** - Skeleton loaders for better UX

## Development Setup

### Prerequisites

- Node.js 18+ and npm
- Backend API running (see backend README)

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with your API URL (default: http://localhost:8000)
# VITE_API_BASE_URL=http://localhost:8000
```

### Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

Output will be in the `dist` directory.

### Preview Production Build

```bash
npm run preview
```

## Docker Deployment

### Using Docker Compose (Recommended)

From the project root:

```bash
docker-compose up -d
```

Frontend will be available at `http://localhost:3000`

### Build Docker Image

```bash
docker build -t whatslang-frontend .
```

### Run Docker Container

```bash
docker run -p 3000:80 whatslang-frontend
```

## Environment Variables

Create a `.env` file with:

```env
VITE_API_BASE_URL=http://localhost:8000
```

For production, set this to your backend API URL.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # shadcn/ui components
│   │   ├── layout/          # Layout components
│   │   ├── bots/            # Bot-specific components
│   │   ├── chats/           # Chat-specific components
│   │   ├── schedules/       # Schedule-specific components
│   │   └── messages/        # Message-specific components
│   ├── pages/               # Route pages
│   │   ├── Dashboard.tsx
│   │   ├── Bots.tsx
│   │   ├── BotForm.tsx
│   │   ├── Chats.tsx
│   │   ├── ChatDetail.tsx
│   │   ├── Schedules.tsx
│   │   └── Messages.tsx
│   ├── services/            # API service layer
│   │   └── api.ts
│   ├── hooks/               # Custom React hooks
│   │   ├── useBots.ts
│   │   ├── useChats.ts
│   │   ├── useSchedules.ts
│   │   ├── useMessages.ts
│   │   └── useHealth.ts
│   ├── lib/                 # Utilities
│   │   ├── utils.ts
│   │   └── queryClient.ts
│   ├── types/               # TypeScript types
│   │   ├── bot.ts
│   │   ├── chat.ts
│   │   ├── schedule.ts
│   │   ├── message.ts
│   │   └── common.ts
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── public/                  # Static assets
├── Dockerfile              # Docker configuration
├── nginx.conf              # Nginx configuration
├── vite.config.ts          # Vite configuration
├── tailwind.config.js      # Tailwind configuration
└── package.json            # Dependencies
```

## API Integration

The frontend communicates with the backend API through:

- **API Service** (`src/services/api.ts`) - Axios instance with all API calls
- **Custom Hooks** - TanStack Query hooks for data fetching and mutations
- **Real-time Updates** - Automatic polling with configurable intervals

### Polling Intervals

- Dashboard: 10 seconds
- Messages: 5 seconds (live updates)
- Bots/Chats/Schedules: 30 seconds
- Health check: 30 seconds

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Follow the existing code style
2. Use TypeScript for type safety
3. Add loading states for async operations
4. Show success/error toasts for user actions
5. Implement proper error handling
6. Make components responsive

## License

MIT

