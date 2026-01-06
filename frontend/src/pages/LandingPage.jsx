import { Link } from 'react-router-dom'
import {
  ShieldCheckIcon,
  UserGroupIcon,
  KeyIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline'

const features = [
  {
    name: 'Authentication',
    description: 'Secure JWT-based authentication with password reset and SSO-ready structure.',
    icon: ShieldCheckIcon,
  },
  {
    name: 'Multi-Tenant Organizations',
    description: 'Built-in organization management with team members and role-based access control.',
    icon: UserGroupIcon,
  },
  {
    name: 'API Key Management',
    description: 'Generate and manage API keys with scopes, rate limiting, and usage tracking.',
    icon: KeyIcon,
  },
  {
    name: 'Settings & Configuration',
    description: 'Pre-built settings pages for profile management and team administration.',
    icon: Cog6ToothIcon,
  },
]

function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">S</span>
              </div>
              <span className="ml-3 text-xl font-semibold text-gray-900">Starter</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                to="/login"
                className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium"
              >
                Sign In
              </Link>
              <Link
                to="/login"
                className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 sm:py-32">
          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 tracking-tight">
              Your SaaS
              <span className="text-primary-600"> Starter Kit</span>
            </h1>
            <p className="mt-6 text-lg sm:text-xl text-gray-600 max-w-3xl mx-auto">
              A production-ready multi-tenant SaaS boilerplate with authentication,
              organization management, and all the infrastructure you need to ship faster.
            </p>
            <div className="mt-10 flex justify-center gap-4">
              <Link
                to="/login"
                className="bg-primary-600 text-white px-8 py-3 rounded-lg text-base font-medium hover:bg-primary-700 transition-colors shadow-lg shadow-primary-500/25"
              >
                Get Started Free
              </Link>
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="bg-gray-100 text-gray-700 px-8 py-3 rounded-lg text-base font-medium hover:bg-gray-200 transition-colors"
              >
                View on GitHub
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-gray-50 py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">
              Everything you need to launch
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Built-in features to get your SaaS off the ground quickly.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature) => (
              <div
                key={feature.name}
                className="bg-white rounded-xl p-6 shadow-sm border border-gray-100"
              >
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {feature.name}
                </h3>
                <p className="text-gray-600 text-sm">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tech Stack Section */}
      <div className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900">Modern Tech Stack</h2>
            <p className="mt-4 text-lg text-gray-600">
              Built with industry-standard technologies you already know.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-8 text-gray-600">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">FastAPI</div>
              <div className="text-sm">Backend</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">React</div>
              <div className="text-sm">Frontend</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">PostgreSQL</div>
              <div className="text-sm">Database</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">Tailwind CSS</div>
              <div className="text-sm">Styling</div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-primary-600 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to build your SaaS?
          </h2>
          <p className="text-primary-100 mb-8 text-lg">
            Get started in minutes with our production-ready boilerplate.
          </p>
          <Link
            to="/login"
            className="inline-block bg-white text-primary-600 px-8 py-3 rounded-lg text-base font-medium hover:bg-primary-50 transition-colors"
          >
            Start Building Now
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center mb-4 md:mb-0">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">S</span>
              </div>
              <span className="ml-3 text-white font-semibold">Multi-Tenant Starter</span>
            </div>
            <div className="flex space-x-6">
              <Link to="/terms" className="hover:text-white transition-colors">
                Terms
              </Link>
              <Link to="/privacy" className="hover:text-white transition-colors">
                Privacy
              </Link>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-gray-800 text-center text-sm">
            &copy; {new Date().getFullYear()} Multi-Tenant Starter. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage
