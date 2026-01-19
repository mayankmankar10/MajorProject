import React, { useState, useEffect } from 'react'
import { Calendar, Clock, MapPin, Video, Phone, Loader2, Plus } from 'lucide-react'
import clsx from 'clsx'

interface Interview {
    id: number
    candidate_name: string
    job_title: string
    scheduled_time: string
    location?: string
    interview_type: 'in_person' | 'video' | 'phone'
    status: 'scheduled' | 'completed' | 'cancelled'
    notes?: string
}

export const Interviews: React.FC = () => {
    const [interviews, setInterviews] = useState<Interview[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)
    const [filter, setFilter] = useState<'all' | 'upcoming' | 'completed'>('upcoming')

    useEffect(() => {
        loadInterviews()
    }, [])

    const loadInterviews = async () => {
        try {
            setIsLoading(true)
            const token = localStorage.getItem('auth_token')
            if (!token) {
                throw new Error('Please log in to view interviews')
            }

            const response = await fetch('/api/interviews', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Unauthorized - Please log in again')
                }
                throw new Error(`Failed to load interviews: ${response.statusText}`)
            }

            const data = await response.json()
            setInterviews(data || [])
        } catch (err: any) {
            console.error('Failed to load interviews:', err)
            setError(err)
            setInterviews([])
        } finally {
            setIsLoading(false)
        }
    }

    const getInterviewTypeIcon = (type: string) => {
        switch (type) {
            case 'video':
                return <Video className="w-4 h-4" />
            case 'phone':
                return <Phone className="w-4 h-4" />
            default:
                return <MapPin className="w-4 h-4" />
        }
    }

    const getInterviewTypeLabel = (type: string) => {
        switch (type) {
            case 'video':
                return 'Video Call'
            case 'phone':
                return 'Phone Call'
            default:
                return 'In Person'
        }
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed':
                return 'bg-green-100 text-green-700 border-green-200'
            case 'cancelled':
                return 'bg-red-100 text-red-700 border-red-200'
            default:
                return 'bg-blue-100 text-blue-700 border-blue-200'
        }
    }

    const formatDate = (dateString: string) => {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        })
    }

    const formatTime = (dateString: string) => {
        const date = new Date(dateString)
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    const filteredInterviews = interviews.filter(interview => {
        if (filter === 'all') return true
        if (filter === 'upcoming') {
            return interview.status === 'scheduled' && new Date(interview.scheduled_time) > new Date()
        }
        if (filter === 'completed') {
            return interview.status === 'completed'
        }
        return true
    })

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-96">
                <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
            </div>
        )
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
                <p className="text-red-800">{error.message || 'Failed to load interviews. Please try again.'}</p>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">Interviews</h1>
                    <p className="text-slate-600 mt-1">Manage and track your interview schedule</p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                    <Plus className="w-5 h-5" />
                    Schedule Interview
                </button>
            </div>

            {/* Filters */}
            <div className="flex gap-2">
                <button
                    onClick={() => setFilter('all')}
                    className={clsx(
                        'px-4 py-2 rounded-lg font-medium transition-colors',
                        filter === 'all'
                            ? 'bg-primary-600 text-white'
                            : 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50'
                    )}
                >
                    All Interviews
                </button>
                <button
                    onClick={() => setFilter('upcoming')}
                    className={clsx(
                        'px-4 py-2 rounded-lg font-medium transition-colors',
                        filter === 'upcoming'
                            ? 'bg-primary-600 text-white'
                            : 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50'
                    )}
                >
                    Upcoming
                </button>
                <button
                    onClick={() => setFilter('completed')}
                    className={clsx(
                        'px-4 py-2 rounded-lg font-medium transition-colors',
                        filter === 'completed'
                            ? 'bg-primary-600 text-white'
                            : 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50'
                    )}
                >
                    Completed
                </button>
            </div>

            {/* Interviews List */}
            {filteredInterviews.length === 0 ? (
                <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-12 text-center">
                    <Calendar className="w-16 h-16 text-slate-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-slate-900 mb-2">No interviews found</h3>
                    <p className="text-slate-600 mb-6">
                        {filter === 'upcoming'
                            ? "You don't have any upcoming interviews scheduled."
                            : filter === 'completed'
                                ? "You haven't completed any interviews yet."
                                : "You don't have any interviews scheduled."}
                    </p>
                    <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                        Schedule Your First Interview
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-4">
                    {filteredInterviews.map((interview) => (
                        <div
                            key={interview.id}
                            className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <h3 className="text-lg font-semibold text-slate-900">
                                            {interview.candidate_name}
                                        </h3>
                                        <span className={clsx(
                                            'px-3 py-1 rounded-full text-xs font-medium border',
                                            getStatusColor(interview.status)
                                        )}>
                                            {interview.status.charAt(0).toUpperCase() + interview.status.slice(1)}
                                        </span>
                                    </div>
                                    <p className="text-slate-600 mb-3">{interview.job_title}</p>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                                <div className="flex items-center gap-2 text-slate-700">
                                    <Calendar className="w-4 h-4 text-slate-400" />
                                    <span className="text-sm">{formatDate(interview.scheduled_time)}</span>
                                </div>
                                <div className="flex items-center gap-2 text-slate-700">
                                    <Clock className="w-4 h-4 text-slate-400" />
                                    <span className="text-sm">{formatTime(interview.scheduled_time)}</span>
                                </div>
                                <div className="flex items-center gap-2 text-slate-700">
                                    {getInterviewTypeIcon(interview.interview_type)}
                                    <span className="text-sm">{getInterviewTypeLabel(interview.interview_type)}</span>
                                </div>
                            </div>

                            {interview.location && (
                                <div className="flex items-start gap-2 text-slate-700 mb-4">
                                    <MapPin className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                                    <span className="text-sm">{interview.location}</span>
                                </div>
                            )}

                            {interview.notes && (
                                <div className="bg-slate-50 rounded-lg p-3 mb-4">
                                    <p className="text-sm text-slate-700">
                                        <span className="font-medium">Notes:</span> {interview.notes}
                                    </p>
                                </div>
                            )}

                            <div className="flex gap-2 pt-4 border-t border-slate-200">
                                {interview.status === 'scheduled' && (
                                    <>
                                        <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium">
                                            View Details
                                        </button>
                                        <button className="px-4 py-2 bg-white text-slate-700 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors text-sm font-medium">
                                            Reschedule
                                        </button>
                                        <button className="px-4 py-2 bg-white text-red-600 border border-red-300 rounded-lg hover:bg-red-50 transition-colors text-sm font-medium">
                                            Cancel
                                        </button>
                                    </>
                                )}
                                {interview.status === 'completed' && (
                                    <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium">
                                        View Feedback
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* AI Assistant CTA */}
            <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg p-6 text-white">
                <h2 className="text-xl font-semibold mb-2">Need help scheduling interviews?</h2>
                <p className="text-primary-100 mb-4">
                    Our AI assistant can help you schedule, reschedule, and manage interviews efficiently.
                </p>
                <a
                    href="/employer/chat"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-white text-primary-700 rounded-lg hover:bg-primary-50 transition-colors font-medium"
                >
                    Chat with AI Assistant
                </a>
            </div>
        </div>
    )
}
