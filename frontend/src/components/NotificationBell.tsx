// frontend/src/components/NotificationBell.tsx
import React, { useState, useEffect } from 'react'
import { Bell } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { apiClient } from '@/services/api'
import { useNavigate } from 'react-router-dom'

interface Notification {
    id: number
    title: string
    message: string
    notification_type: string
    action_url?: string
    is_read: boolean
    created_at: string
}

export const NotificationBell: React.FC = () => {
    const [notifications, setNotifications] = useState<Notification[]>([])
    const [unreadCount, setUnreadCount] = useState(0)
    const [isOpen, setIsOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()

    useEffect(() => {
        fetchNotifications()
        // Poll for new notifications every 30 seconds
        const interval = setInterval(fetchUnreadCount, 30000)
        return () => clearInterval(interval)
    }, [])

    const fetchNotifications = async () => {
        try {
            setLoading(true)
            const notifications = await apiClient.getNotifications()
            setNotifications(notifications)

            const unread = notifications.filter((n: Notification) => !n.is_read).length
            setUnreadCount(unread)
        } catch (error) {
            console.error('Failed to fetch notifications:', error)
        } finally {
            setLoading(false)
        }
    }

    const fetchUnreadCount = async () => {
        try {
            const data = await apiClient.getUnreadCount()
            setUnreadCount(data.unread_count)
        } catch (error) {
            console.error('Failed to fetch unread count:', error)
        }
    }

    const markAsRead = async (notificationId: number) => {
        try {
            await apiClient.markNotificationAsRead(notificationId)

            setNotifications(prev =>
                prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
            )
            setUnreadCount(prev => Math.max(0, prev - 1))
        } catch (error) {
            console.error('Failed to mark as read:', error)
        }
    }

    const markAllAsRead = async () => {
        try {
            await apiClient.markAllNotificationsAsRead()

            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
            setUnreadCount(0)
        } catch (error) {
            console.error('Failed to mark all as read:', error)
        }
    }

    const handleNotificationClick = (notification: Notification) => {
        markAsRead(notification.id)
        if (notification.action_url) {
            navigate(notification.action_url)
        }
        setIsOpen(false)
    }

    return (
        <div className="relative">
            {/* Bell Icon */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
                <Bell className="w-6 h-6" />
                {unreadCount > 0 && (
                    <span className="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                        {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                )}
            </button>

            {/* Dropdown */}
            <AnimatePresence>
                {isOpen && (
                    <>
                        {/* Backdrop */}
                        <div
                            className="fixed inset-0 z-40"
                            onClick={() => setIsOpen(false)}
                        />

                        {/* Notification Panel */}
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-[500px] overflow-hidden flex flex-col"
                        >
                            {/* Header */}
                            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                                <h3 className="font-semibold text-gray-900">Notifications</h3>
                                {unreadCount > 0 && (
                                    <button
                                        onClick={markAllAsRead}
                                        className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                                    >
                                        Mark all read
                                    </button>
                                )}
                            </div>

                            {/* Notifications List */}
                            <div className="overflow-y-auto flex-1">
                                {loading ? (
                                    <div className="p-8 text-center text-gray-500">
                                        Loading...
                                    </div>
                                ) : notifications.length === 0 ? (
                                    <div className="p-8 text-center text-gray-500">
                                        <Bell className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                                        <p>No notifications yet</p>
                                    </div>
                                ) : (
                                    <div className="divide-y divide-gray-100">
                                        {notifications.map(notification => (
                                            <div
                                                key={notification.id}
                                                onClick={() => handleNotificationClick(notification)}
                                                className={`p-4 cursor-pointer transition-colors ${notification.is_read
                                                    ? 'bg-white hover:bg-gray-50'
                                                    : 'bg-blue-50 hover:bg-blue-100'
                                                    }`}
                                            >
                                                <div className="flex items-start gap-3">
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2 mb-1">
                                                            <h4 className="font-medium text-gray-900 text-sm">
                                                                {notification.title}
                                                            </h4>
                                                            {!notification.is_read && (
                                                                <span className="w-2 h-2 bg-blue-500 rounded-full" />
                                                            )}
                                                        </div>
                                                        <p className="text-sm text-gray-600 line-clamp-2">
                                                            {notification.message}
                                                        </p>
                                                        <p className="text-xs text-gray-400 mt-1">
                                                            {new Date(notification.created_at).toLocaleString()}
                                                        </p>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Footer */}
                            {notifications.length > 0 && (
                                <div className="p-3 border-t border-gray-200 text-center">
                                    <button
                                        onClick={() => {
                                            navigate('/employee/notifications')
                                            setIsOpen(false)
                                        }}
                                        className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                                    >
                                        View all notifications
                                    </button>
                                </div>
                            )}
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    )
}
