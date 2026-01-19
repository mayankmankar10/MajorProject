import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Briefcase,
  Users,
  MessageSquare,
  Calendar,
  FileText,
  BarChart3,
  Search,
  ClipboardList,
  Gift,
} from 'lucide-react'
import clsx from 'clsx'
import { useAuthStore } from '@stores/useAuthStore'

interface NavItem {
  name: string
  path: string
  icon: React.ReactNode
  roles?: ('employer' | 'employee')[]
}

const employerNavItems: NavItem[] = [
  { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
  { name: 'Jobs', path: '/jobs', icon: <Briefcase className="w-5 h-5" /> },
  { name: 'Candidates', path: '/candidates', icon: <Users className="w-5 h-5" /> },
  { name: 'Interviews', path: '/interviews', icon: <Calendar className="w-5 h-5" /> },
  { name: 'Analytics', path: '/analytics', icon: <BarChart3 className="w-5 h-5" /> },
  { name: 'Onboarding', path: '/onboarding', icon: <FileText className="w-5 h-5" /> },
  { name: 'AI Chat', path: '/chat', icon: <MessageSquare className="w-5 h-5" /> },
]


const employeeNavItems: NavItem[] = [
  { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
  { name: 'Find Jobs', path: '/jobs', icon: <Search className="w-5 h-5" /> },
  { name: 'Applications', path: '/applications', icon: <ClipboardList className="w-5 h-5" /> },
  { name: 'Offers', path: '/offers', icon: <Gift className="w-5 h-5" /> },
  { name: 'Interviews', path: '/interviews', icon: <Calendar className="w-5 h-5" /> },
  { name: 'Onboarding', path: '/onboarding', icon: <FileText className="w-5 h-5" /> },
  { name: 'AI Chat', path: '/chat', icon: <MessageSquare className="w-5 h-5" /> },
]

interface SidebarProps {
  isOpen?: boolean
  onClose?: () => void
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen = true, onClose }) => {
  const location = useLocation()
  const { user } = useAuthStore()

  const rolePrefix = user?.role === 'employer' ? '/employer' : '/employee'
  const navItems = user?.role === 'employer' ? employerNavItems : employeeNavItems

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed top-16 left-0 h-[calc(100vh-4rem)] w-64 bg-white border-r border-slate-200 z-40',
          'transition-transform duration-300 ease-in-out',
          // On large screens: show when open, hide when closed
          // On small screens: hide by default, show only when explicitly opened
          {
            'translate-x-0': isOpen,
            '-translate-x-full': !isOpen,
            'lg:translate-x-0': isOpen, // Show on desktop when open
          }
        )}
      >
        <nav className="h-full overflow-y-auto p-4">
          <div className="space-y-1">
            {navItems.map((item) => {
              const fullPath = `${rolePrefix}${item.path}`
              const isActive = location.pathname === fullPath
              return (
                <Link
                  key={item.path}
                  to={fullPath}
                  onClick={onClose}
                  className={clsx(
                    'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                    'text-sm font-medium',
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-slate-700 hover:bg-slate-100 hover:text-slate-900'
                  )}
                >
                  {item.icon}
                  {item.name}
                </Link>
              )
            })}
          </div>

          {/* Help Section */}
          <div className="mt-8 p-4 bg-slate-50 rounded-lg">
            <h4 className="text-sm font-semibold text-slate-900 mb-2">Need Help?</h4>
            <p className="text-xs text-slate-600 mb-3">
              Our AI assistant is here to help you with any questions.
            </p>
            <Link
              to={`${rolePrefix}/chat`}
              className="block text-center px-3 py-2 text-xs font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
            >
              Chat with AI
            </Link>
          </div>
        </nav>
      </aside>
    </>
  )
}
