import { create } from 'zustand'
import { Job } from '@/types'
import { apiClient } from '@/services/api'

interface JobState {
  jobs: Job[]
  currentJob: Job | null
  isLoading: boolean
  error: string | null
  filters: {
    search: string
    location: string
    jobType: string
    salaryRange: string
  }

  // Actions
  fetchJobs: () => Promise<void>
  fetchJobById: (id: number) => Promise<void>
  createJob: (jobData: any) => Promise<void>
  updateJob: (id: number, jobData: any) => Promise<void>
  deleteJob: (id: number) => Promise<void>
  searchJobs: (query: string) => Promise<void>
  setFilters: (filters: Partial<JobState['filters']>) => void
  clearFilters: () => void
  clearError: () => void
}

export const useJobStore = create<JobState>((set, get) => ({
  jobs: [],
  currentJob: null,
  isLoading: false,
  error: null,
  filters: {
    search: '',
    location: '',
    jobType: '',
    salaryRange: '',
  },

  fetchJobs: async () => {
    set({ isLoading: true, error: null })
    try {
      const jobs = await apiClient.getJobs()
      set({ jobs, isLoading: false })
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch jobs',
        isLoading: false,
      })
    }
  },

  fetchJobById: async (id: number) => {
    set({ isLoading: true, error: null })
    try {
      const job = await apiClient.getJobById(id)
      set({ currentJob: job, isLoading: false })
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to fetch job',
        isLoading: false,
      })
    }
  },

  createJob: async (jobData: any) => {
    set({ isLoading: true, error: null })
    try {
      const newJob = await apiClient.createJob(jobData)
      set((state) => ({
        jobs: [newJob, ...state.jobs],
        isLoading: false,
      }))
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to create job',
        isLoading: false,
      })
      throw error
    }
  },

  updateJob: async (id: number, jobData: any) => {
    set({ isLoading: true, error: null })
    try {
      const updatedJob = await apiClient.updateJob(id, jobData)
      set((state) => ({
        jobs: state.jobs.map((job) => (job.id === id ? updatedJob : job)),
        currentJob: state.currentJob?.id === id ? updatedJob : state.currentJob,
        isLoading: false,
      }))
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to update job',
        isLoading: false,
      })
      throw error
    }
  },

  deleteJob: async (id: number) => {
    set({ isLoading: true, error: null })
    try {
      await apiClient.deleteJob(id)
      set((state) => ({
        jobs: state.jobs.filter((job) => job.id !== id),
        currentJob: state.currentJob?.id === id ? null : state.currentJob,
        isLoading: false,
      }))
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to delete job',
        isLoading: false,
      })
      throw error
    }
  },

  searchJobs: async (query: string) => {
    set({ isLoading: true, error: null })
    try {
      // Use chat API for semantic search
      const response = await apiClient.sendChatMessage(`Find jobs: ${query}`)
      // This will be handled by the AI, so we fetch all jobs after
      await get().fetchJobs()
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to search jobs',
        isLoading: false,
      })
    }
  },

  setFilters: (filters: Partial<JobState['filters']>) => {
    set((state) => ({
      filters: { ...state.filters, ...filters },
    }))
  },

  clearFilters: () => {
    set({
      filters: {
        search: '',
        location: '',
        jobType: '',
        salaryRange: '',
      },
    })
  },

  clearError: () => {
    set({ error: null })
  },
}))
