import { Notification } from '@/types'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

type MessageHandler = (data: Notification) => void
type ConnectHandler = () => void
type DisconnectHandler = () => void
type ErrorHandler = (error: Event) => void

export class WebSocketService {
  private ws: WebSocket | null = null
  private token: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 3000
  private messageHandlers: MessageHandler[] = []
  private connectHandlers: ConnectHandler[] = []
  private disconnectHandlers: DisconnectHandler[] = []
  private errorHandlers: ErrorHandler[] = []
  private reconnectTimeout: NodeJS.Timeout | null = null

  constructor(token: string) {
    this.token = token
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected')
      return
    }

    try {
      // Connect with token as query parameter
      const wsUrl = `${WS_URL}/api/notifications/ws?token=${this.token}`
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
        this.connectHandlers.forEach((handler) => handler())
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.messageHandlers.forEach((handler) => handler(data))
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.errorHandlers.forEach((handler) => handler(error))
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.disconnectHandlers.forEach((handler) => handler())
        this.attemptReconnect()
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)

    this.reconnectTimeout = setTimeout(() => {
      this.connect()
    }, this.reconnectDelay)
  }

  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    this.reconnectAttempts = 0
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  onMessage(handler: MessageHandler) {
    this.messageHandlers.push(handler)
  }

  onConnect(handler: ConnectHandler) {
    this.connectHandlers.push(handler)
  }

  onDisconnect(handler: DisconnectHandler) {
    this.disconnectHandlers.push(handler)
  }

  onError(handler: ErrorHandler) {
    this.errorHandlers.push(handler)
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}
