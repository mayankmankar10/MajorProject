import { create } from 'zustand'
import { User } from '@/types'
import { apiClient } from '@/services/api'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  token: string | null

  // Actions
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName: string, role: string, companyName?: string) => Promise<void>
  logout: () => void
  setUser: (user: User) => void
  clearError: () => void
  checkAuth: () => Promise<void>
  initializeAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  token: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await apiClient.login({ email, password })
      // Map profile_id (from backend) to profileId (frontend convention)
      const user = {
        ...response.user,
        profileId: (response.user as any).profile_id
      }
      localStorage.setItem('auth_token', response.access_token)
      localStorage.setItem('auth_user', JSON.stringify(user))
      set({
        user,
        isAuthenticated: true,
        token: response.access_token,
        isLoading: false,
      })
    } catch (error: any) {
      const detail = error.response?.data?.detail
      let errorMessage = 'Login failed'

      if (Array.isArray(detail)) {
        // Handle validation errors (array of error objects)
        errorMessage = detail.map((err: any) => err.msg).join(', ')
      } else if (typeof detail === 'string') {
        errorMessage = detail
      }

      set({
        error: errorMessage,
        isLoading: false,
      })
      throw error
    }
  },

  register: async (
    email: string,
    password: string,
    fullName: string,
    role: string,
    companyName?: string
  ) => {
    set({ isLoading: true, error: null })
    try {
      const response = await apiClient.register({
        email,
        password,
        role: role as 'employer' | 'employee',
        full_name: fullName,
        company_name: companyName,
      })
      // Map profile_id (from backend) to profileId (frontend convention)
      const user = {
        ...response.user,
        profileId: (response.user as any).profile_id
      }
      localStorage.setItem('auth_token', response.access_token)
      localStorage.setItem('auth_user', JSON.stringify(user))
      set({
        user,
        isAuthenticated: true,
        token: response.access_token,
        isLoading: false,
      })
    } catch (error: any) {
      const detail = error.response?.data?.detail
      let errorMessage = 'Registration failed'

      if (Array.isArray(detail)) {
        // Handle validation errors (array of error objects)
        errorMessage = detail.map((err: any) => err.msg).join(', ')
      } else if (typeof detail === 'string') {
        errorMessage = detail
      }

      set({
        error: errorMessage,
        isLoading: false,
      })
      throw error
    }
  },

  logout: () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
    set({
      user: null,
      isAuthenticated: false,
      token: null,
      error: null,
    })
  },

  setUser: (user: User) => {
    set({ user, isAuthenticated: true })
  },

  clearError: () => {
    set({ error: null })
  },

  checkAuth: async () => {
    set({ isLoading: true })
    try {
      const response = await apiClient.verifyToken()
      set({
        user: response.user,
        isAuthenticated: true,
        token: response.access_token,
        isLoading: false,
      })
    } catch (error) {
      set({
        user: null,
        isAuthenticated: false,
        token: null,
        isLoading: false,
      })
    }
  },

  initializeAuth: () => {
    const token = localStorage.getItem('auth_token')
    const userStr = localStorage.getItem('auth_user')

    if (token && userStr) {
      try {
        const user = JSON.parse(userStr)
        set({
          user,
          isAuthenticated: true,
          token,
        })
      } catch (error) {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('auth_user')
      }
    }
  },
}))
