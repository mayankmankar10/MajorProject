import React from 'react'
import clsx from 'clsx'
import { motion } from 'framer-motion'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  subtitle?: string
  action?: React.ReactNode
}

interface CardBodyProps extends React.HTMLAttributes<HTMLDivElement> {}

interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  bordered?: boolean
}

const paddingClasses = {
  none: '',
  sm: 'p-3',
  md: 'p-6',
  lg: 'p-8',
}

export const Card: React.FC<CardProps> & {
  Header: React.FC<CardHeaderProps>
  Body: React.FC<CardBodyProps>
  Footer: React.FC<CardFooterProps>
} = ({ children, hover = false, padding = 'md', className, ...props }) => {
  return (
    <motion.div
      whileHover={hover ? { y: -4, boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)' } : {}}
      transition={{ duration: 0.2 }}
      className={clsx(
        'bg-white rounded-lg border border-slate-200',
        'shadow-sm transition-shadow',
        paddingClasses[padding],
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  )
}

const CardHeader: React.FC<CardHeaderProps> = ({
  title,
  subtitle,
  action,
  children,
  className,
  ...props
}) => {
  return (
    <div className={clsx('flex items-start justify-between', className)} {...props}>
      <div className="flex-1">
        {title && (
          <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
        )}
        {subtitle && (
          <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
        )}
        {children}
      </div>
      {action && <div className="ml-4">{action}</div>}
    </div>
  )
}

const CardBody: React.FC<CardBodyProps> = ({ children, className, ...props }) => {
  return (
    <div className={clsx('mt-4', className)} {...props}>
      {children}
    </div>
  )
}

const CardFooter: React.FC<CardFooterProps> = ({
  children,
  bordered = true,
  className,
  ...props
}) => {
  return (
    <div
      className={clsx(
        'mt-4 pt-4',
        bordered && 'border-t border-slate-200',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

Card.Header = CardHeader
Card.Body = CardBody
Card.Footer = CardFooter
