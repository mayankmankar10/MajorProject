import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
    CheckCircle2,
    Circle,
    Clock,
    MessageSquare,
    User,
    Briefcase,
    Settings,
    Award,
    FileText,
    ArrowRight,
    Download,
    Eye,
    ChevronDown,
    ChevronUp
} from 'lucide-react'
import { Card } from '@/components'
import { useAuthStore } from '@/stores/useAuthStore'
import { apiClient } from '@/services/api'

interface StepData {
    [key: string]: any
}

interface OnboardingProgressData {
    employee_id: number
    current_step: string
    is_complete: boolean
    completion_percentage: number
    steps: {
        profile: boolean
        skills: boolean
        preferences: boolean
        certifications: boolean
        documents: boolean
    }
    started_at: string | null
    completed_at: string | null
    last_updated: string | null
    profile_data?: StepData
    skills_data?: StepData
    preferences_data?: StepData
    certifications_data?: StepData
    documents_data?: StepData
}

interface OnboardingStep {
    id: string
    title: string
    description: string
    icon: React.ElementType
    completed: boolean
    data?: StepData
}

export const OnboardingProgress: React.FC = () => {
    const { user } = useAuthStore()
    const [progress, setProgress] = useState<OnboardingProgressData | null>(null)
    const [loading, setLoading] = useState(true)
    const [expandedStep, setExpandedStep] = useState<string | null>(null)
    const [downloadingResume, setDownloadingResume] = useState(false)

    useEffect(() => {
        fetchProgress()
    }, [])

    const fetchProgress = async () => {
        try {
            const employeeId = user?.profileId || user?.id || 1  // Use profileId if available
            const data = await apiClient.getOnboardingProgress(employeeId)
            setProgress(data)
        } catch (error) {
            console.error('Failed to fetch onboarding progress:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleDownloadResume = async () => {
        if (!user?.id) return

        try {
            setDownloadingResume(true)
            const employeeId = user.profileId || user.id
            const blob = await apiClient.downloadEmployeeResume(employeeId)

            // Detect file type from blob
            const isPDF = blob.type === 'application/pdf'
            const extension = isPDF ? 'pdf' : 'txt'
            const fileName = `${progress?.profile_data?.full_name?.replace(/ /g, '_') || 'Employee'}_Resume.${extension}`

            const url = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.download = fileName
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            window.URL.revokeObjectURL(url)
        } catch (error: any) {
            console.error('Failed to download resume:', error)
            const errorMessage = error.response?.status === 404
                ? 'No resume available for download'
                : 'Failed to download resume. Please try again.'
            alert(errorMessage)
        } finally {
            setDownloadingResume(false)
        }
    }

    const toggleStepExpansion = (stepId: string) => {
        setExpandedStep(expandedStep === stepId ? null : stepId)
    }

    const renderStepData = (data: StepData | undefined) => {
        if (!data) return null

        const renderValue = (key: string, value: any) => {
            if (value === null || value === undefined) return null
            if (Array.isArray(value)) {
                if (value.length === 0) return null
                return (
                    <div key={key} className="text-sm">
                        <span className="font-medium text-gray-700">{formatKey(key)}:</span>
                        <ul className="ml-4 mt-1 list-disc list-inside">
                            {value.map((item, idx) => (
                                <li key={idx} className="text-gray-600">
                                    {typeof item === 'object' ? JSON.stringify(item) : String(item)}
                                </li>
                            ))}
                        </ul>
                    </div>
                )
            }
            if (typeof value === 'boolean') {
                return (
                    <div key={key} className="text-sm flex items-center gap-2">
                        <span className="font-medium text-gray-700">{formatKey(key)}:</span>
                        <span className={value ? 'text-green-600' : 'text-gray-400'}>
                            {value ? '✓ Yes' : '✗ No'}
                        </span>
                    </div>
                )
            }
            return (
                <div key={key} className="text-sm">
                    <span className="font-medium text-gray-700">{formatKey(key)}:</span>
                    <span className="text-gray-600 ml-2">{String(value)}</span>
                </div>
            )
        }

        return (
            <div className="mt-3 space-y-2 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <h4 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                    <Eye className="w-4 h-4" />
                    Entered Information
                </h4>
                {Object.entries(data).map(([key, value]) => renderValue(key, value))}
            </div>
        )
    }

    const formatKey = (key: string): string => {
        return key
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ')
    }

    const steps: OnboardingStep[] = [
        {
            id: 'profile',
            title: 'Profile Information',
            description: 'Basic details and contact information',
            icon: User,
            completed: progress?.steps.profile || false,
            data: progress?.profile_data
        },
        {
            id: 'skills',
            title: 'Skills & Experience',
            description: 'Work history and expertise',
            icon: Briefcase,
            completed: progress?.steps.skills || false,
            data: progress?.skills_data
        },
        {
            id: 'preferences',
            title: 'Work Preferences',
            description: 'Preferred shifts, cuisine types, and roles',
            icon: Settings,
            completed: progress?.steps.preferences || false,
            data: progress?.preferences_data
        },
        {
            id: 'certifications',
            title: 'Certifications',
            description: 'Food safety and other certifications',
            icon: Award,
            completed: progress?.steps.certifications || false,
            data: progress?.certifications_data
        },
        {
            id: 'documents',
            title: 'Documents',
            description: 'Resume and required documents',
            icon: FileText,
            completed: progress?.steps.documents || false,
            data: progress?.documents_data
        }
    ]

    const currentStepIndex = steps.findIndex(s => s.id === progress?.current_step)
    const completionPercentage = progress?.completion_percentage || 0

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading your progress...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="max-w-4xl mx-auto">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-8"
            >
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Your Onboarding Progress</h1>
                <p className="text-gray-600">Track your profile completion and review entered information</p>
            </motion.div>

            {/* Progress Overview Card */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
            >
                <Card padding="lg" className="mb-8">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h2 className="text-2xl font-bold text-gray-900">
                                {completionPercentage}% Complete
                            </h2>
                            <p className="text-gray-600 mt-1">
                                {progress?.is_complete
                                    ? '🎉 All done! You can now apply to jobs'
                                    : `${steps.filter(s => s.completed).length} of ${steps.length} steps completed`
                                }
                            </p>
                            {progress?.last_updated && (
                                <p className="text-xs text-gray-500 mt-1">
                                    Last updated: {new Date(progress.last_updated).toLocaleDateString()}
                                </p>
                            )}
                        </div>
                        <div className="flex gap-3">
                            {progress?.documents_data?.has_resume && (
                                <button
                                    onClick={handleDownloadResume}
                                    disabled={downloadingResume}
                                    className="inline-flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-green-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <Download className="w-5 h-5" />
                                    {downloadingResume ? 'Downloading...' : 'Download Resume'}
                                </button>
                            )}
                            {!progress?.is_complete && (
                                <Link
                                    to="/employee/chat"
                                    className="inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-700 transition-all shadow-lg hover:shadow-xl hover:scale-105"
                                >
                                    <MessageSquare className="w-5 h-5" />
                                    Continue in Chat
                                    <ArrowRight className="w-5 h-5" />
                                </Link>
                            )}
                        </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="relative w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${completionPercentage}%` }}
                            transition={{ duration: 1, ease: "easeOut" }}
                            className="absolute top-0 left-0 h-full bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full"
                        />
                    </div>
                </Card>
            </motion.div>

            {/* Steps List with Detailed Data */}
            <div className="space-y-4">
                {steps.map((step, index) => {
                    const isActive = index === currentStepIndex
                    const isExpanded = expandedStep === step.id
                    const hasData = step.completed && step.data

                    return (
                        <motion.div
                            key={step.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.2 + index * 0.1 }}
                        >
                            <Card
                                padding="lg"
                                className={`transition-all ${step.completed
                                    ? 'border-green-200 bg-green-50/50'
                                    : isActive
                                        ? 'border-primary-200 bg-primary-50/50 shadow-md'
                                        : 'border-gray-200'
                                    }`}
                            >
                                <div className="flex items-start gap-4">
                                    {/* Icon */}
                                    <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center ${step.completed
                                        ? 'bg-green-100'
                                        : isActive
                                            ? 'bg-primary-100'
                                            : 'bg-gray-100'
                                        }`}>
                                        {step.completed ? (
                                            <CheckCircle2 className="w-6 h-6 text-green-600" />
                                        ) : isActive ? (
                                            <Clock className="w-6 h-6 text-primary-600" />
                                        ) : (
                                            <Circle className="w-6 h-6 text-gray-400" />
                                        )}
                                    </div>

                                    {/* Content */}
                                    <div className="flex-1">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2 mb-1">
                                                <step.icon className={`w-5 h-5 ${step.completed
                                                    ? 'text-green-600'
                                                    : isActive
                                                        ? 'text-primary-600'
                                                        : 'text-gray-400'
                                                    }`} />
                                                <h3 className={`text-lg font-semibold ${step.completed
                                                    ? 'text-green-900'
                                                    : isActive
                                                        ? 'text-primary-900'
                                                        : 'text-gray-700'
                                                    }`}>
                                                    {step.title}
                                                </h3>
                                            </div>
                                            {hasData && (
                                                <button
                                                    onClick={() => toggleStepExpansion(step.id)}
                                                    className="text-gray-500 hover:text-gray-700 transition-colors"
                                                >
                                                    {isExpanded ? (
                                                        <ChevronUp className="w-5 h-5" />
                                                    ) : (
                                                        <ChevronDown className="w-5 h-5" />
                                                    )}
                                                </button>
                                            )}
                                        </div>
                                        <p className={`text-sm ${step.completed
                                            ? 'text-green-700'
                                            : isActive
                                                ? 'text-primary-700'
                                                : 'text-gray-600'
                                            }`}>
                                            {step.description}
                                        </p>

                                        {/* Status Badge */}
                                        <div className="mt-3">
                                            {step.completed ? (
                                                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                                                    <CheckCircle2 className="w-3 h-3" />
                                                    Completed
                                                </span>
                                            ) : isActive ? (
                                                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-700">
                                                    <Clock className="w-3 h-3" />
                                                    In Progress
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                                                    <Circle className="w-3 h-3" />
                                                    Pending
                                                </span>
                                            )}
                                        </div>

                                        {/* Expanded Step Data */}
                                        {isExpanded && hasData && renderStepData(step.data)}
                                    </div>
                                </div>
                            </Card>
                        </motion.div>
                    )
                })}
            </div>

            {/* Completion Message */}
            {progress?.is_complete && (
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.8 }}
                    className="mt-8"
                >
                    <Card padding="lg" className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
                        <div className="text-center">
                            <div className="text-6xl mb-4">🎉</div>
                            <h2 className="text-2xl font-bold text-green-900 mb-2">
                                Onboarding Complete!
                            </h2>
                            <p className="text-green-700 mb-6">
                                Great job! You're all set to start applying to restaurant jobs.
                            </p>
                            <div className="flex gap-4 justify-center">
                                <Link
                                    to="/employee/jobs"
                                    className="inline-flex items-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition-all shadow-lg hover:shadow-xl"
                                >
                                    <Briefcase className="w-5 h-5" />
                                    Browse Jobs
                                </Link>
                                {progress?.documents_data?.has_resume && (
                                    <button
                                        onClick={handleDownloadResume}
                                        disabled={downloadingResume}
                                        className="inline-flex items-center gap-2 bg-white text-green-600 border-2 border-green-600 px-6 py-3 rounded-lg font-semibold hover:bg-green-50 transition-all shadow-lg hover:shadow-xl disabled:opacity-50"
                                    >
                                        <Download className="w-5 h-5" />
                                        Download Resume
                                    </button>
                                )}
                            </div>
                        </div>
                    </Card>
                </motion.div>
            )}
        </div>
    )
}
