import React, { useState, useEffect, useRef } from 'react'
import { Send, Loader2, MessageSquare, Trash2, Users } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { apiClient } from '@/services/api'
import { useAuthStore } from '@/stores/useAuthStore'
import clsx from 'clsx'
import { ProfileForm } from '@/components/onboarding/ProfileForm'
import { SkillsForm } from '@/components/onboarding/SkillsForm'
import { WorkHistoryForm } from '@/components/onboarding/WorkHistoryForm'
import { PreferencesForm } from '@/components/onboarding/PreferencesForm'
import { CertificationsForm } from '@/components/onboarding/CertificationsForm'
import { ResumeUploadForm } from '@/components/onboarding/ResumeUploadForm'
import { CompanyProfileForm } from '@/components/employer/CompanyProfileForm'
import { HiringPreferencesForm } from '@/components/employer/HiringPreferencesForm'
import { BulkHireModal } from '@/components/employer/BulkHireModal'

interface Message {
    role: 'user' | 'assistant'
    content: string
    timestamp?: Date
}

interface OnboardingProgressData {
    completion_percentage: number
    is_complete: boolean
    steps: {
        profile: boolean
        skills: boolean
        preferences: boolean
        certifications: boolean
        documents: boolean
    }
}

interface EmployerOnboardingProgressData {
    onboarding_complete: boolean
    steps: {
        company_profile: boolean
        hiring_preferences: boolean
    }
}

