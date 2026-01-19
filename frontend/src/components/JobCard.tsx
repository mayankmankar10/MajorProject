import React from 'react'
import { Link } from 'react-router-dom'
import { MapPin, Briefcase, DollarSign, Clock, Star } from 'lucide-react'
import { Card } from './Card'
import { Badge } from './Badge'
import { Button } from './Button'
import { Job } from '@/types'
import { format } from 'date-fns'

interface JobCardProps {
  job: Job
  onApply?: (jobId: number, matchScore?: number) => void
  showMatchScore?: boolean
  matchScore?: number
  isApplied?: boolean
}

export const JobCard: React.FC<JobCardProps> = ({
  job,
  onApply,
  showMatchScore = false,
  matchScore,
  isApplied = false,
}) => {
  const jobTypeLabels: Record<string, string> = {
    full_time: 'Full Time',
    part_time: 'Part Time',
    contract: 'Contract',
    internship: 'Internship',
  }

  return (
    <Card hover padding="md" className="h-full flex flex-col">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <Link
            to={`/jobs/${job.id}`}
            className="text-lg font-semibold text-slate-900 hover:text-primary-600 transition-colors"
          >
            {job.title}
          </Link>
          <div className="flex items-center gap-2 mt-1 text-sm text-slate-600">
            <MapPin className="w-4 h-4" />
            <span>{job.location}</span>
          </div>
        </div>
        {showMatchScore && matchScore !== undefined && (
          <div className="flex items-center gap-1 px-3 py-1 bg-primary-50 rounded-full">
            <Star className="w-4 h-4 text-primary-600 fill-primary-600" />
            <span className="text-sm font-semibold text-primary-700">
              {Math.round(matchScore * 100)}%
            </span>
          </div>
        )}
      </div>

      <p className="text-sm text-slate-600 mb-4 line-clamp-2">
        {job.description}
      </p>

      <div className="flex flex-wrap gap-2 mb-4">
        <Badge variant="default" size="sm">
          <Briefcase className="w-3 h-3" />
          {jobTypeLabels[job.job_type]}
        </Badge>
        {job.salary_range && (
          <Badge variant="info" size="sm">
            <DollarSign className="w-3 h-3" />
            {job.salary_range}
          </Badge>
        )}
        <Badge variant="default" size="sm">
          <Clock className="w-3 h-3" />
          {(job as any).posted_time || format(new Date(job.created_at), 'MMM d, yyyy')}
        </Badge>
      </div>

      {job.requirements?.skills && (
        <div className="mb-4">
          <p className="text-xs font-medium text-slate-700 mb-2">Required Skills:</p>
          <div className="flex flex-wrap gap-1">
            {job.requirements.skills.slice(0, 5).map((skill: string, index: number) => (
              <span
                key={index}
                className="px-2 py-1 text-xs bg-slate-100 text-slate-700 rounded-md"
              >
                {skill}
              </span>
            ))}
            {job.requirements.skills.length > 5 && (
              <span className="px-2 py-1 text-xs bg-slate-100 text-slate-700 rounded-md">
                +{job.requirements.skills.length - 5} more
              </span>
            )}
          </div>
        </div>
      )}

      <div className="mt-auto pt-4 border-t border-slate-200">
        <div className="flex items-center justify-between">
          {isApplied ? (
            <Badge variant="success" dot>
              Applied
            </Badge>
          ) : (
            <span className="text-xs text-slate-500">
              {job.is_active ? 'Accepting applications' : 'Closed'}
            </span>
          )}
          <div className="flex gap-2">
            <Link to={`/jobs/${job.id}`}>
              <Button variant="outline" size="sm">
                View Details
              </Button>
            </Link>
            {onApply && !isApplied && job.is_active && (
              <Button variant="primary" size="sm" onClick={() => onApply(job.id, matchScore)}>
                Apply Now
              </Button>
            )}
          </div>
        </div>
      </div>
    </Card>
  )
}
