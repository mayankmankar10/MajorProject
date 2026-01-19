import { format, formatDistanceToNow } from 'date-fns'
import { clsx, type ClassValue } from 'clsx'

/**
 * Merge Tailwind classes safely
 */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

/**
 * Format date to readable string
 */
export function formatDate(date: string | Date, formatStr: string = 'PPP'): string {
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date
    return format(dateObj, formatStr)
  } catch (error) {
    console.error('Error formatting date:', error)
    return 'Invalid date'
  }
}

/**
 * Format date to relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(date: string | Date): string {
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date
    return formatDistanceToNow(dateObj, { addSuffix: true })
  } catch (error) {
    console.error('Error formatting relative time:', error)
    return 'Invalid date'
  }
}

/**
 * Truncate text to specified length
 */
export function truncate(text: string, length: number = 100): string {
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}

/**
 * Capitalize first letter of each word
 */
export function capitalize(text: string): string {
  return text
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

/**
 * Format salary range
 */
export function formatSalary(salaryRange: string): string {
  return salaryRange
    .replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,')
    .replace('-', ' - ')
}

/**
 * Get initials from name
 */
export function getInitials(name: string): string {
  const parts = name.trim().split(' ')
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase()
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase()
}

/**
 * Generate random color for avatars
 */
export function getAvatarColor(name: string): string {
  const colors = [
    'bg-red-500',
    'bg-blue-500',
    'bg-green-500',
    'bg-yellow-500',
    'bg-purple-500',
    'bg-pink-500',
    'bg-indigo-500',
    'bg-teal-500',
  ]
  const index = name.charCodeAt(0) % colors.length
  return colors[index]
}

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Validate password strength
 */
export function validatePassword(password: string): {
  isValid: boolean
  errors: string[]
} {
  const errors: string[] = []

  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long')
  }
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter')
  }
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter')
  }
  if (!/[0-9]/.test(password)) {
    errors.push('Password must contain at least one number')
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null
      func(...args)
    }

    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * Deep clone object
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj))
}

/**
 * Check if object is empty
 */
export function isEmpty(obj: any): boolean {
  if (obj === null || obj === undefined) return true
  if (Array.isArray(obj)) return obj.length === 0
  if (typeof obj === 'object') return Object.keys(obj).length === 0
  return false
}

/**
 * Generate unique ID
 */
export function generateId(): string {
  return `${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

/**
 * Format file size
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * Get status color class
 */
export function getStatusColor(
  status: string
): { bg: string; text: string; badge: string } {
  const statusColors: Record<string, { bg: string; text: string; badge: string }> = {
    applied: { bg: 'bg-blue-100', text: 'text-blue-800', badge: 'bg-blue-500' },
    reviewing: { bg: 'bg-yellow-100', text: 'text-yellow-800', badge: 'bg-yellow-500' },
    interview_scheduled: {
      bg: 'bg-purple-100',
      text: 'text-purple-800',
      badge: 'bg-purple-500',
    },
    selected: { bg: 'bg-green-100', text: 'text-green-800', badge: 'bg-green-500' },
    rejected: { bg: 'bg-red-100', text: 'text-red-800', badge: 'bg-red-500' },
    hired: { bg: 'bg-emerald-100', text: 'text-emerald-800', badge: 'bg-emerald-500' },
    scheduled: { bg: 'bg-blue-100', text: 'text-blue-800', badge: 'bg-blue-500' },
    confirmed: { bg: 'bg-green-100', text: 'text-green-800', badge: 'bg-green-500' },
    completed: { bg: 'bg-gray-100', text: 'text-gray-800', badge: 'bg-gray-500' },
    cancelled: { bg: 'bg-red-100', text: 'text-red-800', badge: 'bg-red-500' },
  }

  return (
    statusColors[status.toLowerCase()] || {
      bg: 'bg-gray-100',
      text: 'text-gray-800',
      badge: 'bg-gray-500',
    }
  )
}

/**
 * Calculate match score color
 */
export function getMatchScoreColor(score: number): string {
  if (score >= 80) return 'text-green-600'
  if (score >= 60) return 'text-yellow-600'
  if (score >= 40) return 'text-orange-600'
  return 'text-red-600'
}

/**
 * Parse error message from API response
 */
export function parseError(error: any): string {
  if (typeof error === 'string') return error

  if (error?.response?.data?.detail) {
    const detail = error.response.data.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map((d) => d.msg).join(', ')
  }

  if (error?.message) return error.message

  return 'An unexpected error occurred'
}
