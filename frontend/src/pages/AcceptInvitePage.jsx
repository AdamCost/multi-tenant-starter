import { useState, useEffect } from 'react'
import { useNavigate, Link, useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  UserIcon,
  LockClosedIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowRightIcon,
  BuildingOfficeIcon,
} from '@heroicons/react/24/outline'
import api from '../services/api'

function AcceptInvitePage() {
  const { token } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()

  // States
  const [loading, setLoading] = useState(true)
  const [inviteInfo, setInviteInfo] = useState(null)
  const [error, setError] = useState('')
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)

  // Form fields
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  // Fetch invite info on mount
  useEffect(() => {
    const fetchInviteInfo = async () => {
      try {
        const response = await api.get(`/api/invites/${token}`)
        setInviteInfo(response.data)
      } catch (err) {
        const detail = err.response?.data?.detail || 'Invalid or expired invite'
        setError(detail)
      } finally {
        setLoading(false)
      }
    }

    fetchInviteInfo()
  }, [token])

  // If user is already logged in and invite email matches, auto-accept
  useEffect(() => {
    const autoAccept = async () => {
      if (user && inviteInfo && user.email.toLowerCase() === inviteInfo.email.toLowerCase()) {
        try {
          setSubmitting(true)
          await api.post(`/api/invites/${token}/accept`)
          window.location.href = '/app/dashboard'
        } catch (err) {
          if (err.response?.data?.detail?.includes('already a member')) {
            window.location.href = '/app/dashboard'
          } else {
            setFormError(err.response?.data?.detail || 'Failed to accept invite')
            setSubmitting(false)
          }
        }
      }
    }

    if (user && inviteInfo) {
      autoAccept()
    }
  }, [user, inviteInfo, token])

  const validatePassword = () => {
    if (password.length < 12) {
      return 'Password must be at least 12 characters'
    }
    if (!/[A-Z]/.test(password)) {
      return 'Password must contain at least one uppercase letter'
    }
    if (!/[a-z]/.test(password)) {
      return 'Password must contain at least one lowercase letter'
    }
    if (!/[0-9]/.test(password)) {
      return 'Password must contain at least one number'
    }
    if (password !== confirmPassword) {
      return 'Passwords do not match'
    }
    return null
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError('')

    const validationError = validatePassword()
    if (validationError) {
      setFormError(validationError)
      return
    }

    setSubmitting(true)
    try {
      const response = await api.post(`/api/invites/${token}/accept-with-signup`, {
        name,
        password,
      })

      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token)

        try {
          const userResponse = await api.get('/api/auth/me', {
            headers: { Authorization: `Bearer ${response.data.access_token}` }
          })
          localStorage.setItem('user', JSON.stringify(userResponse.data))
        } catch (userErr) {
          console.error('Failed to fetch user data:', userErr)
        }

        window.location.href = '/app/dashboard'
        return
      }

      setSuccess(true)
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create account')
      setSubmitting(false)
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  // Error state (invalid/expired invite)
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-14 sm:h-16">
              <Link to="/" className="flex items-center space-x-2 sm:space-x-3">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">S</span>
                </div>
                <span className="text-xl font-semibold text-gray-900">Starter</span>
              </Link>
            </div>
          </div>
        </header>

        <main className="flex-1 flex items-center justify-center px-4 py-6 sm:py-12">
          <div className="w-full max-w-md">
            <div className="bg-white rounded-2xl shadow-lg p-5 sm:p-8 text-center">
              <div className="w-14 h-14 sm:w-16 sm:h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4 sm:mb-6">
                <ExclamationCircleIcon className="w-8 h-8 sm:w-10 sm:h-10 text-red-600" />
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">
                Invalid Invitation
              </h1>
              <p className="text-sm sm:text-base text-gray-600 mb-5 sm:mb-6">{error}</p>
              <Link
                to="/login"
                className="inline-flex items-center justify-center w-full sm:w-auto px-6 py-3 min-h-[44px] bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors"
              >
                Go to Login
              </Link>
            </div>
          </div>
        </main>
      </div>
    )
  }

  // Success state
  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-14 sm:h-16">
              <Link to="/" className="flex items-center space-x-2 sm:space-x-3">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">S</span>
                </div>
                <span className="text-xl font-semibold text-gray-900">Starter</span>
              </Link>
            </div>
          </div>
        </header>

        <main className="flex-1 flex items-center justify-center px-4 py-6 sm:py-12">
          <div className="w-full max-w-md">
            <div className="bg-white rounded-2xl shadow-lg p-5 sm:p-8 text-center">
              <div className="w-14 h-14 sm:w-16 sm:h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4 sm:mb-6">
                <CheckCircleIcon className="w-8 h-8 sm:w-10 sm:h-10 text-green-600" />
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">
                Welcome to the team!
              </h1>
              <p className="text-sm sm:text-base text-gray-600 mb-5 sm:mb-6">
                You've joined {inviteInfo?.organization_name || 'the organization'}. Let's get started.
              </p>
              <Link
                to="/app/dashboard"
                className="inline-flex items-center justify-center w-full sm:w-auto px-6 py-3 min-h-[44px] bg-gradient-to-r from-primary-500 to-purple-600 text-white rounded-xl font-medium hover:from-primary-600 hover:to-purple-700 transition-all"
              >
                Go to Dashboard
                <ArrowRightIcon className="w-5 h-5 ml-2" />
              </Link>
            </div>
          </div>
        </main>
      </div>
    )
  }

  // If user is logged in but email doesn't match
  if (user && inviteInfo && user.email.toLowerCase() !== inviteInfo.email.toLowerCase()) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-14 sm:h-16">
              <Link to="/" className="flex items-center space-x-2 sm:space-x-3">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">S</span>
                </div>
                <span className="text-xl font-semibold text-gray-900">Starter</span>
              </Link>
            </div>
          </div>
        </header>

        <main className="flex-1 flex items-center justify-center px-4 py-6 sm:py-12">
          <div className="w-full max-w-md">
            <div className="bg-white rounded-2xl shadow-lg p-5 sm:p-8 text-center">
              <div className="w-14 h-14 sm:w-16 sm:h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4 sm:mb-6">
                <ExclamationCircleIcon className="w-8 h-8 sm:w-10 sm:h-10 text-yellow-600" />
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">
                Wrong Account
              </h1>
              <p className="text-sm sm:text-base text-gray-600 mb-5 sm:mb-6">
                This invite was sent to {inviteInfo.email}. You're currently logged in as {user.email}. Please log out and try again.
              </p>
              <Link
                to="/login"
                className="inline-flex items-center justify-center w-full sm:w-auto px-6 py-3 min-h-[44px] bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors"
              >
                Switch Account
              </Link>
            </div>
          </div>
        </main>
      </div>
    )
  }

  // Main form (for new users)
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14 sm:h-16">
            <Link to="/" className="flex items-center space-x-2 sm:space-x-3">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">S</span>
              </div>
              <span className="text-xl font-semibold text-gray-900">Starter</span>
            </Link>

            <div className="flex items-center space-x-2 sm:space-x-4">
              <span className="text-sm text-gray-600 hidden sm:inline">
                Already have an account?
              </span>
              <Link
                to={`/login?redirect=/invite/${token}`}
                className="inline-flex items-center justify-center px-3 sm:px-4 py-2 min-h-[44px] bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
              >
                Sign In
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-4 py-6 sm:py-12">
        <div className="w-full max-w-md">
          {/* Heading */}
          <div className="text-center mb-5 sm:mb-8">
            <div className="w-14 h-14 sm:w-16 sm:h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4">
              <BuildingOfficeIcon className="w-7 h-7 sm:w-8 sm:h-8 text-primary-600" />
            </div>
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 mb-2">
              You're invited!
            </h1>
            <p className="text-sm sm:text-base text-gray-600">
              Join {inviteInfo?.organization_name || 'the team'}
            </p>
          </div>

          {/* Card */}
          <div className="bg-white rounded-2xl shadow-lg p-4 sm:p-6 md:p-8">
            {/* Invite Info */}
            <div className="mb-4 sm:mb-6 p-3 sm:p-4 bg-gray-50 rounded-xl">
              <div className="text-xs sm:text-sm text-gray-600 mb-1">
                Invited as
              </div>
              <div className="text-sm sm:text-base font-medium text-gray-900 capitalize">
                {inviteInfo?.role || 'Member'}
              </div>
              <div className="text-xs sm:text-sm text-gray-500 mt-1.5 sm:mt-2 truncate">
                {inviteInfo?.email}
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5">
              {/* Name Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Full Name
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <UserIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="w-full pl-10 pr-4 py-2.5 min-h-[44px] text-base border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                    placeholder="John Doe"
                  />
                </div>
              </div>

              {/* Password Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <LockClosedIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full pl-10 pr-4 py-2.5 min-h-[44px] text-base border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                    placeholder="Create a password"
                  />
                </div>
                <p className="mt-1.5 text-xs text-gray-500">
                  At least 12 characters with uppercase, lowercase, and number
                </p>
              </div>

              {/* Confirm Password Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Confirm Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <LockClosedIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    className="w-full pl-10 pr-4 py-2.5 min-h-[44px] text-base border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                    placeholder="Confirm your password"
                  />
                </div>
              </div>

              {/* Error Message */}
              {formError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
                  {formError}
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={submitting || !name || !password || !confirmPassword}
                className="w-full py-3 min-h-[48px] bg-gradient-to-r from-primary-500 to-purple-600 text-white rounded-xl font-medium hover:from-primary-600 hover:to-purple-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center space-x-2"
              >
                {submitting ? (
                  <span className="flex items-center">
                    <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      />
                    </svg>
                    Creating account...
                  </span>
                ) : (
                  <>
                    <span>Create Account & Join</span>
                    <ArrowRightIcon className="h-5 w-5" />
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Footer Links */}
          <p className="text-center text-xs sm:text-sm text-gray-500 mt-4 sm:mt-6 px-2">
            By continuing, you agree to our{' '}
            <Link to="/terms" className="text-primary-600 hover:text-primary-700">
              Terms of Service
            </Link>{' '}
            and{' '}
            <Link to="/privacy" className="text-primary-600 hover:text-primary-700">
              Privacy Policy
            </Link>
          </p>
        </div>
      </main>
    </div>
  )
}

export default AcceptInvitePage
