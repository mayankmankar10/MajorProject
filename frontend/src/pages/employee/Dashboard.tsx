import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Briefcase, FileText, Calendar, TrendingUp, Sparkles, MessageSquare, X } from 'lucide-react'
import { Card } from '@/components'
import { useAuthStore } from '@/stores/useAuthStore'
import { Link } from 'react-router-dom'

export const EmployeeDashboard: React.FC = () => {
  const { user } = useAuthStore()
  const [showWelcome, setShowWelcome] = useState(false)

  // Check if user is new (registered within last 24 hours or first login)
  useEffect(() => {
    // For now, show welcome banner for all users on first visit to dashboard
    // In production, check user's created_at date or a "has_seen_welcome" flag
    const hasSeenWelcome = localStorage.getItem('hasSeenWelcome')
    if (!hasSeenWelcome) {
      setShowWelcome(true)
    }
  }, [])

  const handleDismissWelcome = () => {
    setShowWelcome(false)
    localStorage.setItem('hasSeenWelcome', 'true')
  }

  const stats = [
    { label: 'Applications', value: '12', icon: FileText, color: 'blue' },
    { label: 'Interviews', value: '3', icon: Calendar, color: 'purple' },
    { label: 'Job Matches', value: '45', icon: Briefcase, color: 'green' },
    { label: 'Profile Views', value: '89', icon: TrendingUp, color: 'orange' }
  ]

  return (
    <div>
      {/* Welcome Banner for New Employees */}
      <AnimatePresence>
        {showWelcome && (
          <motion.div
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            transition={{ duration: 0.3 }}
            className="mb-6"
          >
            <div className="relative bg-gradient-to-r from-primary-500 via-primary-600 to-secondary-600 rounded-2xl p-8 text-white shadow-xl overflow-hidden">
              {/* Background decoration */}
              <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
              <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full translate-y-1/2 -translate-x-1/2" />

              {/* Close button */}
              <button
                onClick={handleDismissWelcome}
                className="absolute top-4 right-4 p-2 hover:bg-white/20 rounded-lg transition-colors"
                aria-label="Dismiss welcome message"
              >
                <X className="w-5 h-5" />
              </button>

              {/* Content */}
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-4">
                  <Sparkles className="w-8 h-8" />
                  <h2 className="text-3xl font-bold">Welcome to SmartServe! 🎉</h2>
                </div>

                <p className="text-lg text-white/90 mb-6 max-w-2xl">
                  We're excited to have you here, {user?.email?.split('@')[0]}! Let's get you started on your journey to finding the perfect restaurant job.
                </p>

                <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 mb-6 border border-white/20">
                  <h3 className="text-xl font-semibold mb-3 flex items-center gap-2">
                    <MessageSquare className="w-6 h-6" />
                    Quick Start: Chat with Our AI Assistant
                  </h3>
                  <p className="text-white/90 mb-4">
                    Our AI assistant will help you complete your profile, discover your strengths, and find jobs that match your skills and preferences. It's fast, easy, and conversational!
                  </p>
                  <ul className="space-y-2 text-white/90 mb-4">
                    <li className="flex items-start gap-2">
                      <span className="text-white">✓</span>
                      <span>Share your experience and skills</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-white">✓</span>
                      <span>Tell us your work preferences</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-white">✓</span>
                      <span>Get personalized job recommendations</span>
                    </li>
                  </ul>
                </div>

                <Link
                  to="/employee/chat"
                  className="inline-flex items-center gap-2 bg-white text-primary-600 px-6 py-3 rounded-lg font-semibold hover:bg-white/90 transition-all shadow-lg hover:shadow-xl hover:scale-105"
                >
                  <MessageSquare className="w-5 h-5" />
                  Start Chat & Complete Profile
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {showWelcome ? 'Your Dashboard' : 'Welcome Back! 👋'}
        </h1>
        <p className="text-gray-600">Here's what's happening with your job search</p>
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

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card padding="lg">
          <Card.Header
            title="Quick Actions"
            subtitle="Get started with these common tasks"
          />
          <Card.Body>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button className="p-4 border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all text-left">
                <Briefcase className="w-8 h-8 text-blue-600 mb-2" />
                <h3 className="font-semibold text-gray-900 mb-1">Browse Jobs</h3>
                <p className="text-sm text-gray-600">Find matching opportunities</p>
              </button>
              <button className="p-4 border-2 border-gray-200 rounded-xl hover:border-purple-500 hover:bg-purple-50 transition-all text-left">
                <FileText className="w-8 h-8 text-purple-600 mb-2" />
                <h3 className="font-semibold text-gray-900 mb-1">My Applications</h3>
                <p className="text-sm text-gray-600">Track your progress</p>
              </button>
              <button className="p-4 border-2 border-gray-200 rounded-xl hover:border-green-500 hover:bg-green-50 transition-all text-left">
                <Calendar className="w-8 h-8 text-green-600 mb-2" />
                <h3 className="font-semibold text-gray-900 mb-1">Upcoming Interviews</h3>
                <p className="text-sm text-gray-600">Prepare for success</p>
              </button>
            </div>
          </Card.Body>
        </Card>
      </motion.div>
    </div>
  )
}
