import React from 'react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Card } from './Card'
import { cn } from '@/utils'

interface StatsCardProps {
  title: string
  value: string | number
  change?: string
  changeType?: 'increase' | 'decrease' | 'neutral'
  icon?: React.ReactNode
  className?: string
}

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  change,
  changeType = 'neutral',
  icon,
  className,
}) => {
  const changeColors = {
    increase: 'text-green-600',
    decrease: 'text-red-600',
    neutral: 'text-gray-600',
  }

  return (
    <Card className={cn('p-6', className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
          {change && (
            <p className={cn('text-sm mt-2', changeColors[changeType])}>
              {change}
            </p>
          )}
        </div>
        {icon && (
          <div className="p-3 bg-blue-50 rounded-lg text-blue-600">
            {icon}
          </div>
        )}
      </div>
    </Card>
  )
}

interface ApplicationTrendData {
  name: string
  applications: number
  interviews: number
}

interface ApplicationTrendChartProps {
  data: ApplicationTrendData[]
  className?: string
}

export const ApplicationTrendChart: React.FC<ApplicationTrendChartProps> = ({
  data,
  className,
}) => {
  return (
    <Card className={cn('p-6', className)}>
      <h3 className="text-lg font-semibold text-gray-900 mb-6">
        Application Trends
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="name" stroke="#9ca3af" />
          <YAxis stroke="#9ca3af" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="applications"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6' }}
            name="Applications"
          />
          <Line
            type="monotone"
            dataKey="interviews"
            stroke="#a855f7"
            strokeWidth={2}
            dot={{ fill: '#a855f7' }}
            name="Interviews"
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  )
}

interface MatchScoreData {
  range: string
  count: number
}

interface MatchScoreDistributionProps {
  data: MatchScoreData[]
  className?: string
}

export const MatchScoreDistribution: React.FC<MatchScoreDistributionProps> = ({
  data,
  className,
}) => {
  return (
    <Card className={cn('p-6', className)}>
      <h3 className="text-lg font-semibold text-gray-900 mb-6">
        Match Score Distribution
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="range" stroke="#9ca3af" />
          <YAxis stroke="#9ca3af" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]} name="Candidates" />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  )
}

interface ApplicationStatusData {
  name: string
  value: number
  color: string
}

interface ApplicationStatusChartProps {
  data: ApplicationStatusData[]
  className?: string
}

export const ApplicationStatusChart: React.FC<ApplicationStatusChartProps> = ({
  data,
  className,
}) => {
  const COLORS = ['#3b82f6', '#f59e0b', '#a855f7', '#22c55e', '#ef4444']

  return (
    <Card className={cn('p-6', className)}>
      <h3 className="text-lg font-semibold text-gray-900 mb-6">
        Application Status
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </Card>
  )
}

interface JobPerformanceData {
  job: string
  applications: number
  hires: number
}

interface JobPerformanceChartProps {
  data: JobPerformanceData[]
  className?: string
}

export const JobPerformanceChart: React.FC<JobPerformanceChartProps> = ({
  data,
  className,
}) => {
  return (
    <Card className={cn('p-6', className)}>
      <h3 className="text-lg font-semibold text-gray-900 mb-6">
        Job Performance
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis type="number" stroke="#9ca3af" />
          <YAxis type="category" dataKey="job" stroke="#9ca3af" width={150} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Bar dataKey="applications" fill="#3b82f6" name="Applications" />
          <Bar dataKey="hires" fill="#22c55e" name="Hires" />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  )
}

interface ActivityTimelineProps {
  activities: Array<{
    id: number
    type: string
    title: string
    description: string
    timestamp: string
    icon?: React.ReactNode
  }>
  className?: string
}

export const ActivityTimeline: React.FC<ActivityTimelineProps> = ({
  activities,
  className,
}) => {
  return (
    <Card className={cn('p-6', className)}>
      <h3 className="text-lg font-semibold text-gray-900 mb-6">
        Recent Activity
      </h3>
      <div className="space-y-6">
        {activities.length === 0 ? (
          <p className="text-center text-gray-400 py-8">No recent activity</p>
        ) : (
          activities.map((activity, index) => (
            <div key={activity.id} className="flex gap-4">
              <div className="flex flex-col items-center">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600">
                  {activity.icon || (
                    <div className="w-3 h-3 bg-blue-600 rounded-full" />
                  )}
                </div>
                {index < activities.length - 1 && (
                  <div className="w-0.5 h-full bg-gray-200 my-2" />
                )}
              </div>
              <div className="flex-1 pb-6">
                <p className="font-medium text-gray-900">{activity.title}</p>
                <p className="text-sm text-gray-500 mt-1">{activity.description}</p>
                <p className="text-xs text-gray-400 mt-2">{activity.timestamp}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  )
}
