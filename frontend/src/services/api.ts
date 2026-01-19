import axios, { AxiosInstance, AxiosError } from 'axios'
import { AuthResponse, LoginRequest, RegisterRequest } from '@/types'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) || 'http://localhost:8000/api'

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Handle responses
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token')
          localStorage.removeItem('auth_user')
          window.location.href = '/auth/login'
        }
        return Promise.reject(error)
      }
    )
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/auth/login', credentials)
    return response.data
  }

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/auth/register', data)
    return response.data
  }

  async verifyToken(): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/auth/verify-token', {})
    return response.data
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me')
    return response.data
  }

  // Jobs
  async getJobs(filters?: Record<string, any>) {
    const response = await this.client.get('/employer/jobs', { params: filters })
    return response.data
  }

  async getJobById(jobId: number) {
    const response = await this.client.get(`/employer/jobs/${jobId}`)
    return response.data
  }

  async createJob(jobData: any) {
    const response = await this.client.post('/employer/jobs', jobData)
    return response.data
  }

  async updateJob(jobId: number, jobData: any) {
    const response = await this.client.put(`/employer/jobs/${jobId}`, jobData)
    return response.data
  }

  async deleteJob(jobId: number) {
    await this.client.delete(`/employer/jobs/${jobId}`)
  }

  // Employee - Job Discovery
  async getJobRecommendations() {
    const response = await this.client.get('/employee/recommendations')
    return response.data
  }

  async searchJobs(query: string, filters?: Record<string, any>) {
    const response = await this.client.get('/employee/jobs', {
      params: { q: query, ...filters },
    })
    return response.data
  }

  // Employee - Personalized Job Recommendations
  async getRecommendedJobs(employeeId: number, params?: {
    search?: string
    location?: string
    job_type?: string
    min_salary?: number
    max_salary?: number
    experience_level?: string
    top_k?: number
  }) {
    const response = await this.client.get(`/employee/employees/${employeeId}/recommended-jobs`, {
      params
    })
    return response.data
  }

  // Applications
  async getApplications() {
    const userStr = localStorage.getItem('auth_user')
    const user = userStr ? JSON.parse(userStr) : null
    const userId = user?.id

    const response = await this.client.get('/employee/applications', {
      params: { user_id: userId }
    })
    return response.data
  }

  async getApplicationById(appId: number) {
    const response = await this.client.get(`/employee/applications/${appId}`)
    return response.data
  }

  async createApplication(appData: any) {
    const response = await this.client.post('/employee/applications', appData)
    return response.data
  }

  async updateApplicationStatus(appId: number, status: string) {
    const response = await this.client.put(`/applications/${appId}`, { status })
    return response.data
  }

  // Interviews
  async getInterviews() {
    const response = await this.client.get('/interviews')
    return response.data
  }

  async getEmployeeInterviews() {
    const response = await this.client.get('/employee/interviews')
    return response.data
  }

  async scheduleInterview(interviewData: any) {
    const response = await this.client.post('/interviews', interviewData)
    return response.data
  }

  async updateInterview(interviewId: number, data: any) {
    const response = await this.client.put(`/interviews/${interviewId}`, data)
    return response.data
  }

  // Candidates (for employers)
  async getCandidates() {
    const response = await this.client.get('/employer/candidates')
    return response.data
  }

  async getCandidateById(candidateId: number) {
    const response = await this.client.get(`/employer/candidates/${candidateId}`)
    return response.data
  }

  // Analytics
  async getDashboardMetrics() {
    const response = await this.client.get('/analytics/dashboard')
    return response.data
  }

  async getJobPerformance(jobId: number) {
    const response = await this.client.get(`/analytics/jobs/performance/${jobId}`)
    return response.data
  }

  // Chat
  async sendChatMessage(message: string, sessionId?: string) {
    const user = JSON.parse(localStorage.getItem('auth_user') || '{}')
    const response = await this.client.post('/chat/message', {
      message,
      session_id: sessionId,
      user_id: user.id,
      role: user.role
    })
    return response.data
  }

  async getChatHistory(sessionId: string) {
    const response = await this.client.get(`/chat/history/${sessionId}`)
    return response.data
  }

  async getChatSessions() {
    const userStr = localStorage.getItem('auth_user')
    const user = userStr ? JSON.parse(userStr) : null
    const userId = user?.id

    const response = await this.client.get('/chat/sessions', {
      params: { user_id: userId }
    })
    return response.data
  }

  async clearChatSession(sessionId: string) {
    const response = await this.client.post(`/chat/clear/${sessionId}`)
    return response.data
  }

  // Notifications
  async getNotifications() {
    const response = await this.client.get('/notifications')
    return response.data
  }

  async getUnreadCount() {
    const response = await this.client.get('/notifications/unread-count')
    return response.data
  }

  async markNotificationAsRead(notificationId: number) {
    const response = await this.client.post(`/notifications/mark-read`, {
      notification_ids: [notificationId],  // Backend expects array
    })
    return response.data
  }

  async markAllNotificationsAsRead() {
    const response = await this.client.post('/notifications/mark-all-read')
    return response.data
  }

  async deleteNotification(notificationId: number) {
    await this.client.delete(`/notifications/${notificationId}`)
  }

  // Offers
  async getOffers(status?: string) {
    const params = status ? { status } : {}
    const response = await this.client.get('/offers', { params })
    return response.data
  }

  async getOfferDetails(offerId: number) {
    const response = await this.client.get(`/offers/${offerId}`)
    return response.data
  }

  async acceptOffer(offerId: number, data: {
    sign_offer?: boolean
    sign_nda?: boolean
    confirm_start_date?: boolean
  }) {
    const response = await this.client.post(`/offers/${offerId}/accept`, data)
    return response.data
  }

  async declineOffer(offerId: number, data: { reason?: string }) {
    const response = await this.client.post(`/offers/${offerId}/decline`, data)
    return response.data
  }

  // Tools
  async getAvailableTools() {
    const response = await this.client.get('/tools/available')
    return response.data
  }

  async invokeATool(toolName: string, parameters: Record<string, any>) {
    const response = await this.client.post('/tools/invoke', {
      tool_name: toolName,
      parameters,
    })
    return response.data
  }

  // Onboarding - New endpoints
  async getOnboardingProgress(employeeId: number) {
    const response = await this.client.get(`/onboarding/progress/${employeeId}`)
    return response.data
  }


  async getAllOnboardingData(employeeId: number) {
    const response = await this.client.get(`/onboarding/data/${employeeId}`)
    return response.data
  }

  async downloadEmployeeResume(employeeId: number) {
    const response = await this.client.get(`/onboarding/resume/${employeeId}`, {
      responseType: 'blob'
    })
    return response.data
  }


  // Onboarding Update Methods
  async updateEmployeeProfile(employeeId: number, profileData: {
    full_name?: string
    phone?: string
    location?: string
    bio?: string
  }) {
    const response = await this.client.put(`/employee/employees/${employeeId}/profile`, profileData)
    return response.data
  }

  async addEmployeeSkills(employeeId: number, skillsData: {
    skills: string[]
    soft_skills?: string[]  // NEW: Soft skills
    experience_years?: number
    years_in_hospitality?: number
  }) {
    const response = await this.client.post(`/employee/employees/${employeeId}/skills`, skillsData)
    return response.data
  }

  async addWorkHistory(employeeId: number, workHistoryData: {
    work_history: Array<{
      employer: string
      position: string
      location?: string
      start_date: string
      end_date?: string | null
      is_current: boolean
      achievements: string[]
    }>
  }) {
    const response = await this.client.post(`/employee/employees/${employeeId}/work-history`, workHistoryData)
    return response.data
  }

  async updateJobPreferences(employeeId: number, preferences: {
    preferred_role?: string
    preferred_location?: string
    preferred_shift?: string
    expected_salary_min?: number
    expected_salary_max?: number
  }) {
    const response = await this.client.put(`/employee/employees/${employeeId}/preferences`, preferences)
    return response.data
  }

  async addCertifications(employeeId: number, certData: {
    certifications: string[]
  }) {
    const response = await this.client.post(`/employee/employees/${employeeId}/certifications`, certData)
    return response.data
  }

  async uploadEmployeeResume(employeeId: number, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.client.post(`/employee/employees/${employeeId}/resume/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  }

  // Resume Upload (Employee)
  async uploadResume(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.client.post('/employee/upload-resume', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  }

  // Resume Generation (AI-powered)
  async getResume(employeeId: number) {
    const response = await this.client.get(`/employee/employees/${employeeId}/resume`)
    return response.data
  }

  async generateResume(employeeId: number, regenerate: boolean = false, format: string = 'text') {
    const response = await this.client.post(`/employee/employees/${employeeId}/resume/generate`, {
      regenerate,
      format
    })
    return response.data
  }

  async downloadResumePDF(employeeId: number) {
    const response = await this.client.get(`/employee/employees/${employeeId}/resume/download`)
    return response.data
  }

  // Employer Onboarding
  async getEmployerOnboardingStatus() {
    const response = await this.client.get('/employer/onboarding-status')
    return response.data
  }

  async updateEmployerProfile(profileData: {
    company_profile?: string
    industry?: string
    location?: string
    website?: string
  }) {
    const response = await this.client.put('/employer/profile', profileData)
    return response.data
  }

  async updateEmployerHiringPreferences(data: {
    preferences: Array<{
      role: string
      positions: number
      location: string
      shift: string
      salary_min: number
      salary_max: number
    }>
  }) {
    const response = await this.client.put('/employer/hiring-preferences', data)
    return response.data
  }

  // Onboarding Tasks (Employee)
  async getOnboardingTasks() {
    const response = await this.client.get('/onboarding/tasks')
    return response.data
  }

  async completeOnboardingTask(taskId: number) {
    const response = await this.client.post(`/onboarding/tasks/${taskId}/complete`)
    return response.data
  }
}

export const apiClient = new APIClient()
