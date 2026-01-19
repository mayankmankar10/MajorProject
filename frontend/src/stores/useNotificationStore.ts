import { create } from 'zustand'
import { Notification } from '@/types'
import { apiClient } from '@/services/api'
import { WebSocketService } from '@/services/websocket'

interface NotificationState {
  notifications: Notification[]
  unreadCount: number
  isLoading: boolean
  error: string | null
  wsConnected: boolean
  wsService: WebSocketService | null

  // Actions
  fetchNotifications: () => Promise<void>
  markAsRead: (id: number) => Promise<void>
  markAllAsRead: () => Promise<void>
  deleteNotification: (id: number) => Promise<void>
  addNotification: (notification: Notification) => void
  connectWebSocket: (token: string) => void
  disconnectWebSocket: () => void
  clearError: () => void
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  isLoading: false,
  error: null,
  wsConnected: false,
  wsService: null,

  fetchNotifications: async () => {
    set({ isLoading: true, error: null })
    try {
      const notifications = await apiClient.getNotifications()
      const unreadCount = notifications.filter((n) => !n.is_read).length
      
      set({
        notifications,
        unreadCount,
        isLoading: false,
      })
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch notifications',
        isLoading: false,
      })
    }
  },

  markAsRead: async (id: number) => {
    try {
      await apiClient.markNotificationRead(id)
      
      set((state) => ({
        notifications: state.notifications.map((n) =>
          n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n
        ),
        unreadCount: Math.max(0, state.unreadCount - 1),
      }))
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to mark as read',
      })
    }
  },

  markAllAsRead: async () => {
    try {
      await apiClient.markAllNotificationsRead()
      
      set((state) => ({
        notifications: state.notifications.map((n) => ({
          ...n,
          is_read: true,
          read_at: new Date().toISOString(),
        })),
        unreadCount: 0,
      }))
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to mark all as read',
      })
    }
  },

  deleteNotification: async (id: number) => {
    try {
      await apiClient.deleteNotification(id)
      
      set((state) => ({
        notifications: state.notifications.filter((n) => n.id !== id),
        unreadCount: state.notifications.find((n) => n.id === id)?.is_read
          ? state.unreadCount
          : Math.max(0, state.unreadCount - 1),
      }))
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to delete notification',
      })
    }
  },

  addNotification: (notification: Notification) => {
    set((state) => ({
      notifications: [notification, ...state.notifications],
      unreadCount: notification.is_read ? state.unreadCount : state.unreadCount + 1,
    }))
  },

  connectWebSocket: (token: string) => {
    const wsService = new WebSocketService(token)
    
    wsService.onMessage((notification: Notification) => {
      get().addNotification(notification)
    })
    
    wsService.onConnect(() => {
      set({ wsConnected: true })
    })
    
    wsService.onDisconnect(() => {
      set({ wsConnected: false })
    })
    
    wsService.connect()
    
    set({ wsService })
  },

  disconnectWebSocket: () => {
    const { wsService } = get()
    if (wsService) {
      wsService.disconnect()
      set({ wsService: null, wsConnected: false })
    }
  },

  clearError: () => {
    set({ error: null })
  },
}))
