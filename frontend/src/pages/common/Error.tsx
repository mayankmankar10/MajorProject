import React from 'react'
import { useNavigate, useRouteError } from 'react-router-dom'
import { motion } from 'framer-motion'
import { AlertTriangle, Home, RefreshCw } from 'lucide-react'
import { Button } from '@/components'

export const ErrorPage: React.FC = () => {
  const navigate = useNavigate()
  const error = useRouteError() as any

  const handleRefresh = () => {
    window.location.reload()
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 via-orange-50 to-yellow-50 px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="text-center max-w-2xl"
      >
        {/* Error Icon */}
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ delay: 0.2, type: 'spring' }}
          className="inline-flex items-center justify-center w-32 h-32 bg-white rounded-full shadow-xl mb-8"
        >
          <AlertTriangle className="w-16 h-16 text-red-500" />
        </motion.div>

        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Oops! Something Went Wrong
          </h1>
          <p className="text-lg text-gray-600 mb-2">
            We're sorry, but an unexpected error occurred.
          </p>
          <p className="text-sm text-gray-500 mb-8">
            Don't worry, our team has been notified and is working on it.
          </p>
        </motion.div>

        {/* Error Details (Development Only) */}
        {error && import.meta.env.DEV && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-xl shadow-lg p-6 mb-8 text-left"
          >
            <h3 className="text-sm font-semibold text-red-600 mb-2">Error Details:</h3>
            <pre className="text-xs text-gray-700 overflow-auto max-h-40">
              {error.statusText || error.message || JSON.stringify(error, null, 2)}
            </pre>
          </motion.div>
        )}

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="flex flex-col sm:flex-row gap-4 justify-center"
        >
          <Button
            variant="primary"
            size="lg"
            onClick={handleRefresh}
            leftIcon={<RefreshCw className="w-5 h-5" />}
          >
            Try Again
          </Button>
          <Button
            variant="outline"
            size="lg"
            onClick={() => navigate('/')}
            leftIcon={<Home className="w-5 h-5" />}
          >
            Go Home
          </Button>
        </motion.div>

        {/* Help Text */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-12 pt-8 border-t border-gray-200"
        >
          <p className="text-sm text-gray-600 mb-2">
            If this problem persists, please contact support
          </p>
          <a
            href="mailto:support@smartserve.com"
            className="text-sm text-blue-600 hover:text-blue-700 font-medium hover:underline"
          >
            support@smartserve.com
          </a>
        </motion.div>
      </motion.div>
    </div>
  )
}
