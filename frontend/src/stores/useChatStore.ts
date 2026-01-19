import { create } from 'zustand'
import { ChatMessage, ChatSession } from '@/types'
import { apiClient } from '@/services/api'

interface ChatState {
  sessions: Record<string, ChatSession>
  currentSessionId: string | null
  isLoading: boolean
  error: string | null

  // Actions
  sendMessage: (message: string, sessionId?: string) => Promise<void>
  loadHistory: (sessionId: string) => Promise<void>
  clearSession: (sessionId: string) => Promise<void>
  setCurrentSession: (sessionId: string) => void
  addMessage: (sessionId: string, message: ChatMessage) => void
  clearError: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: {},
  currentSessionId: null,
  isLoading: false,
  error: null,

  sendMessage: async (message: string, sessionId?: string) => {
    set({ isLoading: true, error: null })
    
    const sid = sessionId || get().currentSessionId || `session_${Date.now()}`
    
    // Add user message immediately
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    }
    
    get().addMessage(sid, userMessage)

    try {
      const response = await apiClient.sendChatMessage(message, sid)
      
      // Add assistant response
      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now()}_assistant`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
      }
      
      get().addMessage(sid, assistantMessage)
      
      set({ 
        currentSessionId: sid,
        isLoading: false 
      })
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to send message',
        isLoading: false,
      })
      throw error
    }
  },

  loadHistory: async (sessionId: string) => {
    set({ isLoading: true, error: null })
    try {
      const history = await apiClient.getChatHistory(sessionId)
      
      set((state) => ({
        sessions: {
          ...state.sessions,
          [sessionId]: {
            session_id: sessionId,
            messages: history.messages || [],
          },
        },
        currentSessionId: sessionId,
        isLoading: false,
      }))
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to load history',
        isLoading: false,
      })
    }
  },

  clearSession: async (sessionId: string) => {
    try {
      await apiClient.clearChatSession(sessionId)
      
      set((state) => {
        const newSessions = { ...state.sessions }
        delete newSessions[sessionId]
        
        return {
          sessions: newSessions,
          currentSessionId: state.currentSessionId === sessionId ? null : state.currentSessionId,
        }
      })
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to clear session',
      })
      throw error
    }
  },

  setCurrentSession: (sessionId: string) => {
    set({ currentSessionId: sessionId })
  },

  addMessage: (sessionId: string, message: ChatMessage) => {
    set((state) => {
      const session = state.sessions[sessionId] || { session_id: sessionId, messages: [] }
      
      return {
        sessions: {
          ...state.sessions,
          [sessionId]: {
            ...session,
            messages: [...session.messages, message],
          },
        },
      }
    })
  },

  clearError: () => {
    set({ error: null })
  },
}))
