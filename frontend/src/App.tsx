import React, { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/useAuthStore'

// Layouts
import { MainLayout, AuthLayout, DashboardLayout } from '@/layouts'

// Auth Pages
import { Login, Register, RoleSelection } from '@/pages/auth'

// Common Pages
import { NotFound, ErrorPage, Chat } from '@/pages/common'

// Employee Pages
import { EmployeeDashboard } from '@/pages/employee/Dashboard'
import { JobSearch } from '@/pages/employee/JobSearch'
import { Applications } from '@/pages/employee/Applications'
import { Interviews } from '@/pages/employee/Interviews'
import { Profile } from '@/pages/employee/Profile'
import { OnboardingProgress } from '@/pages/employee/OnboardingProgress'
import { Offers } from '@/pages/employee/Offers'

// Employer Pages
import { EmployerDashboard } from '@/pages/employer/Dashboard'
import { Jobs } from '@/pages/employer/Jobs'
import { Candidates } from '@/pages/employer/Candidates'
import { Analytics } from '@/pages/employer/Analytics'
import { Interviews as EmployerInterviews } from '@/pages/employer/Interviews'
import { EmployerOnboarding } from '@/pages/employer/Onboarding'

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode; allowedRole?: 'employee' | 'employer' }> = ({ children, allowedRole }) => {
  const { isAuthenticated, user } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" replace />
  }

  if (allowedRole && user?.role !== allowedRole) {
    // Redirect to appropriate dashboard if role doesn't match
    const redirectPath = user?.role === 'employer' ? '/employer/dashboard' : '/employee/dashboard'
    return <Navigate to={redirectPath} replace />
  }

  return <>{children}</>
}

// Root Redirect Component - uses hooks properly to avoid issues on page reload
const RootRedirect = () => {
  const { isAuthenticated, user } = useAuthStore()

  if (isAuthenticated && user) {
    const dashboardPath = user.role === 'employer' ? '/employer/dashboard' : '/employee/dashboard'
    return <Navigate to={dashboardPath} replace />
  }

  return <Navigate to="/auth/role" replace />
}

function App() {
  const { initializeAuth } = useAuthStore()

  // Initialize auth state from localStorage on app mount
  useEffect(() => {
    initializeAuth()
  }, [initializeAuth])

  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />

      {/* Auth Routes */}
      <Route element={<AuthLayout><MainLayout /></AuthLayout>}>
        <Route path="/auth/role" element={<RoleSelection />} />
        <Route path="/auth/login" element={<Login />} />
        <Route path="/auth/register" element={<Register />} />
      </Route>

      {/* Employee Routes */}
      <Route
        path="/employee/*"
        element={
          <ProtectedRoute allowedRole="employee">
            <DashboardLayout>
              <Routes>
                <Route path="dashboard" element={<EmployeeDashboard />} />
                <Route path="jobs" element={<JobSearch />} />
                <Route path="applications" element={<Applications />} />
                <Route path="interviews" element={<Interviews />} />
                <Route path="profile" element={<Profile />} />
                <Route path="onboarding" element={<OnboardingProgress />} />
                <Route path="offers" element={<Offers />} />
                <Route path="chat" element={<Chat />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      {/* Employer Routes */}
      <Route
        path="/employer/*"
        element={
          <ProtectedRoute allowedRole="employer">
            <DashboardLayout>
              <Routes>
                <Route path="dashboard" element={<EmployerDashboard />} />
                <Route path="jobs" element={<Jobs />} />
                <Route path="candidates" element={<Candidates />} />
                <Route path="analytics" element={<Analytics />} />
                <Route path="interviews" element={<EmployerInterviews />} />
                <Route path="onboarding" element={<EmployerOnboarding />} />
                <Route path="chat" element={<Chat />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      {/* Error Pages */}
      <Route path="/error" element={<ErrorPage />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default App
