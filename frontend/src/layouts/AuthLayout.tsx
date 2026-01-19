import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/useAuthStore'

interface AuthLayoutProps {
  children: React.ReactNode
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ children }) => {
  const { isAuthenticated, user } = useAuthStore()

  // Redirect authenticated users to their dashboard
  if (isAuthenticated && user) {
    const dashboardPath = user.role === 'employer' 
      ? '/employer/dashboard' 
      : '/employee/dashboard'
    return <Navigate to={dashboardPath} replace />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      {children}
    </div>
  )
}
