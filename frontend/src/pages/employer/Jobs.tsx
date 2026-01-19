import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Briefcase, Plus, Users, MapPin, DollarSign, Loader, AlertCircle } from 'lucide-react'
import { Card, Button, Badge, PostJobModal } from '@/components'

export const Jobs: React.FC = () => {
  const [jobs, setJobs] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [showPostJobModal, setShowPostJobModal] = useState(false)

  const fetchJobs = async () => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem('auth_token')
      const userStr = localStorage.getItem('auth_user')
      if (!token) {
        throw new Error('Please log in to view jobs')
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

      const response = await fetch(`/api/employer/jobs${userId ? `?user_id=${userId}` : ''}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Unauthorized - Please log in again')
        }
        throw new Error(`Failed to load jobs: ${response.statusText}`)
      }

      const data = await response.json()
      setJobs(data)
    } catch (err: any) {
      setError(err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchJobs()
  }, [])

  const handleJobPosted = () => {
    // Refresh jobs list after successful post
    fetchJobs()
  }

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
        <p className="text-red-800">Failed to load jobs. Please try again.</p>
      </div>
    )
  }

  return (
    <div>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 flex justify-between items-center"
      >
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Job Listings</h1>
          <p className="text-gray-600">
            {jobs?.length || 0} job{jobs?.length !== 1 ? 's' : ''} posted
          </p>
        </div>
        <Button
          variant="primary"
          size="md"
          leftIcon={<Plus className="w-5 h-5" />}
          onClick={() => setShowPostJobModal(true)}
        >
          Post New Job
        </Button>
      </motion.div>

      {!jobs || jobs.length === 0 ? (
        <Card padding="lg">
          <div className="text-center py-12">
            <Briefcase className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No jobs posted yet</h3>
            <p className="text-gray-600 mb-6">Start by posting your first job listing</p>
            <Button
              variant="primary"
              onClick={() => setShowPostJobModal(true)}
            >
              Post Your First Job
            </Button>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {jobs.map((job: any, idx: number) => (
            <motion.div
              key={job.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
            >
              <Card padding="lg" hover>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4 flex-1">
                    <div className="p-3 bg-blue-100 rounded-xl">
                      <Briefcase className="w-6 h-6 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                          <div className="flex items-center gap-3 text-sm text-gray-600 mt-1">
                            {job.location && (
                              <span className="flex items-center gap-1">
                                <MapPin className="w-4 h-4" />
                                {job.location}
                              </span>
                            )}
                            {job.job_category && (
                              <span className="capitalize">{job.job_category.replace('_', ' ')}</span>
                            )}
                          </div>
                        </div>
                        <Badge variant={job.is_active ? 'success' : 'default'}>
                          {job.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>

                      {job.description && (
                        <p className="text-sm text-gray-700 mb-3 line-clamp-2">
                          {job.description}
                        </p>
                      )}

                      <div className="flex items-center gap-4 text-sm">
                        <span className="flex items-center gap-1 text-gray-600">
                          <Users className="w-4 h-4" />
                          <strong>{job.application_count || 0}</strong> applications
                        </span>

                        {job.shift_type && (
                          <span className="text-gray-600">
                            Shift: <strong className="capitalize">{job.shift_type}</strong>
                          </span>
                        )}

                        {job.salary_range && (
                          <span className="flex items-center gap-1 text-gray-600">
                            <DollarSign className="w-4 h-4" />
                            ₹{job.salary_range}
                          </span>
                        )}

                        {job.quantity_needed && (
                          <div className="flex items-center gap-2 text-sm">
                            <Users className="w-4 h-4 text-gray-400" />
                            <span className="text-gray-600">
                              Positions:
                              <span className="ml-1">
                                {job.offers_accepted > 0 && (
                                  <span className="text-green-600 font-semibold">{job.offers_accepted} hired</span>
                                )}
                                {job.offers_pending > 0 && (
                                  <span className="text-yellow-600 font-semibold">
                                    {job.offers_accepted > 0 ? ', ' : ''}{job.offers_pending} pending
                                  </span>
                                )}
                                {job.positions_available > 0 && (
                                  <span className="text-blue-600 font-semibold">
                                    {(job.offers_accepted > 0 || job.offers_pending > 0) ? ', ' : ''}{job.positions_available} available
                                  </span>
                                )}
                                {job.offers_accepted === 0 && job.offers_pending === 0 && job.positions_available === 0 && (
                                  <span className="text-gray-500">0/{job.quantity_needed}</span>
                                )}
                                <span className="text-gray-400 ml-1">({job.quantity_needed} total)</span>
                              </span>
                            </span>
                          </div>
                        )}
                      </div>

                      {job.created_at && (
                        <p className="text-xs text-gray-500 mt-2">
                          Posted on {new Date(job.created_at).toLocaleDateString('en-IN', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric'
                          })}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* Post Job Modal */}
      <PostJobModal
        isOpen={showPostJobModal}
        onClose={() => setShowPostJobModal(false)}
        onSuccess={handleJobPosted}
      />
    </div>
  )
}
