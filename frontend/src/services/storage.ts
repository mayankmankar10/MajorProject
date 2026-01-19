/**
 * LocalStorage utility service
 * Provides type-safe storage operations with error handling
 */

const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  AUTH_USER: 'auth_user',
  THEME: 'theme',
  CHAT_SESSIONS: 'chat_sessions',
  FILTERS: 'filters',
} as const

export class StorageService {
  /**
   * Get item from localStorage with type safety
   */
  static getItem<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(key)
      if (!item) return null
      return JSON.parse(item) as T
    } catch (error) {
      console.error(`Error getting item from localStorage: ${key}`, error)
      return null
    }
  }

  /**
   * Set item in localStorage
   */
  static setItem<T>(key: string, value: T): void {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error(`Error setting item in localStorage: ${key}`, error)
    }
  }

  /**
   * Remove item from localStorage
   */
  static removeItem(key: string): void {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.error(`Error removing item from localStorage: ${key}`, error)
    }
  }

  /**
   * Clear all items from localStorage
   */
  static clear(): void {
    try {
      localStorage.clear()
    } catch (error) {
      console.error('Error clearing localStorage', error)
    }
  }

  /**
   * Check if a key exists in localStorage
   */
  static hasItem(key: string): boolean {
    return localStorage.getItem(key) !== null
  }

  /**
   * Get all keys from localStorage
   */
  static getAllKeys(): string[] {
    return Object.keys(localStorage)
  }

  // Auth-specific methods
  static getAuthToken(): string | null {
    return localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN)
  }

  static setAuthToken(token: string): void {
    localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token)
  }

  static removeAuthToken(): void {
    localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN)
  }

  static getAuthUser<T>(): T | null {
    return this.getItem<T>(STORAGE_KEYS.AUTH_USER)
  }

  static setAuthUser<T>(user: T): void {
    this.setItem(STORAGE_KEYS.AUTH_USER, user)
  }

  static removeAuthUser(): void {
    localStorage.removeItem(STORAGE_KEYS.AUTH_USER)
  }

  // Theme-specific methods
  static getTheme(): 'light' | 'dark' | null {
    return localStorage.getItem(STORAGE_KEYS.THEME) as 'light' | 'dark' | null
  }

  static setTheme(theme: 'light' | 'dark'): void {
    localStorage.setItem(STORAGE_KEYS.THEME, theme)
  }

  // Chat sessions
  static getChatSessions<T>(): T | null {
    return this.getItem<T>(STORAGE_KEYS.CHAT_SESSIONS)
  }

  static setChatSessions<T>(sessions: T): void {
    this.setItem(STORAGE_KEYS.CHAT_SESSIONS, sessions)
  }

  static removeChatSessions(): void {
    localStorage.removeItem(STORAGE_KEYS.CHAT_SESSIONS)
  }

  // Filters
  static getFilters<T>(): T | null {
    return this.getItem<T>(STORAGE_KEYS.FILTERS)
  }

  static setFilters<T>(filters: T): void {
    this.setItem(STORAGE_KEYS.FILTERS, filters)
  }

  static removeFilters(): void {
    localStorage.removeItem(STORAGE_KEYS.FILTERS)
  }
}

export const storage = StorageService
