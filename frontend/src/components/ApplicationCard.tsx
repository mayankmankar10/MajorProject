import React from 'react'
import { Link } from 'react-router-dom'
import { MapPin, Calendar, Star, Clock } from 'lucide-react'
import { Card } from './Card'
import { Badge } from './Badge'
import { Button } from './Button'
import { Application } from '../types'
import { format } from 'date-fns'

interface ApplicationCardProps {
  application: Application
  onViewDetails?: (appId: number) => void
}

const statusVariants = {
  applied: 'default' as const,
  reviewing: 'info' as const,
  interview_scheduled: 'warning' as const,
  selected: 'success' as const,
  rejected: 'danger' as const,
  hired: 'success' as const,
}

const statusLabels = {
  applied: 'Applied',
  reviewing: 'Under Review',
  interview_scheduled: 'Interview Scheduled',
  selected: 'Selected',
  rejected: 'Rejected',
  hired: 'Hired',
}

export const ApplicationCard: React.FC<ApplicationCardProps> = ({
  application,
  onViewDetails,
}) => {
  return (
    <Card padding="md" className="transition-all hover:shadow-md">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <Link
            to={`/jobs/${application.job_id}`}
            className="text-lg font-semibold text-slate-900 hover:text-primary-600 transition-colors"
          >
            {application.job?.title || 'Job Title'}
          </Link>
          {application.job?.location && (
            <div className="flex items-center gap-2 mt-1 text-sm text-slate-600">
              <MapPin className="w-4 h-4" />
              <span>{application.job.location}</span>
            </div>
          )}
        </div>
        <Badge variant={statusVariants[application.status as keyof typeof statusVariants]} dot>
          {statusLabels[application.status as keyof typeof statusLabels]}
        </Badge>
      </div>

      <div className="flex flex-wrap gap-3 mb-4 text-sm text-slate-600">
        <div className="flex items-center gap-1">
          <Calendar className="w-4 h-4" />
          <span>Applied {format(new Date(application.applied_at), 'MMM d, yyyy')}</span>
        </div>
        {application.match_score !== null && (
          <div className="flex items-center gap-1">
            <Star className="w-4 h-4 text-primary-600" />
            <span className="font-medium text-primary-600">
              {Math.round(application.match_score)}% Match
            </span>
          </div>
        )}
      </div>

      {application.cover_letter && (
        <p className="text-sm text-slate-600 mb-4 line-clamp-2">
          {application.cover_letter}
        </p>
      )}

      {application.notes && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg mb-4">
          <p className="text-xs font-medium text-amber-900 mb-1">Employer Note:</p>
          <p className="text-sm text-amber-800">{application.notes}</p>
        </div>
      )}

      <div className="flex items-center justify-between pt-4 border-t border-slate-200">
        <div className="flex items-center gap-1 text-xs text-slate-500">
          <Clock className="w-3 h-3" />
          {application.reviewed_at
            ? `Reviewed ${format(new Date(application.reviewed_at), 'MMM d')}`
            : 'Awaiting review'}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onViewDetails && onViewDetails(application.id)}
        >
          View Details
        </Button>
      </div>
    </Card>
  )
}
