import React from 'react'
import { Calendar, Clock, MapPin, Video, CheckCircle, XCircle } from 'lucide-react'
import { Card } from './Card'
import { Badge } from './Badge'
import { Button } from './Button'
import { Interview } from '@types'
import { format } from 'date-fns'

interface InterviewCardProps {
  interview: Interview
  onConfirm?: (interviewId: number) => void
  onCancel?: (interviewId: number) => void
  onJoin?: (meetingLink: string) => void
}

const statusVariants = {
  scheduled: 'warning' as const,
  confirmed: 'info' as const,
  completed: 'success' as const,
  cancelled: 'danger' as const,
}

const statusLabels = {
  scheduled: 'Scheduled',
  confirmed: 'Confirmed',
  completed: 'Completed',
  cancelled: 'Cancelled',
}

export const InterviewCard: React.FC<InterviewCardProps> = ({
  interview,
  onConfirm,
  onCancel,
  onJoin,
}) => {
  const interviewDate = new Date(interview.scheduled_at)
  const isPast = interviewDate < new Date()
  const isUpcoming = !isPast && interview.status === 'confirmed'

  return (
    <Card padding="md" className={isUpcoming ? 'border-2 border-primary-500' : ''}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-slate-900 mb-1">
            Interview Scheduled
          </h3>
          <Badge variant={statusVariants[interview.status]} dot size="sm">
            {statusLabels[interview.status]}
          </Badge>
        </div>
        {isUpcoming && (
          <Badge variant="primary" size="sm">
            Upcoming
          </Badge>
        )}
      </div>

      <div className="space-y-3 mb-4">
        <div className="flex items-center gap-3 text-sm text-slate-700">
          <Calendar className="w-4 h-4 text-slate-400" />
          <span className="font-medium">
            {format(interviewDate, 'EEEE, MMMM d, yyyy')}
          </span>
        </div>

        <div className="flex items-center gap-3 text-sm text-slate-700">
          <Clock className="w-4 h-4 text-slate-400" />
          <span>
            {format(interviewDate, 'h:mm a')} ({interview.duration_minutes} minutes)
          </span>
        </div>

        {interview.location && (
          <div className="flex items-center gap-3 text-sm text-slate-700">
            <MapPin className="w-4 h-4 text-slate-400" />
            <span>{interview.location}</span>
          </div>
        )}

        {interview.meeting_link && (
          <div className="flex items-center gap-3 text-sm text-primary-600">
            <Video className="w-4 h-4" />
            <span className="font-medium">Video Interview</span>
          </div>
        )}
      </div>

      {interview.interviewer_notes && (
        <div className="p-3 bg-slate-50 rounded-lg mb-4">
          <p className="text-xs font-medium text-slate-700 mb-1">Notes:</p>
          <p className="text-sm text-slate-600">{interview.interviewer_notes}</p>
        </div>
      )}

      {interview.feedback && interview.status === 'completed' && (
        <div className="p-3 bg-success-50 border border-success-200 rounded-lg mb-4">
          <p className="text-xs font-medium text-success-900 mb-1">Feedback:</p>
          <p className="text-sm text-success-800">{interview.feedback}</p>
        </div>
      )}

      <div className="flex items-center justify-between pt-4 border-t border-slate-200">
        <div className="text-xs text-slate-500">
          Created {format(new Date(interview.created_at), 'MMM d, yyyy')}
        </div>

        <div className="flex gap-2">
          {interview.status === 'scheduled' && onConfirm && (
            <Button
              variant="primary"
              size="sm"
              leftIcon={<CheckCircle className="w-4 h-4" />}
              onClick={() => onConfirm(interview.id)}
            >
              Confirm
            </Button>
          )}

          {interview.status === 'confirmed' && interview.meeting_link && onJoin && (
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Video className="w-4 h-4" />}
              onClick={() => onJoin(interview.meeting_link)}
            >
              Join Meeting
            </Button>
          )}

          {(interview.status === 'scheduled' || interview.status === 'confirmed') &&
            onCancel && (
              <Button
                variant="danger"
                size="sm"
                leftIcon={<XCircle className="w-4 h-4" />}
                onClick={() => onCancel(interview.id)}
              >
                Cancel
              </Button>
            )}
        </div>
      </div>
    </Card>
  )
}
