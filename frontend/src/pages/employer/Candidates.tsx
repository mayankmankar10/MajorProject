import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { Users, Star, Mail, Phone, Briefcase, Loader, AlertCircle, Filter } from 'lucide-react'
import { Card, Button, Badge } from '@/components'

// Helper function to normalize match scores (handles both 0-1 and 0-100 formats)
const normalizeScore = (score: number | null | undefined): number => {
  if (!score) return 0
  // If score is less than 1, it's in decimal format (0.85), multiply by 100
  // If score is >= 1, it's already in percentage format (85)
  return score < 1 ? score * 100 : score
}

export const Candidates: React.FC = () => {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [applications, setApplications] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const fetchApplications = async () => {
      try {
        setIsLoading(true)
        const token = localStorage.getItem('auth_token')
        const userStr = localStorage.getItem('auth_user')
        if (!token) {
          throw new Error('Please log in to view applications')
        }

        // Get user_id from localStorage
        let userId = ''
        if (userStr) {
          try {
            const user = JSON.parse(userStr)
            userId = user.id || ''
          } catch (e) {
            console.error('Failed to parse user from localStorage')
          }
        }

        // Build URL with query params
        const params = new URLSearchParams()
        if (userId) params.append('user_id', userId)
        params.append('limit', '100')
        if (statusFilter) params.append('status', statusFilter)

        const response = await fetch(`/api/employer/applications?${params.toString()}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (!response.ok) {
          if (response.status === 401) {
            throw new Error('Unauthorized - Please log in again')
          }
          throw new Error(`Failed to load applications: ${response.statusText}`)
        }

        const data = await response.json()
        setApplications(data)
      } catch (err: any) {
        setError(err)
      } finally {
        setIsLoading(false)
      }
    }
    fetchApplications()
  }, [statusFilter])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
        <AlertCircle className="w-5 h-5 text-red-600" />
        <p className="text-red-800">Failed to load applications. Please try again.</p>
      </div>
    )
  }

  // Use actual database status values (lowercase to match DB)
  const statusOptions = ['offer_sent', 'hired']

  const formatStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      'applied': 'Applied',
      'reviewing': 'Reviewed',
      'offer_sent': 'Offered',
      'interview_scheduled': 'Interviewing',
      'selected': 'Offered',
      'rejected': 'Rejected',
      'hired': 'Hired'
    }
    return labels[status] || status.replace('_', ' ').charAt(0).toUpperCase() + status.slice(1)
  }

  return (
    <div>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Applications</h1>
        <p className="text-gray-600">
          {applications?.length || 0} application{applications?.length !== 1 ? 's' : ''} received
        </p>
      </motion.div>

      {/* Filter Bar */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-6 flex items-center gap-3 flex-wrap"
      >
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-gray-600" />
          <span className="text-sm font-medium text-gray-700">Filter by status:</span>
        </div>
        <Button
          variant={statusFilter === null ? 'primary' : 'ghost'}
          size="sm"
          onClick={() => setStatusFilter(null)}
        >
          All
        </Button>
        {statusOptions.map(status => (
          <Button
            key={status}
            variant={statusFilter === status ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setStatusFilter(status)}
          >
            {formatStatusLabel(status)}
          </Button>
        ))}
      </motion.div>

      {!applications || applications.length === 0 ? (
        <Card padding="lg">
          <div className="text-center py-12">
            <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {statusFilter ? `No ${formatStatusLabel(statusFilter).toLowerCase()} applications` : 'No applications yet'}
            </h3>
            <p className="text-gray-600 mb-6">
              {statusFilter
                ? 'Try selecting a different status filter'
                : 'Applications will appear here when candidates apply to your jobs'
              }
            </p>
            {statusFilter && (
              <Button variant="primary" onClick={() => setStatusFilter(null)}>
                Show All Applications
              </Button>
            )}
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {applications.map((application: any, idx: number) => (
            <motion.div
              key={application.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
            >
              <Card padding="lg" hover>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4 flex-1">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                      {application.employee_name?.split(' ').map((n: string) => n[0]).join('').slice(0, 2) || 'NA'}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {application.employee_name || 'Unknown Candidate'}
                          </h3>
                          <div className="flex items-center gap-2 text-sm text-gray-600 mt-1">
                            <Briefcase className="w-4 h-4" />
                            <span>
                              {(application.status === 'offer_sent' || application.status === 'hired')
                                ? 'Direct Hire:'
                                : 'Applied for:'} <strong>{application.job_title}</strong>
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          {application.match_score && (
                            <div className="flex items-center gap-1 text-yellow-600 mb-2">
                              <Star className="w-4 h-4 fill-current" />
                              <span className="font-semibold">
                                {Math.round(normalizeScore(application.match_score))}% Match
                              </span>
                            </div>
                          )}
                          <Badge
                            variant={
                              application.status === 'hired' || application.status === 'offer_sent' ? 'success' :
                                application.status === 'rejected' ? 'default' :
                                  application.status === 'offered' ? 'success' :
                                    application.status === 'interviewing' ? 'primary' :
                                      'default'
                            }
                          >
                            {application.status === 'offer_sent' ? 'offer sent' :
                              application.status?.replace('_', ' ') || 'Pending'}
                          </Badge>
                        </div>
                      </div>

                      <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                        {application.employee_email && (
                          <span className="flex items-center gap-1">
                            <Mail className="w-4 h-4" />
                            {application.employee_email}
                          </span>
                        )}
                        {application.employee_phone && (
                          <span className="flex items-center gap-1">
                            <Phone className="w-4 h-4" />
                            {application.employee_phone}
                          </span>
                        )}
                      </div>

                      {application.cover_letter && (
                        <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg line-clamp-3 mb-3">
                          {application.cover_letter}
                        </p>
                      )}

                      <div className="flex items-center justify-between">
                        <p className="text-xs text-gray-500">
                          {(application.status === 'offer_sent' || application.status === 'hired') ? 'Hired on' : 'Applied on'} {new Date(application.applied_at).toLocaleDateString('en-IN', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric'
                          })} at {new Date(application.applied_at).toLocaleTimeString('en-IN', {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </p>
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => navigate(`/employer/chat?action=review&applicationId=${application.id}`)}
                        >
                          Review in Chat
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
