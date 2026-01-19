import React from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { User, Briefcase, ArrowRight, CheckCircle } from 'lucide-react'
import { Button } from '@/components'

export const RoleSelection: React.FC = () => {
  const navigate = useNavigate()

  const handleRoleSelect = (role: 'employee' | 'employer') => {
    navigate(`/auth/register?role=${role}`)
  }

  const employeeFeatures = [
    'Find matching job opportunities',
    'Track application status',
    'Schedule interviews',
    'AI-powered job recommendations',
    'Resume builder & optimization'
  ]

  const employerFeatures = [
    'Post unlimited job listings',
    'AI-powered candidate matching',
    'Applicant tracking system',
    'Interview scheduling',
    'Analytics & insights'
  ]

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 px-4 py-12">
      <div className="w-full max-w-6xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
            className="inline-block mb-6"
          >
            <div className="w-20 h-20 bg-gradient-to-br from-blue-600 to-purple-600 rounded-3xl flex items-center justify-center text-white font-bold text-3xl shadow-2xl">
              SS
            </div>
          </motion.div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Welcome to <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">SmartServe</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Your intelligent hiring and job search platform. Choose your role to get started.
          </p>
        </motion.div>

        {/* Role Cards */}
        <div className="grid md:grid-cols-2 gap-8 mb-8">
          {/* Employee Card */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="bg-white rounded-3xl shadow-2xl overflow-hidden hover:shadow-3xl transition-shadow duration-300"
          >
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-8 text-white">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-16 h-16 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center">
                  <User className="w-8 h-8" />
                </div>
                <div>
                  <h2 className="text-3xl font-bold">Job Seeker</h2>
                  <p className="text-blue-100">Find your dream job</p>
                </div>
              </div>
            </div>

            <div className="p-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Features for you:</h3>
              <ul className="space-y-3 mb-8">
                {employeeFeatures.map((feature, idx) => (
                  <motion.li
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 + idx * 0.1 }}
                    className="flex items-start gap-3"
                  >
                    <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">{feature}</span>
                  </motion.li>
                ))}
              </ul>

              <Button
                variant="primary"
                size="lg"
                fullWidth
                onClick={() => handleRoleSelect('employee')}
                rightIcon={<ArrowRight className="w-5 h-5" />}
              >
                Continue as Job Seeker
              </Button>

              <p className="text-center text-sm text-gray-500 mt-4">
                Perfect for professionals seeking opportunities
              </p>
            </div>
          </motion.div>

          {/* Employer Card */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="bg-white rounded-3xl shadow-2xl overflow-hidden hover:shadow-3xl transition-shadow duration-300"
          >
            <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-8 text-white">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-16 h-16 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center">
                  <Briefcase className="w-8 h-8" />
                </div>
                <div>
                  <h2 className="text-3xl font-bold">Employer</h2>
                  <p className="text-purple-100">Hire top talent</p>
                </div>
              </div>
            </div>

            <div className="p-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Features for you:</h3>
              <ul className="space-y-3 mb-8">
                {employerFeatures.map((feature, idx) => (
                  <motion.li
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 + idx * 0.1 }}
                    className="flex items-start gap-3"
                  >
                    <CheckCircle className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700">{feature}</span>
                  </motion.li>
                ))}
              </ul>

              <Button
                variant="secondary"
                size="lg"
                fullWidth
                onClick={() => handleRoleSelect('employer')}
                rightIcon={<ArrowRight className="w-5 h-5" />}
              >
                Continue as Employer
              </Button>

              <p className="text-center text-sm text-gray-500 mt-4">
                Ideal for companies and recruiters
              </p>
            </div>
          </motion.div>
        </div>

        {/* Already have account */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="text-center"
        >
          <p className="text-gray-600">
            Already have an account?{' '}
            <button
              onClick={() => navigate('/auth/login')}
              className="text-blue-600 hover:text-blue-700 font-semibold underline"
            >
              Sign in here
            </button>
          </p>
        </motion.div>

        {/* Stats Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="grid grid-cols-3 gap-6 mt-12 max-w-3xl mx-auto"
        >
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600 mb-1">10K+</div>
            <div className="text-sm text-gray-600">Active Jobs</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600 mb-1">5K+</div>
            <div className="text-sm text-gray-600">Companies</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600 mb-1">50K+</div>
            <div className="text-sm text-gray-600">Job Seekers</div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
