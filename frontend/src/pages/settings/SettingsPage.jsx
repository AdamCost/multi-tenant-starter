/**
 * SettingsPage
 *
 * Unified settings page with sidebar navigation.
 */
import { Outlet, NavLink, useLocation, Navigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import {
  UserCircleIcon,
  BuildingOfficeIcon,
} from '@heroicons/react/24/outline'

const SETTINGS_SECTIONS = [
  {
    id: 'profile',
    path: '/app/settings/profile',
    icon: UserCircleIcon,
    label: 'Profile',
    adminOnly: false,
  },
  {
    id: 'organization',
    path: '/app/settings/organization',
    icon: BuildingOfficeIcon,
    label: 'Organization',
    adminOnly: true,
  },
]

function SettingsPage() {
  const { canManageTeam } = useAuth()
  const location = useLocation()

  // Filter sections based on admin status
  const visibleSections = SETTINGS_SECTIONS.filter(
    section => !section.adminOnly || canManageTeam
  )

  // Redirect to profile if on base settings path
  if (location.pathname === '/app/settings') {
    return <Navigate to="/app/settings/profile" replace />
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">
          Manage your account and organization settings
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Sidebar Navigation */}
        <nav className="lg:w-64 flex-shrink-0">
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            {visibleSections.map((section) => (
              <NavLink
                key={section.id}
                to={section.path}
                className={({ isActive }) =>
                  `flex items-center px-4 py-3 text-sm font-medium border-b border-gray-100 last:border-b-0 transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700 border-l-2 border-l-primary-600'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`
                }
              >
                <section.icon className="w-5 h-5 mr-3" />
                {section.label}
              </NavLink>
            ))}
          </div>
        </nav>

        {/* Main Content */}
        <div className="flex-1 min-w-0">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
