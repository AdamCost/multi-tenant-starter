import { useAuth } from '../context/AuthContext'
import {
  RocketLaunchIcon,
  UserGroupIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline'
import { Link } from 'react-router-dom'

function DashboardPage() {
  const { user, team } = useAuth()

  const quickLinks = [
    {
      name: 'Settings',
      description: 'Manage your profile and preferences',
      href: '/app/settings/profile',
      icon: Cog6ToothIcon,
    },
    {
      name: 'Team',
      description: 'Invite team members and manage roles',
      href: '/app/settings/organization',
      icon: UserGroupIcon,
    },
  ]

  return (
    <div className="max-w-4xl mx-auto">
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.name || user?.email?.split('@')[0]}!
        </h1>
        <p className="text-gray-600 mt-1">
          {team ? `You're working in ${team.name}` : 'Get started with your dashboard'}
        </p>
      </div>

      {/* Getting Started Card */}
      <div className="bg-gradient-to-r from-primary-500 to-purple-600 rounded-2xl p-8 text-white mb-8">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-white/20 rounded-xl">
            <RocketLaunchIcon className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-xl font-semibold mb-2">Start Building</h2>
            <p className="text-primary-100 mb-4">
              This is your dashboard. Customize it to fit your SaaS needs.
              Add your own components, charts, and data visualizations here.
            </p>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-4 py-2 bg-white text-primary-600 rounded-lg text-sm font-medium hover:bg-primary-50 transition-colors"
            >
              View Documentation
            </a>
          </div>
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {quickLinks.map((link) => (
          <Link
            key={link.name}
            to={link.href}
            className="bg-white rounded-xl p-6 border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all group"
          >
            <div className="flex items-start space-x-4">
              <div className="p-2 bg-primary-100 rounded-lg group-hover:bg-primary-200 transition-colors">
                <link.icon className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
                  {link.name}
                </h3>
                <p className="text-gray-600 text-sm mt-1">{link.description}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Placeholder Content */}
      <div className="mt-8 bg-gray-50 rounded-xl border-2 border-dashed border-gray-300 p-12 text-center">
        <p className="text-gray-500">
          Add your custom dashboard widgets here.
        </p>
        <p className="text-gray-400 text-sm mt-2">
          Charts, metrics, recent activity, etc.
        </p>
      </div>
    </div>
  )
}

export default DashboardPage
