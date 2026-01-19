// Multi-Job Bulk Hire API Service
import axios from 'axios'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) || 'http://localhost:8000/api'

export interface BulkHireJob {
    id: number
    title: string
    location: string
    job_category: string | null
    cuisine_type: string | null
    shift_type: string | null
    quantity_needed: number
    quantity_filled: number
    remaining: number
    salary_range: string | null
}

export interface CandidateMatch {
    id: number
    name: string
    base_score: number
    bonus_score: number
    final_score: number
    skills: string[]
    experience_years: number
    cuisine_experience: string[]
    shift_preferences: string[]
}

export interface BulkHireInitiateResponse {
    success: boolean
    job_title: string
    job_id: number
    quantity_requested: number
    matches: CandidateMatch[]
    total_matches: number
}

export interface BulkHireConfirmResponse {
    success: boolean
    message: string
    total_hired: number
    applications_created: number
    offers_sent: number
    job_title: string
    candidates: Array<{ id: number; name: string }>
}

// Multi-job types
export interface JobSelection {
    job_id: number
    quantity: number
}

export interface JobCandidates {
    job_id: number
    job_title: string
    quantity_requested: number
    candidates: CandidateMatch[]
}

export interface MultiJobInitiateResponse {
    success: boolean
    total_positions: number
    jobs_count: number
    matches_by_job: JobCandidates[]
}

export interface JobEmployeeSelection {
    job_id: number
    candidates: Array<{ employee_id: number; score: number }>
}

export interface JobHireResult {
    job_id: number
    job_title: string
    hired_count: number
    candidates: Array<{ id: number; name: string }>
}

export interface MultiJobConfirmResponse {
    success: boolean
    message: string
    total_hired: number
    jobs_processed: number
    results_by_job: JobHireResult[]
}

export const bulkHireApi = {
    // Get employer's active jobs with remaining positions
    async getJobs(userId: number): Promise<{ success: boolean; jobs: BulkHireJob[]; total: number }> {
        const response = await axios.get(`${API_BASE_URL}/bulk-hire/jobs?user_id=${userId}`, {
            headers: {
                Authorization: `Bearer ${localStorage.getItem('auth_token')}`
            }
        })
        return response.data
    },

    // Single job initiate
    async initiate(jobId: number, quantity: number): Promise<BulkHireInitiateResponse> {
        const response = await axios.post(`${API_BASE_URL}/bulk-hire/initiate`, {
            job_id: jobId,
            quantity
        }, {
            headers: {
                Authorization: `Bearer ${localStorage.getItem('auth_token')}`
            }
        })
        return response.data
    },

    // Single job confirm
    async confirm(jobId: number, employeeIds: number[]): Promise<BulkHireConfirmResponse> {
        const response = await axios.post(`${API_BASE_URL}/bulk-hire/confirm`, {
            job_id: jobId,
            employee_ids: employeeIds
        }, {
            headers: {
                Authorization: `Bearer ${localStorage.getItem('auth_token')}`
            }
        })
        return response.data
    },

    // Multi-job initiate
    async initiateMulti(jobSelections: JobSelection[]): Promise<MultiJobInitiateResponse> {
        const response = await axios.post(`${API_BASE_URL}/bulk-hire/initiate-multi`, {
            job_selections: jobSelections
        }, {
            headers: {
                Authorization: `Bearer ${localStorage.getItem('auth_token')}`
            }
        })
        return response.data
    },

    // Multi-job confirm
    async confirmMulti(selections: JobEmployeeSelection[]): Promise<MultiJobConfirmResponse> {
        const response = await axios.post(`${API_BASE_URL}/bulk-hire/confirm-multi`, {
            selections
        }, {
            headers: {
                Authorization: `Bearer ${localStorage.getItem('auth_token')}`
            }
        })
        return response.data
    }
}
