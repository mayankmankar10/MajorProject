import React, { useState, useEffect } from 'react'
import { CheckCircle2, Loader2, MessageSquare, Building2, ArrowRight } from 'lucide-react'
import { apiClient } from '@/services/api'
import clsx from 'clsx'
import { useNavigate } from 'react-router-dom'

interface OnboardingTask {
    id: number
    title: string
    description: string
    completed: boolean
    order: number
    key: 'company_profile' | 'hiring_preferences'
}

export const EmployerOnboarding: React.FC = () => {
    const navigate = useNavigate()
    const [tasks, setTasks] = useState<OnboardingTask[]>([])
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        loadOnboardingStatus()
    }, [])

    const loadOnboardingStatus = async () => {
        try {
            setIsLoading(true)
            const response = await apiClient.getEmployerOnboardingStatus()

            // Create task list based on completion status
            setTasks([
                {
                    id: 1,
                    title: 'Complete Company Profile',
                    description: 'Add your company information, industry, and location to build trust with candidates.',
                    completed: response.steps.company_profile || false,
                    order: 1,
                    key: 'company_profile'
                },
                {
                    id: 2,
                    title: 'Set Hiring Preferences',
                    description: 'Define the roles you typically hire for with locations, shifts, and salary ranges.',
                    completed: response.steps.hiring_preferences || false,
                    order: 2,
                    key: 'hiring_preferences'
                }
            ])
        } catch (error) {
            console.error('Failed to load onboarding status:', error)
            setTasks([
                {
                    id: 1,
                    title: 'Complete Company Profile',
                    description: 'Add your company information, industry, and location to build trust with candidates.',
                    completed: false,
                    order: 1,
                    key: 'company_profile'
                },
                {
                    id: 2,
                    title: 'Set Hiring Preferences',
                    description: 'Define the roles you typically hire for with locations, shifts, and salary ranges.',
                    completed: false,
                    order: 2,
                    key: 'hiring_preferences'
                }
            ])
        } finally {
            setIsLoading(false)
        }
    }

    const completedCount = tasks.filter(t => t.completed).length
    const totalCount = tasks.length
    const progress = totalCount > 0 ? (completedCount / totalCount) * 100 : 0

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-96">
                <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
            </div>
        )
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            {/* Header */}
            <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg p-8 text-white">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-3 bg-white/20 rounded-lg">
                        <Building2 className="w-8 h-8" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold">Welcome to SmartServe!</h1>
                        <p className="text-green-100 mt-1">Let's set up your employer profile to start hiring</p>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="mt-6">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">Your Progress</span>
                        <span className="text-sm font-medium">{completedCount} of {totalCount} completed</span>
                    </div>
                    <div className="w-full bg-green-800/30 rounded-full h-3">
                        <div
                            className="bg-white rounded-full h-3 transition-all duration-500"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>

                <div className="mt-6">
                    <button
                        onClick={() => navigate('/employer/chat')}
                        className="px-6 py-2.5 bg-white text-green-700 font-semibold rounded-lg hover:bg-green-50 transition-colors flex items-center gap-2"
                    >
                        <MessageSquare className="w-5 h-5" />
                        <span>Continue in Chat</span>
                        <ArrowRight className="w-4 h-4 ml-1" />
                    </button>
                </div>
            </div>

            {/* Completion Message */}
            {completedCount === totalCount && totalCount > 0 && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                    <div className="flex items-start gap-3">
                        <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <h3 className="text-lg font-semibold text-green-900 mb-1">
                                🎉 Congratulations! You're all set!
                            </h3>
                            <p className="text-green-700">
                                You've completed your profile setup. You can now post jobs and start receiving qualified applications!
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Tasks List */}
            <div className="bg-white rounded-lg shadow-sm border border-slate-200">
                <div className="p-6 border-b border-slate-200">
                    <h2 className="text-xl font-semibold text-slate-900">Getting Started Checklist</h2>
                    <p className="text-slate-600 mt-1">Complete these tasks in the AI Chat to optimize your hiring experience</p>
                </div>

                <div className="divide-y divide-slate-200">
                    {tasks.map((task, index) => (
                        <div
                            key={task.id}
                            className={clsx(
                                'p-6 transition-colors',
                                task.completed ? 'bg-slate-50' : 'bg-white hover:bg-slate-50'
                            )}
                        >
                            <div className="flex items-start gap-4">
                                {/* Task Number/Icon */}
                                <div className="flex-shrink-0">
                                    {task.completed ? (
                                        <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                                            <CheckCircle2 className="w-6 h-6 text-green-600" />
                                        </div>
                                    ) : (
                                        <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center">
                                            <span className="text-lg font-semibold text-slate-600">{index + 1}</span>
                                        </div>
                                    )}
                                </div>

                                {/* Task Content */}
                                <div className="flex-1 min-w-0">
                                    <h3 className={clsx(
                                        'text-lg font-semibold mb-1',
                                        task.completed ? 'text-slate-500 line-through' : 'text-slate-900'
                                    )}>
                                        {task.title}
                                    </h3>
                                    <p className={clsx(
                                        'text-sm',
                                        task.completed ? 'text-slate-400' : 'text-slate-600'
                                    )}>
                                        {task.description}
                                    </p>
                                </div>

                                <div className="flex-shrink-0">
                                    {!task.completed && (
                                        <button
                                            onClick={() => navigate('/employer/chat')}
                                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
                                        >
                                            <MessageSquare className="w-4 h-4" />
                                            <span>Complete in Chat</span>
                                        </button>
                                    )}
                                    {task.completed && (
                                        <span className="text-sm font-medium text-green-600">
                                            ✓ Completed
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
