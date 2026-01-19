import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Briefcase, Users, Calendar, TrendingUp, Loader } from 'lucide-react'
import { Card } from '@/components'
import { apiClient } from '@/services/api'

export const EmployerDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setIsLoading(true)
        const response = await apiClient.getDashboardMetrics()
        setAnalytics(response)
      } catch (err: any) {
        setError(err)
      } finally {
        setIsLoading(false)
      }
    }
    fetchAnalytics()
  }, [])

  const stats = [
    {
      label: 'Active Jobs',
      value: analytics?.active_jobs || '0',
      icon: Briefcase,
      color: 'blue'
    },
    {
      label: 'Total Applications',
      value: analytics?.total_applications || '0',
      icon: Users,
      color: 'purple'
    },
    {
      label: 'Upcoming Interviews',
      value: analytics?.upcoming_interviews || '0',
      icon: Calendar,
      color: 'green'
    },
    {
      label: 'Recent Applications (7d)',
      value: analytics?.recent_applications_7d || '0',
      icon: TrendingUp,
      color: 'orange'
    }
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Failed to load dashboard analytics. Please try again.</p>
      </div>
    )
  }

  return (
    <div>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Employer Dashboard 📊</h1>
        <p className="text-gray-600">
          {analytics?.company_name ? `Welcome to ${analytics.company_name}` : 'Manage your hiring process efficiently'}
        </p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, idx) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
          >
            <Card padding="md" hover>
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-xl bg-${stat.color}-100`}>
                  <stat.icon className={`w-6 h-6 text-${stat.color}-600`} />
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
                  <div className="text-sm text-gray-600">{stat.label}</div>
                </div>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Application Status Breakdown */}
      {analytics?.applications_by_status && Object.keys(analytics.applications_by_status).length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-8"
        >
          <Card padding="lg">
            <Card.Header
              title="Application Status"
              subtitle="Breakdown of applications by status"
            />
            <Card.Body>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(analytics.applications_by_status).map(([status, count]) => (
                  <div key={status} className="text-center p-4 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">{count as number}</div>
                    <div className="text-sm text-gray-600 capitalize">{status.replace('_', ' ')}</div>
                  </div>
                ))}
              </div>
            </Card.Body>
          </Card>
        </motion.div>
      )}

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <Card padding="lg">
          <Card.Header
            title="Quick Actions"
            subtitle="Streamline your hiring workflow"
          />
          <Card.Body>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={() => window.location.href = '/employer/jobs'}
                className="p-4 border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all text-left"
              >
                <Briefcase className="w-8 h-8 text-blue-600 mb-2" />
                <h3 className="font-semibold text-gray-900 mb-1">View Jobs</h3>
                <p className="text-sm text-gray-600">Manage job listings</p>
              </button>
              <button
                onClick={() => window.location.href = '/employer/candidates'}
                className="p-4 border-2 border-gray-200 rounded-xl hover:border-purple-500 hover:bg-purple-50 transition-all text-left"
              >
                <Users className="w-8 h-8 text-purple-600 mb-2" />
                <h3 className="font-semibold text-gray-900 mb-1">View Applications</h3>
                <p className="text-sm text-gray-600">Review applications</p>
              </button>
              <button
                onClick={() => window.location.href = '/employer/interviews'}
                className="p-4 border-2 border-gray-200 rounded-xl hover:border-green-500 hover:bg-green-50 transition-all text-left"
              >
                <Calendar className="w-8 h-8 text-green-600 mb-2" />
                <h3 className="font-semibold text-gray-900 mb-1">Schedule Interviews</h3>
                <p className="text-sm text-gray-600">Manage interviews</p>
              </button>
            </div>
          </Card.Body>
        </Card>
      </motion.div>
    </div>
  )
}
