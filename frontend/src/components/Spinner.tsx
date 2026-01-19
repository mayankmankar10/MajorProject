import React from 'react'
import clsx from 'clsx'
import { motion } from 'framer-motion'

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  color?: 'primary' | 'secondary' | 'white'
  fullScreen?: boolean
  text?: string
}

const sizeClasses = {
  sm: 'w-4 h-4 border-2',
  md: 'w-8 h-8 border-2',
  lg: 'w-12 h-12 border-3',
  xl: 'w-16 h-16 border-4',
}

const colorClasses = {
  primary: 'border-primary-600 border-t-transparent',
  secondary: 'border-secondary-600 border-t-transparent',
  white: 'border-white border-t-transparent',
}

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  color = 'primary',
  fullScreen = false,
  text,
}) => {
  const spinner = (
    <div className="flex flex-col items-center justify-center gap-3">
      <motion.div
        className={clsx('rounded-full', sizeClasses[size], colorClasses[color])}
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      />
      {text && <p className="text-sm text-slate-600">{text}</p>}
    </div>
  )

  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm z-50">
        {spinner}
      </div>
    )
  }

  return spinner
}
