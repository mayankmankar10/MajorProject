import React from 'react'
import clsx from 'clsx'

export type BadgeVariant = 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info'
export type BadgeSize = 'sm' | 'md' | 'lg'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
  size?: BadgeSize
  dot?: boolean
  removable?: boolean
  onRemove?: () => void
}

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-slate-100 text-slate-800 border-slate-300',
  primary: 'bg-primary-100 text-primary-800 border-primary-300',
  success: 'bg-success-100 text-success-800 border-success-300',
  warning: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  danger: 'bg-danger-100 text-danger-800 border-danger-300',
  info: 'bg-blue-100 text-blue-800 border-blue-300',
}

const sizeClasses: Record<BadgeSize, string> = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-0.5',
  lg: 'text-base px-3 py-1',
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  size = 'md',
  dot = false,
  removable = false,
  onRemove,
  children,
  className,
  ...props
}) => {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 font-medium rounded-full border',
        'transition-colors',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {dot && (
        <span
          className={clsx(
            'w-1.5 h-1.5 rounded-full',
            variant === 'default' && 'bg-slate-600',
            variant === 'primary' && 'bg-primary-600',
            variant === 'success' && 'bg-success-600',
            variant === 'warning' && 'bg-yellow-600',
            variant === 'danger' && 'bg-danger-600',
            variant === 'info' && 'bg-blue-600'
          )}
        />
      )}
      {children}
      {removable && onRemove && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
          className="hover:bg-black/10 rounded-full p-0.5 transition-colors"
          aria-label="Remove badge"
        >
          <svg
            className="w-3 h-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      )}
    </span>
  )
}
