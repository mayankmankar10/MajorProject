import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileText,
  Calendar,
  TrendingUp,
  Clock,
  CheckCircle2,
  XCircle,
  Eye,
  MessageSquare,
  Briefcase,
  Star,
  AlertCircle,
  Building2,
  MapPin,
  DollarSign,
  Send
} from 'lucide-react'
import { Card, Badge, Button } from '@/components'
import { apiClient } from '@/services/api'
// import { useAuthStore } from '@/stores/useAuthStore'
import { Link } from 'react-router-dom'

interface Application {
  id: number
  job_id: number
  employee_id: number
  status: string
  match_score: number
  cover_letter?: string
  applied_at: string
  updated_at: string
  reviewed_at?: string
  notes?: string
  job?: {
    id: number
    title: string
    description: string
    location: string
    salary_range: string
    job_type: string
    employer?: {
      company_name: string
    }
  }
}

// Helper function to normalize match scores (handles both 0-1 and 0-100 formats)
const normalizeScore = (score: number | null | undefined): number => {
  if (!score) return 0
  // If score is less than 1, it's in decimal format (0.85), multiply by 100
  // If score is >= 1, it's already in percentage format (85)
  return score < 1 ? score * 100 : score
}

export const Applications: React.FC = () => {
  // const { user } = useAuthStore()
  const [applications, setApplications] = useState<Application[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState<string>('recent')
  const [selectedApp, setSelectedApp] = useState<Application | null>(null)

  useEffect(() => {
    loadApplications()
  }, [])

  const loadApplications = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getApplications()
      setApplications(data || [])
    } catch (error) {
      console.error('Failed to load applications:', error)
      setApplications([])
    } finally {
      setLoading(false)
    }
  }

  // Calculate stats
  const stats = {
    total: applications.length,
    applied: applications.filter(a => a.status === 'applied').length,
    reviewing: applications.filter(a => a.status === 'reviewing').length,
    interview: applications.filter(a => a.status === 'interview_scheduled').length,
    selected: applications.filter(a => a.status === 'selected').length,
    rejected: applications.filter(a => a.status === 'rejected').length,
    hired: applications.filter(a => a.status === 'hired').length
  }

  // AI Insights
  const insights = {
    avgMatchScore: applications.length > 0
      ? (applications.reduce((sum, app) => sum + normalizeScore(app.match_score), 0) / applications.length).toFixed(1)
      : 0,
    topMatches: applications.filter(a => normalizeScore(a.match_score) >= 85).length,
    pendingFollowups: applications.filter(a =>
      a.status === 'applied' &&
      new Date().getTime() - new Date(a.applied_at).getTime() > 7 * 24 * 60 * 60 * 1000
    ).length,
    successRate: applications.length > 0
      ? ((stats.hired + stats.selected) / applications.length * 100).toFixed(1)
      : 0
  }

  // Filter and sort
  const filteredApplications = statusFilter === 'all'
    ? applications
    : applications.filter(app => app.status === statusFilter)

  const sortedApplications = [...filteredApplications].sort((a, b) => {
    switch (sortBy) {
      case 'recent':
        return new Date(b.applied_at).getTime() - new Date(a.applied_at).getTime()
      case 'oldest':
        return new Date(a.applied_at).getTime() - new Date(b.applied_at).getTime()
      case 'match':
        return (b.match_score || 0) - (a.match_score || 0)
      default:
        return 0
    }
  })

  const getStatusConfig = (status: string) => {
    const configs: Record<string, { color: string; icon: any; label: string; bgColor: string }> = {
      applied: {
        color: 'text-yellow-700',
        bgColor: 'bg-yellow-100',
        icon: Send,
        label: 'Applied'
      },
      reviewing: {
        color: 'text-blue-700',
        bgColor: 'bg-blue-100',
        icon: Eye,
        label: 'Under Review'
      },
      interview_scheduled: {
        color: 'text-purple-700',
        bgColor: 'bg-purple-100',
        icon: Calendar,
        label: 'Interview Scheduled'
      },
      offer_sent: {
        color: 'text-orange-700',
        bgColor: 'bg-orange-100',
        icon: Star,
        label: 'Offer Received'
      },
      offer_accepted: {
        color: 'text-green-700',
        bgColor: 'bg-green-100',
        icon: CheckCircle2,
        label: 'Offer Accepted'
      },
      offer_declined: {
        color: 'text-gray-700',
        bgColor: 'bg-gray-100',
        icon: XCircle,
        label: 'Offer Declined'
      },
      selected: {
        color: 'text-green-700',
        bgColor: 'bg-green-100',
        icon: CheckCircle2,
        label: 'Selected'
      },
      rejected: {
        color: 'text-red-700',
        bgColor: 'bg-red-100',
        icon: XCircle,
        label: 'Rejected'
      },
      hired: {
        color: 'text-emerald-700',
        bgColor: 'bg-emerald-100',
        icon: Star,
        label: 'Hired'
      }
    }
    return configs[status] || configs['applied']
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
    return date.toLocaleDateString()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your applications...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">My Applications</h1>
        <p className="text-gray-600">Track progress and get AI-powered insights on your job applications</p>
      </motion.div>

      {/* AI Insights Banner */}
      {applications.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card padding="lg" className="mb-8 bg-gradient-to-r from-primary-50 to-secondary-50 border-primary-200">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-primary-100 rounded-xl">
                <TrendingUp className="w-6 h-6 text-primary-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 mb-3">📊 Your Application Insights</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-2xl font-bold text-primary-600">{insights.avgMatchScore}%</div>
                    <div className="text-sm text-gray-600">Avg Match Score</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600">{insights.topMatches}</div>
                    <div className="text-sm text-gray-600">Top Matches (85%+)</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-emerald-600">{insights.successRate}%</div>
                    <div className="text-sm text-gray-600">Success Rate</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-yellow-600">{insights.pendingFollowups}</div>
                    <div className="text-sm text-gray-600">Needs Follow-up</div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-8">
        <StatCard
          title="Total"
          value={stats.total}
          active={statusFilter === 'all'}
          onClick={() => setStatusFilter('all')}
          color="gray"
          delay={0.1}
        />
        <StatCard
          title="Applied"
          value={stats.applied}
          active={statusFilter === 'applied'}
          onClick={() => setStatusFilter('applied')}
          color="yellow"
          delay={0.15}
        />
        <StatCard
          title="Reviewing"
          value={stats.reviewing}
          active={statusFilter === 'reviewing'}
          onClick={() => setStatusFilter('reviewing')}
          color="blue"
          delay={0.2}
        />
        <StatCard
          title="Interview"
          value={stats.interview}
          active={statusFilter === 'interview_scheduled'}
          onClick={() => setStatusFilter('interview_scheduled')}
          color="purple"
          delay={0.25}
        />
        <StatCard
          title="Selected"
          value={stats.selected}
          active={statusFilter === 'selected'}
          onClick={() => setStatusFilter('selected')}
          color="green"
          delay={0.3}
        />
        <StatCard
          title="Hired"
          value={stats.hired}
          active={statusFilter === 'hired'}
          onClick={() => setStatusFilter('hired')}
          color="emerald"
          delay={0.35}
        />
      </div>

      {/* Filter & Sort Bar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="flex items-center justify-between mb-6"
      >
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-gray-400" />
          <span className="text-gray-600">
            Showing <strong className="text-gray-900">{sortedApplications.length}</strong> application{sortedApplications.length !== 1 ? 's' : ''}
          </span>
          {statusFilter !== 'all' && (
            <Badge variant="primary">
              {getStatusConfig(statusFilter).label}
            </Badge>
          )}
        </div>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          <option value="recent">Most Recent</option>
          <option value="oldest">Oldest First</option>
          <option value="match">Highest Match</option>
        </select>
      </motion.div>

      {/* Applications List */}
      {sortedApplications.length > 0 ? (
        <div className="space-y-4">
          {sortedApplications.map((application, idx) => {
            const statusConfig = getStatusConfig(application.status)
            const StatusIcon = statusConfig.icon
            const matchPercentage = normalizeScore(application.match_score).toFixed(0)
            const daysAgo = Math.ceil(
              (new Date().getTime() - new Date(application.applied_at).getTime()) / (1000 * 60 * 60 * 24)
            )

            return (
              <motion.div
                key={application.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.45 + idx * 0.05 }}
              >
                <Card padding="lg" hover className="cursor-pointer" onClick={() => setSelectedApp(application)}>
                  <div className="flex items-start gap-4">
                    {/* Company Icon */}
                    <div className={`flex-shrink-0 w-14 h-14 rounded-xl flex items-center justify-center ${statusConfig.bgColor}`}>
                      <Building2 className={`w-7 h-7 ${statusConfig.color}`} />
                    </div>

                    <div className="flex-1 min-w-0">
                      {/* Header */}
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900 mb-1">
                            {application.job?.title || 'Job Title'}
                          </h3>
                          <div className="flex items-center gap-3 text-sm text-gray-600">
                            <span className="flex items-center gap-1">
                              <Building2 className="w-4 h-4" />
                              {application.job?.employer?.company_name || 'Company Name'}
                            </span>
                            {application.job?.location && (
                              <span className="flex items-center gap-1">
                                <MapPin className="w-4 h-4" />
                                {application.job.location}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className={`px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${statusConfig.bgColor} ${statusConfig.color}`}>
                            <StatusIcon className="w-3 h-3" />
                            {statusConfig.label}
                          </div>
                        </div>
                      </div>

                      {/* Stats */}
                      <div className="flex items-center gap-4 mb-3">
                        {/* Match Score */}
                        <div className="flex items-center gap-2">
                          <div className="flex items-center gap-1">
                            <Star className={`w-4 h-4 ${parseInt(matchPercentage) >= 80 ? 'text-green-600 fill-green-600' : 'text-yellow-600'}`} />
                            <span className="text-sm font-semibold text-gray-900">{matchPercentage}%</span>
                          </div>
                          <span className="text-xs text-gray-500">Match</span>
                        </div>

                        {/* Applied Date */}
                        <div className="flex items-center gap-1 text-sm text-gray-600">
                          <Clock className="w-4 h-4" />
                          Applied {formatDate(application.applied_at)}
                        </div>

                        {/* Job Type */}
                        {application.job?.job_type && (
                          <Badge variant="default">{application.job.job_type}</Badge>
                        )}
                      </div>

                      {/* AI Recommendation */}
                      {daysAgo >= 7 && application.status === 'applied' && (
                        <div className="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg mb-3">
                          <AlertCircle className="w-4 h-4 text-yellow-600 flex-shrink-0 mt-0.5" />
                          <div className="text-sm text-yellow-800">
                            <strong>AI Tip:</strong> It's been {daysAgo} days. Consider following up via chat or reviewing similar opportunities.
                          </div>
                        </div>
                      )}

                      {parseInt(matchPercentage) >= 90 && application.status === 'applied' && (
                        <div className="flex items-start gap-2 p-3 bg-green-50 border border-green-200 rounded-lg mb-3">
                          <TrendingUp className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                          <div className="text-sm text-green-800">
                            <strong>Excellent Match!</strong> Your profile aligns very well with this role. High chance of success!
                          </div>
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedApp(application)
                          }}
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          View Details
                        </Button>
                        <Link to="/employee/chat">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <MessageSquare className="w-4 h-4 mr-1" />
                            Discuss with AI
                          </Button>
                        </Link>
                      </div>
                    </div>
                  </div>
                </Card>
              </motion.div>
            )
          })}
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card padding="lg" className="text-center">
            <Briefcase className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {statusFilter === 'all' ? 'No applications yet' : `No ${getStatusConfig(statusFilter).label.toLowerCase()} applications`}
            </h3>
            <p className="text-gray-600 mb-6">
              {statusFilter === 'all'
                ? "Start exploring job opportunities and apply to positions that match your skills!"
                : `You don't have any applications with status "${getStatusConfig(statusFilter).label}"`
              }
            </p>
            {statusFilter === 'all' ? (
              <Link to="/employee/jobs">
                <Button variant="primary" size="md">
                  <Briefcase className="w-4 h-4 mr-2" />
                  Browse Jobs
                </Button>
              </Link>
            ) : (
              <Button
                variant="outline"
                size="md"
                onClick={() => setStatusFilter('all')}
              >
                View All Applications
              </Button>
            )}
          </Card>
        </motion.div>
      )}

      {/* Application Detail Modal */}
      <AnimatePresence>
        {selectedApp && (
          <ApplicationDetailsModal
            application={selectedApp}
            onClose={() => setSelectedApp(null)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

// Stat Card Component
const StatCard: React.FC<{
  title: string
  value: number
  active: boolean
  onClick: () => void
  color: string
  delay: number
}> = ({ title, value, active, onClick, color, delay }) => {
  const colorClasses = {
    gray: active ? 'ring-2 ring-gray-500 bg-gray-50' : 'hover:bg-gray-50',
    yellow: active ? 'ring-2 ring-yellow-500 bg-yellow-50' : 'hover:bg-yellow-50',
    blue: active ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:bg-blue-50',
    purple: active ? 'ring-2 ring-purple-500 bg-purple-50' : 'hover:bg-purple-50',
    green: active ? 'ring-2 ring-green-500 bg-green-50' : 'hover:bg-green-50',
    emerald: active ? 'ring-2 ring-emerald-500 bg-emerald-50' : 'hover:bg-emerald-50'
  }

  const textColors = {
    gray: 'text-gray-900',
    yellow: 'text-yellow-600',
    blue: 'text-blue-600',
    purple: 'text-purple-600',
    green: 'text-green-600',
    emerald: 'text-emerald-600'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
    >
      <Card
        padding="md"
        hover
        className={colorClasses[color as keyof typeof colorClasses]}
      >
        <button
          onClick={onClick}
          className="w-full text-left"
        >
          <div className={`text-2xl font-bold ${textColors[color as keyof typeof textColors]}`}>
            {value}
          </div>
          <div className="text-sm text-gray-600">{title}</div>
        </button>
      </Card>
    </motion.div>
  )
}

// Application Details Modal
const ApplicationDetailsModal: React.FC<{
  application: Application
  onClose: () => void
}> = ({ application, onClose }) => {
  const statusConfig = getStatusConfig(application.status)
  const StatusIcon = statusConfig.icon
  const matchPercentage = normalizeScore(application.match_score).toFixed(0)

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                {application.job?.title || 'Application Details'}
              </h2>
              <p className="text-gray-600">
                {application.job?.employer?.company_name || 'Company'}
              </p>
            </div>
            <div className={`px-4 py-2 rounded-full text-sm font-medium flex items-center gap-2 ${statusConfig.bgColor} ${statusConfig.color}`}>
              <StatusIcon className="w-4 h-4" />
              {statusConfig.label}
            </div>
          </div>

          {/* Match Score */}
          <div className="mb-6 p-4 bg-primary-50 border border-primary-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">Match Score</div>
                <div className="text-3xl font-bold text-primary-600">{matchPercentage}%</div>
              </div>
              <Star className="w-12 h-12 text-primary-600" />
            </div>
          </div>

          {/* Job Details */}
          <div className="space-y-4 mb-6">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Job Description</h3>
              <p className="text-gray-700 text-sm leading-relaxed">
                {application.job?.description || 'No description available'}
              </p>
            </div>

            {application.job?.location && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Location</h3>
                <p className="text-gray-700 text-sm flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  {application.job.location}
                </p>
              </div>
            )}

            {application.job?.salary_range && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Salary Range</h3>
                <p className="text-gray-700 text-sm flex items-center gap-2">
                  <DollarSign className="w-4 h-4" />
                  {application.job.salary_range}
                </p>
              </div>
            )}
          </div>

          {/* Timeline */}
          <div className="mb-6">
            <h3 className="font-semibold text-gray-900 mb-3">Application Timeline</h3>
            <div className="space-y-3">
              <TimelineItem
                icon={Send}
                label="Applied"
                date={new Date(application.applied_at).toLocaleDateString()}
                active
              />
              {application.reviewed_at && (
                <TimelineItem
                  icon={Eye}
                  label="Reviewed"
                  date={new Date(application.reviewed_at).toLocaleDateString()}
                  active
                />
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <Link to="/employee/chat" className="flex-1">
              <Button variant="primary" size="md" className="w-full">
                <MessageSquare className="w-4 h-4 mr-2" />
                Discuss with AI
              </Button>
            </Link>
            <Button variant="outline" size="md" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}

const TimelineItem: React.FC<{
  icon: any
  label: string
  date: string
  active?: boolean
}> = ({ icon: Icon, label, date, active }) => (
  <div className="flex items-center gap-3">
    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${active ? 'bg-primary-100' : 'bg-gray-100'}`}>
      <Icon className={`w-4 h-4 ${active ? 'text-primary-600' : 'text-gray-400'}`} />
    </div>
    <div className="flex-1">
      <div className="font-medium text-gray-900">{label}</div>
      <div className="text-sm text-gray-600">{date}</div>
    </div>
  </div>
)

function getStatusConfig(status: string) {
  const configs: Record<string, { color: string; icon: any; label: string; bgColor: string }> = {
    applied: {
      color: 'text-yellow-700',
      bgColor: 'bg-yellow-100',
      icon: Send,
      label: 'Applied'
    },
    reviewing: {
      color: 'text-blue-700',
      bgColor: 'bg-blue-100',
      icon: Eye,
      label: 'Under Review'
    },
    interview_scheduled: {
      color: 'text-purple-700',
      bgColor: 'bg-purple-100',
      icon: Calendar,
      label: 'Interview Scheduled'
    },
    selected: {
      color: 'text-green-700',
      bgColor: 'bg-green-100',
      icon: CheckCircle2,
      label: 'Selected'
    },
    rejected: {
      color: 'text-red-700',
      bgColor: 'bg-red-100',
      icon: XCircle,
      label: 'Rejected'
    },
    hired: {
      color: 'text-emerald-700',
      bgColor: 'bg-emerald-100',
      icon: Star,
      label: 'Hired'
    }
  }
  return configs[status] || configs['applied']
}
