import React, { useState, useEffect } from 'react'
import { CheckCircle2, Loader2, FileText, Award } from 'lucide-react'
import { apiClient } from '@/services/api'
import clsx from 'clsx'

interface OnboardingTask {
    id: number
    title: string
    description: string
    completed: boolean
    order: number
}

export const Onboarding: React.FC = () => {
    const [tasks, setTasks] = useState<OnboardingTask[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [completingTaskId, setCompletingTaskId] = useState<number | null>(null)

    useEffect(() => {
        loadOnboardingTasks()
    }, [])

    const loadOnboardingTasks = async () => {
        try {
            setIsLoading(true)
            const response = await apiClient.getOnboardingTasks()
            setTasks(response.tasks || [])
        } catch (error) {
            console.error('Failed to load onboarding tasks:', error)
            // Set default tasks if API fails
            setTasks([
                {
                    id: 1,
                    title: 'Complete Your Profile',
                    description: 'Add your personal information, skills, and experience to help employers find you.',
                    completed: false,
                    order: 1
                },
                {
                    id: 2,
                    title: 'Upload Your Resume',
                    description: 'Upload your resume to automatically populate your profile and improve job matches.',
                    completed: false,
                    order: 2
                },
                {
                    id: 3,
                    title: 'Set Job Preferences',
                    description: 'Tell us what kind of jobs you\'re looking for, preferred locations, and salary expectations.',
                    completed: false,
                    order: 3
                },
                {
                    id: 4,
                    title: 'Browse Available Jobs',
                    description: 'Explore job listings that match your profile and skills.',
                    completed: false,
                    order: 4
                },
                {
                    id: 5,
                    title: 'Apply to Your First Job',
                    description: 'Submit your first job application and start your journey!',
                    completed: false,
                    order: 5
                }
            ])
        } finally {
            setIsLoading(false)
        }
    }

    const handleCompleteTask = async (taskId: number) => {
        try {
            setCompletingTaskId(taskId)
            await apiClient.completeOnboardingTask(taskId)

            // Update local state
            setTasks(prev =>
                prev.map(task =>
                    task.id === taskId ? { ...task, completed: true } : task
                )
            )
        } catch (error) {
            console.error('Failed to complete task:', error)
            // Still mark as complete locally for demo purposes
            setTasks(prev =>
                prev.map(task =>
                    task.id === taskId ? { ...task, completed: true } : task
                )
            )
        } finally {
            setCompletingTaskId(null)
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
            <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg p-8 text-white">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-3 bg-white/20 rounded-lg">
                        <Award className="w-8 h-8" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold">Welcome to SmartServe!</h1>
                        <p className="text-primary-100 mt-1">Let's get you started on your job search journey</p>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="mt-6">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">Your Progress</span>
                        <span className="text-sm font-medium">{completedCount} of {totalCount} completed</span>
                    </div>
                    <div className="w-full bg-white/20 rounded-full h-3">
                        <div
                            className="bg-white rounded-full h-3 transition-all duration-500"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
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
                                You've completed all onboarding tasks. You're now ready to explore jobs and start applying!
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Tasks List */}
            <div className="bg-white rounded-lg shadow-sm border border-slate-200">
                <div className="p-6 border-b border-slate-200">
                    <h2 className="text-xl font-semibold text-slate-900">Getting Started Checklist</h2>
                    <p className="text-slate-600 mt-1">Complete these tasks to optimize your job search experience</p>
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

                                {/* Action Button */}
                                <div className="flex-shrink-0">
                                    {!task.completed && (
                                        <button
                                            onClick={() => handleCompleteTask(task.id)}
                                            disabled={completingTaskId === task.id}
                                            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                                        >
                                            {completingTaskId === task.id ? (
                                                <>
                                                    <Loader2 className="w-4 h-4 animate-spin" />
                                                    <span>Completing...</span>
                                                </>
                                            ) : (
                                                <span>Mark Complete</span>
                                            )}
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

            {/* Help Section */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <div className="flex items-start gap-3">
                    <FileText className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div>
                        <h3 className="text-lg font-semibold text-blue-900 mb-1">Need Help?</h3>
                        <p className="text-blue-700 mb-3">
                            Our AI assistant can help you complete these tasks and answer any questions you have.
                        </p>
                        <a
                            href="/employee/chat"
                            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            Chat with AI Assistant
                        </a>
                    </div>
                </div>
            </div>
        </div>
    )
}
