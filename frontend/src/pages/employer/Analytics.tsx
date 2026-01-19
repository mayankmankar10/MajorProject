import React, { useState, useEffect } from 'react'
import { BarChart3, TrendingUp, Users, Briefcase, Calendar, Loader2 } from 'lucide-react'
import { apiClient } from '@/services/api'
import clsx from 'clsx'

interface DashboardMetrics {
    total_jobs: number
    active_jobs: number
    total_applications: number
    interviews_scheduled: number
    hires_made: number
    avg_time_to_hire: number
}

export const Analytics: React.FC = () => {
    const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        loadAnalytics()
    }, [])

    const loadAnalytics = async () => {
        try {
            setIsLoading(true)
            const response = await apiClient.getDashboardMetrics()
            setMetrics(response)
        } catch (error) {
            console.error('Failed to load analytics:', error)
            // Set mock data for demo
            setMetrics({
                total_jobs: 15,
                active_jobs: 8,
                total_applications: 127,
                interviews_scheduled: 23,
                hires_made: 12,
                avg_time_to_hire: 14
            })
        } finally {
            setIsLoading(false)
        }
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-96">
                <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
            </div>
        )
    }

    const statCards = [
        {
            title: 'Total Jobs Posted',
            value: metrics?.total_jobs || 0,
            icon: Briefcase,
            color: 'blue',
            change: '+12%',
            changeType: 'positive' as const
        },
        {
            title: 'Active Jobs',
            value: metrics?.active_jobs || 0,
            icon: TrendingUp,
            color: 'green',
            change: '+5%',
            changeType: 'positive' as const
        },
        {
            title: 'Total Applications',
            value: metrics?.total_applications || 0,
            icon: Users,
            color: 'purple',
            change: '+23%',
            changeType: 'positive' as const
        },
        {
            title: 'Interviews Scheduled',
            value: metrics?.interviews_scheduled || 0,
            icon: Calendar,
            color: 'orange',
            change: '+8%',
            changeType: 'positive' as const
        }
    ]

    const colorClasses = {
        blue: {
            bg: 'bg-blue-100',
            icon: 'text-blue-600',
            border: 'border-blue-200'
        },
        green: {
            bg: 'bg-green-100',
            icon: 'text-green-600',
            border: 'border-green-200'
        },
        purple: {
            bg: 'bg-purple-100',
            icon: 'text-purple-600',
            border: 'border-purple-200'
        },
        orange: {
            bg: 'bg-orange-100',
            icon: 'text-orange-600',
            border: 'border-orange-200'
        }
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-slate-900">Analytics Dashboard</h1>
                <p className="text-slate-600 mt-1">Track your recruitment performance and metrics</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {statCards.map((stat) => {
                    const Icon = stat.icon
                    const colors = colorClasses[stat.color as keyof typeof colorClasses]

                    return (
                        <div
                            key={stat.title}
                            className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow"
                        >
                            <div className="flex items-center justify-between mb-4">
                                <div className={clsx('p-3 rounded-lg', colors.bg)}>
                                    <Icon className={clsx('w-6 h-6', colors.icon)} />
                                </div>
                                <span className={clsx(
                                    'text-sm font-medium px-2 py-1 rounded',
                                    stat.changeType === 'positive' ? 'text-green-700 bg-green-100' : 'text-red-700 bg-red-100'
                                )}>
                                    {stat.change}
                                </span>
                            </div>
                            <h3 className="text-sm font-medium text-slate-600 mb-1">{stat.title}</h3>
                            <p className="text-3xl font-bold text-slate-900">{stat.value}</p>
                        </div>
                    )
                })}
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Hiring Metrics */}
                <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
                    <h2 className="text-lg font-semibold text-slate-900 mb-4">Hiring Metrics</h2>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                            <div>
                                <p className="text-sm text-slate-600">Total Hires</p>
                                <p className="text-2xl font-bold text-slate-900">{metrics?.hires_made || 0}</p>
                            </div>
                            <div className="p-3 bg-green-100 rounded-lg">
                                <Users className="w-6 h-6 text-green-600" />
                            </div>
                        </div>
                        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                            <div>
                                <p className="text-sm text-slate-600">Avg. Time to Hire</p>
                                <p className="text-2xl font-bold text-slate-900">{metrics?.avg_time_to_hire || 0} days</p>
                            </div>
                            <div className="p-3 bg-blue-100 rounded-lg">
                                <Calendar className="w-6 h-6 text-blue-600" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Application Funnel */}
                <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
                    <h2 className="text-lg font-semibold text-slate-900 mb-4">Application Funnel</h2>
                    <div className="space-y-3">
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-slate-700">Applications Received</span>
                                <span className="text-sm font-semibold text-slate-900">{metrics?.total_applications || 0}</span>
                            </div>
                            <div className="w-full bg-slate-200 rounded-full h-2">
                                <div className="bg-blue-600 h-2 rounded-full" style={{ width: '100%' }} />
                            </div>
                        </div>
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-slate-700">Interviews Scheduled</span>
                                <span className="text-sm font-semibold text-slate-900">{metrics?.interviews_scheduled || 0}</span>
                            </div>
                            <div className="w-full bg-slate-200 rounded-full h-2">
                                <div
                                    className="bg-purple-600 h-2 rounded-full"
                                    style={{
                                        width: `${metrics?.total_applications ? (metrics.interviews_scheduled / metrics.total_applications * 100) : 0}%`
                                    }}
                                />
                            </div>
                        </div>
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-slate-700">Hires Made</span>
                                <span className="text-sm font-semibold text-slate-900">{metrics?.hires_made || 0}</span>
                            </div>
                            <div className="w-full bg-slate-200 rounded-full h-2">
                                <div
                                    className="bg-green-600 h-2 rounded-full"
                                    style={{
                                        width: `${metrics?.total_applications ? (metrics.hires_made / metrics.total_applications * 100) : 0}%`
                                    }}
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Charts Placeholder */}
            <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
                <h2 className="text-lg font-semibold text-slate-900 mb-4">Performance Over Time</h2>
                <div className="flex items-center justify-center h-64 bg-slate-50 rounded-lg">
                    <div className="text-center">
                        <BarChart3 className="w-16 h-16 text-slate-400 mx-auto mb-3" />
                        <p className="text-slate-600">Chart visualization coming soon</p>
                        <p className="text-sm text-slate-500 mt-1">Track your hiring trends over time</p>
                    </div>
                </div>
            </div>

            {/* AI Insights */}
            <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg p-6 text-white">
                <h2 className="text-xl font-semibold mb-2">💡 AI-Powered Insights</h2>
                <p className="text-primary-100 mb-4">
                    Get personalized recommendations to improve your recruitment process
                </p>
                <a
                    href="/employer/chat"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-white text-primary-700 rounded-lg hover:bg-primary-50 transition-colors font-medium"
                >
                    Ask AI for Insights
                </a>
            </div>
        </div>
    )
}
