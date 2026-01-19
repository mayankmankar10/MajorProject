// frontend/src/components/RecommendedJobs.tsx
import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Sparkles, TrendingUp, Star } from 'lucide-react'
import { Card, Button, Badge } from '@/components'
import { apiClient } from '@/services/api'

interface JobRecommendation {
    job_id: number
    title: string
    company: string
    location: string
    salary_range?: string
    match_score: number
    score_breakdown: {
        skills: number
        experience: number
        role: number
        salary: number
        location: number
    }
    description_preview: string
}

interface RecommendedJobsProps {
    onApply?: (jobId: string) => void
}

export const RecommendedJobs: React.FC<RecommendedJobsProps> = ({
    onApply
}) => {
    const [recommendations, setRecommendations] = useState<JobRecommendation[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchRecommendations()
    }, [])

    const fetchRecommendations = async () => {
        try {
            setLoading(true)
            const response = await apiClient.getJobRecommendations()

            setRecommendations(response.recommendations || [])
        } catch (error: any) {
            console.error('Failed to load recommendations:', error.response?.data?.detail || error.message)
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <Card>
                <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
                </div>
            </Card>
        )
    }

    if (recommendations.length === 0) {
        return (
            <Card>
                <div className="text-center py-12">
                    <Sparkles className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        No Recommendations Yet
                    </h3>
                    <p className="text-gray-600">
                        Complete your profile to get personalized job recommendations
                    </p>
                </div>
            </Card>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
                        <Sparkles className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-gray-900">Recommended For You</h2>
                        <p className="text-sm text-gray-600">
                            {recommendations.length} personalized job matches
                        </p>
                    </div>
                </div>
                <Button variant="ghost" size="sm" onClick={fetchRecommendations}>
                    <TrendingUp className="w-4 h-4 mr-2" />
                    Refresh
                </Button>
            </div>

            {/* Recommendations List */}
            <div className="space-y-4">
                {recommendations.map((rec, idx) => (
                    <motion.div
                        key={rec.job_id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.1 }}
                    >
                        <Card padding="lg" hover>
                            <div className="flex items-start justify-between gap-4">
                                {/* Job Info */}
                                <div className="flex-1">
                                    <div className="flex items-start gap-3 mb-3">
                                        <div className="flex-1">
                                            <h3 className="text-lg font-semibold text-gray-900 mb-1">
                                                {rec.title}
                                            </h3>
                                            <p className="text-sm text-gray-600">
                                                {rec.company} • {rec.location}
                                            </p>
                                            {rec.salary_range && (
                                                <p className="text-sm text-gray-500 mt-1">
                                                    {rec.salary_range}
                                                </p>
                                            )}
                                        </div>

                                        {/* Match Score Badge */}
                                        <div className="flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg">
                                            <Star className="w-4 h-4 text-green-600 fill-green-600" />
                                            <span className="text-sm font-bold text-green-700">
                                                {Math.round(rec.match_score * 100)}% Match
                                            </span>
                                        </div>
                                    </div>

                                    {/* Description Preview */}
                                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                                        {rec.description_preview}
                                    </p>

                                    {/* Score Breakdown */}
                                    <div className="flex flex-wrap gap-2 mb-3">
                                        {rec.score_breakdown.skills > 0 && (
                                            <Badge variant="primary" size="sm">
                                                Skills: {Math.round(rec.score_breakdown.skills * 100)}%
                                            </Badge>
                                        )}
                                        {rec.score_breakdown.experience > 0 && (
                                            <Badge variant="success" size="sm">
                                                Experience: {Math.round(rec.score_breakdown.experience * 100)}%
                                            </Badge>
                                        )}
                                        {rec.score_breakdown.role > 0 && (
                                            <Badge variant="info" size="sm">
                                                Role: {Math.round(rec.score_breakdown.role * 100)}%
                                            </Badge>
                                        )}
                                    </div>

                                    {/* Actions */}
                                    <div className="flex gap-2">
                                        {onApply && (
                                            <Button
                                                variant="primary"
                                                size="sm"
                                                onClick={() => onApply(rec.job_id.toString())}
                                            >
                                                Quick Apply
                                            </Button>
                                        )}
                                        <Button variant="outline" size="sm">
                                            View Details
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        </Card>
                    </motion.div>
                ))}
            </div>
        </div>
    )
}
