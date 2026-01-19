import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Search, MapPin, Filter, Loader2, AlertCircle } from 'lucide-react'
import { Input, Button, JobCard, Badge, Card } from '@/components'
import { apiClient } from '@/services/api'
import { useAuthStore } from '@/stores/useAuthStore'
import { Job } from '@/types'

// Extended Job interface for search results with additional fields from API
interface JobSearchResult extends Omit<Job, 'job_type' | 'requirements'> {
  job_type: string  // Allow any string from backend
  requirements?: any  // Make optional
  posted_time: string  // Human-readable time from backend
  match_score: number  // 0-1 score from matching algorithm
  already_applied: boolean  // Whether user has already applied
  company_name: string  // Employer company name
  min_hospitality_experience?: number
  job_category?: string
}

export const JobSearch: React.FC = () => {
  const user = useAuthStore((state) => state.user)
  const [jobs, setJobs] = useState<JobSearchResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [searchQuery, setSearchQuery] = useState('')
  const [location, setLocation] = useState('')
  const [showFilters, setShowFilters] = useState(false)

  // Filter states
  const [jobType, setJobType] = useState('')
  const [experienceLevel, setExperienceLevel] = useState('')
  const [salaryRange, setSalaryRange] = useState('')

  // Fetch jobs on component mount and when filters change
  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = async () => {
    try {
      setLoading(true)
      setError(null)

      // Get employee ID from user - try profileId first, then id
      const employeeId = user?.profileId || user?.id

      if (!employeeId) {
        setError('Employee profile not found. Please complete your profile first.')
        return
      }

      // Build filter params
      const params: any = {}
      if (searchQuery) params.search = searchQuery
      if (location) params.location = location
      if (jobType) params.job_type = jobType
      if (experienceLevel) params.experience_level = experienceLevel

      // Fetch recommended jobs
      const response = await apiClient.getRecommendedJobs(employeeId, params)

      setJobs(response.jobs || [])
    } catch (err: any) {
      console.error('Error fetching jobs:', err)
      setError(err.response?.data?.detail || 'Failed to fetch jobs. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    fetchJobs()
  }

  const handleApply = async (jobId: number, matchScore?: number) => {
    try {
      // Create application with the match score from search results
      const response = await apiClient.createApplication({
        job_id: jobId,
        user_id: user?.id || 0,  // Pass user ID for authentication
        cover_letter: '', // Optional: Add cover letter field if needed
        match_score: matchScore || 0  // Pass the pre-calculated match score
      })

      console.log('Application Submitted! 🎉', response)

      // Refresh job list to update "already_applied" status
      fetchJobs()
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to submit application. Please try again.'
      console.error('Application Failed:', errorMessage)
      alert(errorMessage)  // Show error to user
    }
  }


  return (
    <div>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Find Your Next Job</h1>
        <p className="text-gray-600">Discover opportunities tailored to your skills</p>
      </motion.div>

      {/* Search Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card padding="lg" className="mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <Input
                placeholder="Job title, keywords, or company"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                leftIcon={<Search className="w-5 h-5" />}
              />
            </div>
            <div className="flex gap-2">
              <Input
                placeholder="Location"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                leftIcon={<MapPin className="w-5 h-5" />}
              />
              <Button
                variant="primary"
                size="md"
                className="whitespace-nowrap"
                onClick={handleSearch}
                disabled={loading}
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Search'}
              </Button>
            </div>
          </div>

          {/* Filter Toggle */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              leftIcon={<Filter className="w-4 h-4" />}
            >
              {showFilters ? 'Hide Filters' : 'Show Filters'}
            </Button>
          </div>

          {/* Filters */}
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 pt-4 border-t border-gray-200"
            >
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Job Type
                  </label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={jobType}
                    onChange={(e) => setJobType(e.target.value)}
                  >
                    <option value="">All Types</option>
                    <option value="full_time">Full-time</option>
                    <option value="part_time">Part-time</option>
                    <option value="contract">Contract</option>
                    <option value="internship">Internship</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Experience Level
                  </label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={experienceLevel}
                    onChange={(e) => setExperienceLevel(e.target.value)}
                  >
                    <option value="">All Levels</option>
                    <option value="entry">Entry Level</option>
                    <option value="mid">Mid Level</option>
                    <option value="senior">Senior Level</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Salary Range
                  </label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={salaryRange}
                    onChange={(e) => setSalaryRange(e.target.value)}
                  >
                    <option value="">Any Salary</option>
                    <option value="0-20k">₹0 - ₹20k</option>
                    <option value="20k-40k">₹20k - ₹40k</option>
                    <option value="40k-60k">₹40k - ₹60k</option>
                    <option value="60k+">₹60k+</option>
                  </select>
                </div>
              </div>

              <div className="mt-4 flex gap-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleSearch}
                  disabled={loading}
                >
                  Apply Filters
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setJobType('')
                    setExperienceLevel('')
                    setSalaryRange('')
                    setSearchQuery('')
                    setLocation('')
                    fetchJobs()
                  }}
                >
                  Clear All
                </Button>
              </div>
            </motion.div>
          )}
        </Card>
      </motion.div>

      {/* Error State */}
      {error && (
        <Card padding="lg" className="mb-6 bg-red-50 border-red-200">
          <div className="flex items-center gap-3 text-red-800">
            <AlertCircle className="w-5 h-5" />
            <p>{error}</p>
          </div>
        </Card>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      )}

      {/* Quick Stats */}
      {!loading && !error && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex items-center justify-between mb-6"
        >
          <div className="flex items-center gap-4">
            <span className="text-gray-600">
              <strong className="text-gray-900">{jobs.length}</strong> jobs found
            </span>
            {jobs.some(j => j.match_score >= 0.8) && (
              <Badge variant="success" dot>High Match</Badge>
            )}
          </div>
          <span className="text-sm text-gray-500">
            Sorted by relevance
          </span>
        </motion.div>
      )}

      {/* Job Listings */}
      {!loading && !error && jobs.length > 0 && (
        <div className="space-y-4">
          {jobs.map((job, idx) => (
            <motion.div
              key={job.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + idx * 0.05 }}
            >
              <JobCard
                job={job as any}
                onApply={handleApply}
                showMatchScore
                matchScore={job.match_score}
              />
            </motion.div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && jobs.length === 0 && (
        <Card padding="lg" className="text-center py-12">
          <div className="flex flex-col items-center gap-4">
            <Search className="w-12 h-12 text-gray-400" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No jobs found</h3>
              <p className="text-gray-600">
                Try adjusting your search filters or check back later for new opportunities
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
