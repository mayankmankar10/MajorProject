import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Calendar, Video, Clock } from 'lucide-react'
import { InterviewCard, Button, Card } from '@/components'
import { apiClient } from '@/services/api'

export const Interviews: React.FC = () => {
  const [filter, setFilter] = useState<'upcoming' | 'past'>('upcoming')
  const [interviews, setInterviews] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchInterviews = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await apiClient.getEmployeeInterviews()
        setInterviews(data)
      } catch (err: any) {
        console.error('Error fetching interviews:', err)
        setError(err.response?.data?.detail || 'Failed to load interviews')
        setInterviews([])
      } finally {
        setLoading(false)
      }
    }

    fetchInterviews()
  }, [])

  const upcomingInterviews = interviews.filter(interview =>
    new Date(interview.scheduled_at) >= new Date() && interview.status !== 'completed'
  )

  const pastInterviews = interviews.filter(interview =>
    new Date(interview.scheduled_at) < new Date() || interview.status === 'completed'
  )

  const displayedInterviews = filter === 'upcoming' ? upcomingInterviews : pastInterviews

  const handleConfirm = (interviewId: number) => {
    console.log('Confirming interview:', interviewId)
  }

  const handleJoin = (meetingLink: string) => {
    if (meetingLink) {
      window.open(meetingLink, '_blank')
    }
  }

  const handleCancel = (interviewId: number) => {
    console.log('Cancelling interview:', interviewId)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">Loading interviews...</div>
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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">My Interviews</h1>
        <p className="text-gray-600">Manage and prepare for your upcoming interviews</p>
      </motion.div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg"
        >
          <p className="text-red-800">{error}</p>
        </motion.div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card padding="md" hover>
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-blue-100">
                <Calendar className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900">{upcomingInterviews.length}</div>
                <div className="text-sm text-gray-600">Upcoming</div>
              </div>
            </div>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
          <Card padding="md" hover>
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-green-100">
                <Video className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {upcomingInterviews.filter(i => i.status === 'scheduled').length}
                </div>
                <div className="text-sm text-gray-600">Scheduled</div>
              </div>
            </div>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Card padding="md" hover>
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-purple-100">
                <Clock className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900">{pastInterviews.length}</div>
                <div className="text-sm text-gray-600">Completed</div>
              </div>
            </div>
          </Card>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="flex gap-2 mb-6"
      >
        <Button
          variant={filter === 'upcoming' ? 'primary' : 'outline'}
          size="md"
          onClick={() => setFilter('upcoming')}
        >
          Upcoming ({upcomingInterviews.length})
        </Button>
        <Button
          variant={filter === 'past' ? 'primary' : 'outline'}
          size="md"
          onClick={() => setFilter('past')}
        >
          Past ({pastInterviews.length})
        </Button>
      </motion.div>

      {displayedInterviews.length > 0 ? (
        <div className="space-y-4">
          {displayedInterviews.map((interview, idx) => {
            // Pass the interview data directly - the API response matches what InterviewCard expects
            const interviewData = {
              id: interview.id,
              application_id: interview.application_id,
              scheduled_at: interview.scheduled_at,
              duration_minutes: interview.duration_minutes,
              location: interview.location || '',
              meeting_link: interview.meeting_link || '',
              calendar_link: '',  // Not returned by API, provide default
              status: interview.status as 'scheduled' | 'confirmed' | 'completed' | 'cancelled',
              interviewer_notes: interview.interviewer_notes || '',
              feedback: interview.feedback || '',
              created_at: interview.created_at || interview.scheduled_at, // Fallback to scheduled_at if no created_at
              updated_at: interview.updated_at || ''
            }

            return (
              <motion.div
                key={interview.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + idx * 0.1 }}
              >
                <InterviewCard
                  interview={interviewData}
                  onConfirm={handleConfirm}
                  onJoin={handleJoin}
                  onCancel={handleCancel}
                />
              </motion.div>
            )
          })}
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card padding="lg" className="text-center">
            <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No {filter} interviews
            </h3>
            <p className="text-gray-600 mb-6">
              {filter === 'upcoming'
                ? "You don't have any scheduled interviews yet. Keep applying to jobs!"
                : "You haven't completed any interviews yet."
              }
            </p>
            {filter === 'upcoming' && (
              <Button variant="primary" size="md">
                Browse Jobs
              </Button>
            )}
          </Card>
        </motion.div>
      )}

      {upcomingInterviews.length > 0 && filter === 'upcoming' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="mt-8"
        >
          <Card padding="lg" className="bg-green-50 border-green-200">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-green-100 rounded-xl">
                <Video className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Interview Preparation Tips</h3>
                <ul className="text-sm text-gray-700 space-y-1">
                  <li>• Test your camera and microphone 15 minutes before video interviews</li>
                  <li>• Prepare examples using the STAR method (Situation, Task, Action, Result)</li>
                  <li>• Research the company, role, and interviewer on LinkedIn</li>
                  <li>• Prepare thoughtful questions to ask the interviewer</li>
                  <li>• Have a notepad ready to take notes during the interview</li>
                  <li>• Dress professionally, even for video interviews</li>
                </ul>
              </div>
            </div>
          </Card>
        </motion.div>
      )}
    </div>
  )
}

export default Interviews