export const Chat: React.FC = () => {
    const { user } = useAuthStore()
    const [searchParams, setSearchParams] = useSearchParams()
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [sessionId, setSessionId] = useState<string>('')
    const [onboardingProgress, setOnboardingProgress] = useState<OnboardingProgressData | null>(null)
    const [employerOnboardingProgress, setEmployerOnboardingProgress] = useState<EmployerOnboardingProgressData | null>(null)
    const [isChecklistExpanded, setIsChecklistExpanded] = useState(false)
    const [activeModal, setActiveModal] = useState<'profile' | 'skills' | 'work_history' | 'preferences' | 'certifications' | 'resume' | null>(null)
    const [activeEmployerModal, setActiveEmployerModal] = useState<'company_profile' | 'hiring_preferences' | null>(null)
    const [isBulkHireModalOpen, setIsBulkHireModalOpen] = useState(false)
    const [autoReviewTriggered, setAutoReviewTriggered] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    // Load chat history on mount
    useEffect(() => {
        const loadChatHistory = async () => {
            // Reset messages when user changes (new login)
            setMessages([])
            setSessionId('')

            try {
                const sessions = await apiClient.getChatSessions()
                if (sessions.sessions && sessions.sessions.length > 0) {
                    // Handle both old format (string) and new format (object)
                    const lastSession = sessions.sessions[0]
                    const lastSessionId = typeof lastSession === 'string'
                        ? lastSession
                        : lastSession.session_id

                    setSessionId(lastSessionId)
                    const history = await apiClient.getChatHistory(lastSessionId)
                    if (history.messages) {
                        setMessages(history.messages.map((msg: any) => ({
                            role: msg.role,
                            content: msg.content,
                            timestamp: new Date()
                        })))
                    }
                }
            } catch (error) {
                console.error('Failed to load chat history:', error)
            }
        }

        // Only load if user exists
        if (user) {
            loadChatHistory()
        }
    }, [user?.id]) // Re-run when user ID changes

    // Load onboarding progress for employees
    useEffect(() => {
        const loadOnboardingProgress = async () => {
            if (user?.role !== 'employee') return

            try {
                const employeeId = user?.profileId || user?.id || 1  // Use profileId if available
                const progress = await apiClient.getOnboardingProgress(employeeId)
                console.log('Onboarding progress loaded:', progress)
                setOnboardingProgress(progress)
            } catch (error) {
                console.error('Failed to load onboarding progress:', error)
                // Fallback: Show checklist with all tasks incomplete for new users
                setOnboardingProgress({
                    completion_percentage: 0,
                    is_complete: false,
                    steps: {
                        profile: false,
                        skills: false,
                        preferences: false,
                        certifications: false,
                        documents: false
                    }
                })
            }
        }

        // Only load if user is employee
        if (user?.role === 'employee') {
            loadOnboardingProgress()
        }
    }, [user])

    // Load onboarding progress for employers
    useEffect(() => {
        const loadEmployerOnboardingProgress = async () => {
            if (user?.role !== 'employer') return

            try {
                const progress = await apiClient.getEmployerOnboardingStatus()
                console.log('Employer onboarding progress loaded:', progress)
                setEmployerOnboardingProgress(progress)
            } catch (error) {
                console.error('Failed to load employer onboarding progress:', error)
                // Fallback: Show checklist with all tasks incomplete
                setEmployerOnboardingProgress({
                    onboarding_complete: false,
                    steps: {
                        company_profile: false,
                        hiring_preferences: false
                    }
                })
            }
        }

        // Only load if user is employer
        if (user?.role === 'employer') {
            loadEmployerOnboardingProgress()
        }
    }, [user])

    // Handle auto-review from URL parameters
    useEffect(() => {
        const action = searchParams.get('action')
        const applicationId = searchParams.get('applicationId')

        // Only trigger review once and if user is employer
        if (action === 'review' && applicationId && user?.role === 'employer' && !autoReviewTriggered && !isLoading) {
            setAutoReviewTriggered(true)

            // Auto-send review request
            const reviewMessage = `Review application #${applicationId}. Please provide insights about the candidate, their qualifications, match score, and recommendations.`

            setMessages(prev => [...prev, {
                role: 'user',
                content: reviewMessage,
                timestamp: new Date()
            }])

            setIsLoading(true)

            apiClient.sendChatMessage(reviewMessage, sessionId)
                .then(response => {
                    if (response.session_id) {
                        setSessionId(response.session_id)
                    }

                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: response.response || 'I apologize, but I encountered an error processing your request.',
                        timestamp: new Date()
                    }])
                })
                .catch(error => {
                    console.error('Auto-review error:', error)
                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: `Sorry, I encountered an error reviewing this application: ${error.message || 'Please try again.'}`,
                        timestamp: new Date()
                    }])
                })
                .finally(() => {
                    setIsLoading(false)
                    // Clear query params after auto-review
                    setSearchParams({})
                })
        }
    }, [searchParams, user, sessionId, autoReviewTriggered, isLoading, setSearchParams])

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim() || isLoading) return

        const userMessage: Message = {
            role: 'user',
            content: input.trim(),
            timestamp: new Date()
        }

        setMessages(prev => [...prev, userMessage])
        setInput('')
        setIsLoading(true)

        try {
            const response = await apiClient.sendChatMessage(input.trim(), sessionId)

            if (response.session_id) {
                setSessionId(response.session_id)
            }

            const assistantMessage: Message = {
                role: 'assistant',
                content: response.response || 'I apologize, but I encountered an error processing your request.',
                timestamp: new Date()
            }

            setMessages(prev => [...prev, assistantMessage])
        } catch (error: any) {
            console.error('Chat error:', error)
            const errorMessage: Message = {
                role: 'assistant',
                content: `Sorry, I encountered an error: ${error.message || 'Please try again.'}`,
                timestamp: new Date()
            }
            setMessages(prev => [...prev, errorMessage])
        } finally {
            setIsLoading(false)
        }
    }

    const handleClearChat = async () => {
        if (!sessionId) {
            setMessages([])
            return
        }

        try {
            await apiClient.clearChatSession(sessionId)
            setMessages([])
            setSessionId('')
        } catch (error) {
            console.error('Failed to clear chat:', error)
        }
    }

    const handleFormComplete = async () => {
        setActiveModal(null)
        // Refresh onboarding progress
        if (user?.role === 'employee' && user?.id) {
            try {
                const employeeId = user.profileId || user.id  // Use profileId if available
                const progress = await apiClient.getOnboardingProgress(employeeId)
                setOnboardingProgress(progress)
            } catch (error) {
                console.error('Failed to refresh onboarding progress:', error)
            }
        }
    }

    const handleEmployerFormComplete = async () => {
        setActiveEmployerModal(null)
        // Refresh employer onboarding progress
        if (user?.role === 'employer') {
            try {
                const progress = await apiClient.getEmployerOnboardingStatus()
                setEmployerOnboardingProgress(progress)
            } catch (error) {
                console.error('Failed to refresh employer onboarding progress:', error)
            }
        }
    }

    const getWelcomeMessage = () => {
        if (user?.role === 'employee') {
            return "Hi! I'm your AI assistant. I can help you find jobs, check application status, analyze your profile, and more. What would you like to do today?"
        } else {
            return "Hi! I'm your AI assistant. I can help you post jobs, find candidates, manage applications, schedule interviews, and more. How can I assist you?"
        }
    }

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col bg-white rounded-lg shadow-sm border border-slate-200">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-200">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary-100 rounded-lg">
                        <MessageSquare className="w-5 h-5 text-primary-600" />
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold text-slate-900">AI Assistant</h2>
                        <p className="text-sm text-slate-500">
                            {user?.role === 'employee' ? 'Job Search Helper' : 'Recruitment Assistant'}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {/* Bulk Hire Button (Employers Only) */}
                    {user?.role === 'employer' && (
                        <button
                            onClick={() => setIsBulkHireModalOpen(true)}
                            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
                            title="Bulk hire from existing jobs"
                        >
                            <Users className="w-4 h-4" />
                            Bulk Hire
                        </button>
                    )}
                    <button
                        onClick={handleClearChat}
                        className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                        title="Clear chat"
                    >
                        <Trash2 className="w-5 h-5" />
                    </button>
                </div>
            </div>

            {/* Welcome Header & Onboarding Checklist (Employees Only) */}
            {user?.role === 'employee' && onboardingProgress && !onboardingProgress.is_complete && (
                <>
                    {/* Welcome Header with Progress */}
                    <div className="px-6 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
                        <div className="flex items-start gap-4">
                            <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
                                <MessageSquare className="w-6 h-6" />
                            </div>
                            <div className="flex-1">
                                <h2 className="text-xl font-bold mb-1">Welcome to SmartServe!</h2>
                                <p className="text-blue-100 text-sm">Let's get you started on your job search journey</p>
                            </div>
                            <button
                                onClick={() => setIsChecklistExpanded(!isChecklistExpanded)}
                                className="px-3 py-1 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors"
                            >
                                {isChecklistExpanded ? 'Hide Checklist' : 'Show Checklist'}
                            </button>
                        </div>

                        {/* Progress Bar */}
                        <div className="mt-3 space-y-2">
                            <div className="flex items-center justify-between text-xs">
                                <span className="font-semibold">Your Progress</span>
                                <span className="font-medium">
                                    {Object.values(onboardingProgress!.steps).filter(Boolean).length} of 5 completed
                                </span>
                            </div>
                            <div className="relative w-full h-2 bg-blue-800/30 rounded-full overflow-hidden">
                                <div
                                    className="absolute top-0 left-0 h-full bg-white rounded-full transition-all duration-500"
                                    style={{ width: `${onboardingProgress!.completion_percentage}%` }}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Collapsible Getting Started Checklist */}
                    {isChecklistExpanded && (
                        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 max-h-96 overflow-y-auto">
                            <h3 className="text-base font-bold text-gray-900 mb-2">Getting Started Checklist</h3>
                            <p className="text-xs text-gray-600 mb-3">Complete these tasks to optimize your job search experience</p>

                            <div className="space-y-2">
                                {/* Task 1: Complete Profile */}
                                <div className="flex items-start gap-2 p-3 bg-white rounded-lg border border-gray-200">
                                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 font-bold flex items-center justify-center text-xs">
                                        1
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h4 className="font-semibold text-gray-900 text-sm">Complete Your Profile</h4>
                                        <p className="text-xs text-gray-600">Add your personal information, skills, and experience to help employers find you.</p>
                                    </div>
                                    <button
                                        onClick={() => setActiveModal('profile')}
                                        disabled={onboardingProgress!.steps.profile}
                                        className={`flex-shrink-0 px-3 py-1 rounded-lg font-medium text-xs transition-all ${onboardingProgress!.steps.profile
                                            ? 'bg-green-100 text-green-700 cursor-not-allowed'
                                            : 'bg-blue-600 text-white hover:bg-blue-700'
                                            }`}
                                    >
                                        {onboardingProgress!.steps.profile ? '✓' : 'Start'}
                                    </button>
                                </div>

                                {/* Task 2: Add Skills */}
                                <div className="flex items-start gap-2 p-3 bg-white rounded-lg border border-gray-200">
                                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 font-bold flex items-center justify-center text-xs">
                                        2
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h4 className="font-semibold text-gray-900 text-sm">Add Your Skills</h4>
                                        <p className="text-xs text-gray-600">Tell us about your work history and expertise.</p>
                                    </div>
                                    <button
                                        onClick={() => setActiveModal('skills')}
                                        disabled={onboardingProgress!.steps.skills}
                                        className={`flex-shrink-0 px-3 py-1 rounded-lg font-medium text-xs transition-all ${onboardingProgress!.steps.skills
                                            ? 'bg-green-100 text-green-700 cursor-not-allowed'
                                            : 'bg-blue-600 text-white hover:bg-blue-700'
                                            }`}
                                    >
                                        {onboardingProgress!.steps.skills ? '✓' : 'Start'}
                                    </button>
                                </div>

                                {/* Task 3: Set Preferences */}
                                <div className="flex items-start gap-2 p-3 bg-white rounded-lg border border-gray-200">
                                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 font-bold flex items-center justify-center text-xs">
                                        3
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h4 className="font-semibold text-gray-900 text-sm">Set Job Preferences</h4>
                                        <p className="text-xs text-gray-600">Tell us what kind of jobs you're looking for.</p>
                                    </div>
                                    <button
                                        onClick={() => setActiveModal('preferences')}
                                        disabled={onboardingProgress!.steps.preferences}
                                        className={`flex-shrink-0 px-3 py-1 rounded-lg font-medium text-xs transition-all ${onboardingProgress!.steps.preferences
                                            ? 'bg-green-100 text-green-700 cursor-not-allowed'
                                            : 'bg-blue-600 text-white hover:bg-blue-700'
                                            }`}
                                    >
                                        {onboardingProgress!.steps.preferences ? '✓' : 'Start'}
                                    </button>
                                </div>

                                {/* Task 4: Add Certifications */}
                                <div className="flex items-start gap-2 p-3 bg-white rounded-lg border border-gray-200">
                                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 font-bold flex items-center justify-center text-xs">
                                        4
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h4 className="font-semibold text-gray-900 text-sm">Add Certifications</h4>
                                        <p className="text-xs text-gray-600">Add your food safety and other certifications.</p>
                                    </div>
                                    <button
                                        onClick={() => setActiveModal('certifications')}
                                        disabled={onboardingProgress!.steps.certifications}
                                        className={`flex-shrink-0 px-3 py-1 rounded-lg font-medium text-xs transition-all ${onboardingProgress!.steps.certifications
                                            ? 'bg-green-100 text-green-700 cursor-not-allowed'
                                            : 'bg-blue-600 text-white hover:bg-blue-700'
                                            }`}
                                    >
                                        {onboardingProgress!.steps.certifications ? '✓' : 'Start'}
                                    </button>
                                </div>

                                {/* Task 5: Upload Documents */}
                                <div className="flex items-start gap-2 p-3 bg-white rounded-lg border border-gray-200">
                                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 font-bold flex items-center justify-center text-xs">
                                        5
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h4 className="font-semibold text-gray-900 text-sm">Upload Your Resume</h4>
                                        <p className="text-xs text-gray-600">Upload your resume to improve job matches.</p>
                                    </div>
                                    <button
                                        onClick={() => setActiveModal('resume')}
                                        disabled={onboardingProgress!.steps.documents}
                                        className={`flex-shrink-0 px-3 py-1 rounded-lg font-medium text-xs transition-all ${onboardingProgress!.steps.documents
                                            ? 'bg-green-100 text-green-700 cursor-not-allowed'
                                            : 'bg-blue-600 text-white hover:bg-blue-700'
                                            }`}
                                    >
                                        {onboardingProgress!.steps.documents ? '✓' : 'Start'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </>
            )}

            {/* Welcome Header & Onboarding Checklist (Employers Only) */}
            {user?.role === 'employer' && employerOnboardingProgress && !employerOnboardingProgress.onboarding_complete && (
                <>
                    {/* Welcome Header with Progress */}
                    <div className="px-6 py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white">
                        <div className="flex items-start gap-4">
                            <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
                                <MessageSquare className="w-6 h-6" />
                            </div>
                            <div className="flex-1">
                                <h2 className="text-xl font-bold mb-1">Welcome to SmartServe!</h2>
                                <p className="text-green-100 text-sm">Complete your profile to start hiring top talent</p>
                            </div>
                            <button
                                onClick={() => setIsChecklistExpanded(!isChecklistExpanded)}
                                className="px-3 py-1 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors"
                            >
                                {isChecklistExpanded ? 'Hide Checklist' : 'Show Checklist'}
                            </button>
                        </div>

                        {/* Progress Bar */}
                        <div className="mt-3 space-y-2">
                            <div className="flex items-center justify-between text-xs">
                                <span className="font-semibold">Your Progress</span>
                                <span className="font-medium">
                                    {Object.values(employerOnboardingProgress!.steps).filter(Boolean).length} of 2 completed
                                </span>
                            </div>
                            <div className="relative w-full h-2 bg-green-800/30 rounded-full overflow-hidden">
                                <div
                                    className="absolute top-0 left-0 h-full bg-white rounded-full transition-all duration-500"
                                    style={{
                                        width: `${(Object.values(employerOnboardingProgress!.steps).filter(Boolean).length / 2) * 100}%`
                                    }}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Collapsible Getting Started Checklist */}
                    {isChecklistExpanded && (
                        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 max-h-96 overflow-y-auto">
                            <h3 className="text-base font-bold text-gray-900 mb-2">Getting Started Checklist</h3>
                            <p className="text-xs text-gray-600 mb-3">Complete these tasks to optimize your recruitment experience</p>

                            <div className="space-y-2">
                                {/* Task 1: Complete Company Profile */}
                                <div className="flex items-start gap-2 p-3 bg-white rounded-lg border border-gray-200">
                                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 text-green-600 font-bold flex items-center justify-center text-xs">
                                        1
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h4 className="font-semibold text-gray-900 text-sm">Complete Company Profile</h4>
                                        <p className="text-xs text-gray-600">Add your company information, industry, and location to build trust with candidates.</p>
                                    </div>
                                    <button
                                        onClick={() => setActiveEmployerModal('company_profile')}
                                        disabled={employerOnboardingProgress!.steps.company_profile}
                                        className={`flex-shrink-0 px-3 py-1 rounded-lg font-medium text-xs transition-all ${employerOnboardingProgress!.steps.company_profile
                                            ? 'bg-green-100 text-green-700 cursor-not-allowed'
                                            : 'bg-green-600 text-white hover:bg-green-700'
                                            }`}
                                    >
                                        {employerOnboardingProgress!.steps.company_profile ? '✓' : 'Start'}
                                    </button>
                                </div>

                                {/* Task 2: Set Hiring Preferences */}
                                <div className="flex items-start gap-2 p-3 bg-white rounded-lg border border-gray-200">
                                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 text-green-600 font-bold flex items-center justify-center text-xs">
                                        2
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h4 className="font-semibold text-gray-900 text-sm">Set Hiring Preferences</h4>
                                        <p className="text-xs text-gray-600">Define the roles you typically hire for with locations, shifts, and salary ranges.</p>
                                    </div>
                                    <button
                                        onClick={() => setActiveEmployerModal('hiring_preferences')}
                                        disabled={employerOnboardingProgress!.steps.hiring_preferences}
                                        className={`flex-shrink-0 px-3 py-1 rounded-lg font-medium text-xs transition-all ${employerOnboardingProgress!.steps.hiring_preferences
                                            ? 'bg-green-100 text-green-700 cursor-not-allowed'
                                            : 'bg-green-600 text-white hover:bg-green-700'
                                            }`}
                                    >
                                        {employerOnboardingProgress!.steps.hiring_preferences ? '✓' : 'Start'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </>
            )}

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-center px-4">
                        <div className="p-4 bg-primary-50 rounded-full mb-4">
                            <MessageSquare className="w-12 h-12 text-primary-600" />
                        </div>
                        <h3 className="text-xl font-semibold text-slate-900 mb-2">
                            Welcome to AI Chat
                        </h3>
                        <p className="text-slate-600 max-w-md mb-6">
                            {getWelcomeMessage()}
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
                            {user?.role === 'employee' ? (
                                <>
                                    <button
                                        onClick={() => setInput('Find chef jobs in Mumbai')}
                                        className="p-3 text-left bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors"
                                    >
                                        <p className="font-medium text-slate-900">Find Jobs</p>
                                        <p className="text-sm text-slate-600">Search for job opportunities</p>
                                    </button>
                                    <button
                                        onClick={() => setInput("What's my application status?")}
                                        className="p-3 text-left bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors"
                                    >
                                        <p className="font-medium text-slate-900">Check Applications</p>
                                        <p className="text-sm text-slate-600">View your application status</p>
                                    </button>
                                    <button
                                        onClick={() => setInput('Analyze my profile')}
                                        className="p-3 text-left bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors"
                                    >
                                        <p className="font-medium text-slate-900">Profile Analysis</p>
                                        <p className="text-sm text-slate-600">Get insights on your profile</p>
                                    </button>
                                    <button
                                        onClick={() => setInput('Show me my best job matches')}
                                        className="p-3 text-left bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors"
                                    >
                                        <p className="font-medium text-slate-900">Best Matches</p>
                                        <p className="text-sm text-slate-600">Find jobs that match your skills</p>
                                    </button>
                                </>
                            ) : (
                                <>
                                    <button
                                        onClick={() => setInput('Post a chef job in Mumbai, salary 50k-80k')}
                                        className="p-3 text-left bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors"
                                    >
                                        <p className="font-medium text-slate-900">Post a Job</p>
                                        <p className="text-sm text-slate-600">Create a new job posting</p>
                                    </button>
                                    <button
                                        onClick={() => setInput('Find candidates for chef position')}
                                        className="p-3 text-left bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors"
                                    >
                                        <p className="font-medium text-slate-900">Find Candidates</p>
                                        <p className="text-sm text-slate-600">Search for qualified candidates</p>
                                    </button>
                                    <button
                                        onClick={() => setInput('Show all applications')}
                                        className="p-3 text-left bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors"
                                    >
                                        <p className="font-medium text-slate-900">View Applications</p>
                                        <p className="text-sm text-slate-600">Review job applications</p>
                                    </button>
                                    <button
                                        onClick={() => setInput('I need 3 waiters and 2 cooks')}
                                        className="p-3 text-left bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors"
                                    >
                                        <p className="font-medium text-slate-900">Bulk Hiring</p>
                                        <p className="text-sm text-slate-600">Hire multiple positions</p>
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                )}

                {messages.map((message, index) => (
                    <div
                        key={index}
                        className={clsx(
                            'flex',
                            message.role === 'user' ? 'justify-end' : 'justify-start'
                        )}
                    >
                        <div
                            className={clsx(
                                'max-w-[80%] rounded-lg px-4 py-3',
                                message.role === 'user'
                                    ? 'bg-primary-600 text-white'
                                    : 'bg-slate-100 text-slate-900'
                            )}
                        >
                            <p className="whitespace-pre-wrap break-words">{message.content}</p>
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-100 rounded-lg px-4 py-3">
                            <Loader2 className="w-5 h-5 animate-spin text-slate-600" />
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-200">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type your message..."
                        className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || isLoading}
                        className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                    >
                        {isLoading ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <Send className="w-5 h-5" />
                        )}
                    </button>
                </div>
            </form>

            {/* Onboarding Modals */}
            {activeModal && user?.id && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6">
                            <h2 className="text-2xl font-bold text-gray-900 mb-4">
                                {activeModal === 'profile' && 'Complete Your Profile'}
                                {activeModal === 'skills' && 'Add Your Skills'}
                                {activeModal === 'work_history' && 'Work Experience'}
                                {activeModal === 'preferences' && 'Set Job Preferences'}
                                {activeModal === 'certifications' && 'Add Certifications'}
                                {activeModal === 'resume' && 'Upload Your Resume'}
                            </h2>

                            {activeModal === 'profile' && (
                                <ProfileForm
                                    employeeId={user.profileId || user.id}  // Use profileId if available
                                    onComplete={handleFormComplete}
                                    onCancel={() => setActiveModal(null)}
                                />
                            )}
                            {activeModal === 'skills' && (
                                <SkillsForm
                                    employeeId={user.profileId || user.id}  // Use profileId if available
                                    onComplete={handleFormComplete}
                                    onCancel={() => setActiveModal(null)}
                                />
                            )}
                            {activeModal === 'work_history' && (
                                <WorkHistoryForm
                                    employeeId={user.profileId || user.id}
                                    onComplete={handleFormComplete}
                                    onCancel={() => setActiveModal(null)}
                                />
                            )}
                            {activeModal === 'preferences' && (
                                <PreferencesForm
                                    employeeId={user.profileId || user.id}  // Use profileId if available
                                    onComplete={handleFormComplete}
                                    onCancel={() => setActiveModal(null)}
                                />
                            )}
                            {activeModal === 'certifications' && (
                                <CertificationsForm
                                    employeeId={user.profileId || user.id}  // Use profileId if available
                                    onComplete={handleFormComplete}
                                    onCancel={() => setActiveModal(null)}
                                />
                            )}
                            {activeModal === 'resume' && (
                                <ResumeUploadForm
                                    employeeId={user.profileId || user.id}  // Use profileId if available
                                    onComplete={handleFormComplete}
                                    onCancel={() => setActiveModal(null)}
                                />
                            )}
                        </div>
                    </div>
                </div>
            )}


            {/* Employer Onboarding Modals */}
            {
                activeEmployerModal && user?.id && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                            <div className="p-6">
                                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                                    {activeEmployerModal === 'company_profile' && 'Complete Company Profile'}
                                    {activeEmployerModal === 'hiring_preferences' && 'Set Hiring Preferences'}
                                </h2>

                                {activeEmployerModal === 'company_profile' && (
                                    <CompanyProfileForm
                                        onComplete={handleEmployerFormComplete}
                                        onCancel={() => setActiveEmployerModal(null)}
                                    />
                                )}
                                {activeEmployerModal === 'hiring_preferences' && (
                                    <HiringPreferencesForm
                                        onComplete={handleEmployerFormComplete}
                                        onCancel={() => setActiveEmployerModal(null)}
                                    />
                                )}
                            </div>
                        </div>
                    </div>
                )
            }

            {/* Bulk Hire Modal */}
            <BulkHireModal
                isOpen={isBulkHireModalOpen}
                onClose={() => setIsBulkHireModalOpen(false)}
                onSuccess={(result) => {
                    // Format multi-job results for chat
                    let successMessage = `🎯 Bulk Hiring Complete!\n\n`

                    result.resultsByJob.forEach(jobResult => {
                        successMessage += `📋 ${jobResult.jobTitle}\n`
                        successMessage += `Positions Filled: ${jobResult.candidates.length}\n`
                        jobResult.candidates.forEach(c => {
                            const scoreText = c.score ? ` (Score: ${c.score}/100)` : ''
                            successMessage += `✓ ${c.name}${scoreText}\n`
                        })
                        successMessage += `\n`
                    })

                    successMessage += `📊 Total: ${result.totalHired} candidates hired across ${result.resultsByJob.length} jobs\n`
                    successMessage += `📧 Offer letters sent to all candidates`

                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: successMessage,
                        timestamp: new Date()
                    }])
                }}
            />
        </div >
    )
}
