# SmartServe Frontend

Modern, clean, and responsive frontend for SmartServe AI-Powered Recruitment Platform.

## 🎨 Tech Stack

- **React 18** - UI Library
- **TypeScript** - Type Safety
- **Vite** - Build Tool & Dev Server
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **Zustand** - State Management
- **React Router** - Routing
- **Axios** - HTTP Client
- **React Hook Form + Zod** - Form Management & Validation
- **Lucide React** - Icons
- **Recharts** - Data Visualization
- **Sonner** - Toast Notifications

## 📦 Installation

```powershell
# Install dependencies
npm install

# Create environment file
Copy-Item .env.example .env.local

# Edit .env.local with your configuration
```

## 🚀 Development

```powershell
# Start development server (http://localhost:3000)
npm run dev

# Type checking
npm run type-check

# Lint code
npm run lint

# Format code
npm run format

# Run tests
npm run test
```

## 🏗️ Build

```powershell
# Build for production
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
src/
├── components/     # Reusable UI components
├── pages/          # Page components
├── services/       # API & WebSocket services
├── stores/         # Zustand state stores
├── types/          # TypeScript type definitions
├── utils/          # Utility functions
├── hooks/          # Custom React hooks
├── layouts/        # Layout components
├── App.tsx         # Main app component
├── main.tsx        # Entry point
└── index.css       # Global styles
```

## 🎯 Key Features

### ✅ Completed
- ✅ Project scaffolding with Vite + TypeScript
- ✅ Tailwind CSS configuration with custom theme
- ✅ API client service with Axios
- ✅ Authentication store with Zustand
- ✅ Reusable Button component
- ✅ Reusable Input component
- ✅ TypeScript types for all entities

### ⏳ In Progress
- ⏳ Layout components (Navbar, Sidebar, Footer)
- ⏳ Authentication pages (Login, Register, Role Selection)
- ⏳ Dashboard pages (Employer & Employee)
- ⏳ Job management pages
- ⏳ Chat interface with AI assistant
- ⏳ Real-time notifications via WebSocket
- ⏳ Application tracking
- ⏳ Interview management

## 🔧 Configuration

### Environment Variables

Create `.env.local` file in the frontend root:

```env
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8001
VITE_APP_NAME=SmartServe
```

### API Integration

The frontend connects to the backend API at `http://localhost:8000/api`. Make sure the backend is running before starting the frontend.

```powershell
# In the project root, start backend:
cd C:\manpower_connector
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## 🎨 Design System

### Colors

- **Primary**: Blue tones (#0ea5e9)
- **Secondary**: Purple tones (#a855f7)
- **Accent**: Violet tones (#8b5cf6)
- **Success**: Green tones (#22c55e)
- **Danger**: Red tones (#ef4444)

### Typography

- **Font**: Inter (Google Fonts)
- **Sizes**: sm, base, lg, xl, 2xl

### Components

All components follow a consistent API:
- Props for variants, sizes, and states
- Framer Motion animations for smooth UX
- Full TypeScript support
- Accessibility features built-in

## 🧪 Testing

```powershell
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage
```

## 📚 Component Usage

### Button

```tsx
import { Button } from '@components/Button'

<Button variant="primary" size="md">
  Click Me
</Button>

<Button variant="danger" isLoading>
  Submitting...
</Button>
```

### Input

```tsx
import { Input } from '@components/Input'

<Input
  label="Email"
  type="email"
  placeholder="your@email.com"
  error={errors.email?.message}
/>
```

## 🔄 State Management

Using Zustand for lightweight, fast state management:

```tsx
import { useAuthStore } from '@stores/useAuthStore'

const { user, login, logout } = useAuthStore()
```

## 📡 API Calls

```tsx
import { apiClient } from '@services/api'

// Login
await apiClient.login({ email, password })

// Get jobs
const jobs = await apiClient.getJobs()

// Create application
await apiClient.createApplication({ job_id, cover_letter })
```

## 🚀 Deployment

### Build for Production

```powershell
npm run build
```

The build output will be in the `dist/` directory.

### Deploy to Vercel

```powershell
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Deploy to Netlify

```powershell
# Install Netlify CLI
npm i -g netlify-cli

# Deploy
netlify deploy --prod
```

## 🐛 Troubleshooting

### API Connection Issues

1. Check backend is running on port 8000
2. Verify `VITE_API_URL` in `.env.local`
3. Check CORS settings in backend

### Build Errors

```powershell
# Clear cache and reinstall
Remove-Item -Recurse -Force node_modules
npm install

# Clear Vite cache
npm run dev -- --force
```

### TypeScript Errors

```powershell
# Run type checker
npm run type-check

# Check tsconfig.json paths
```

## 📖 Documentation

- [Vite Documentation](https://vitejs.dev/)
- [React Documentation](https://react.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [Framer Motion Documentation](https://www.framer.com/motion/)

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Status**: Frontend scaffolding complete ✅  
**Next Steps**: Implement remaining pages and components

For detailed setup instructions, see [FRONTEND_SETUP.md](./FRONTEND_SETUP.md)
