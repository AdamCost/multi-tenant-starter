import { useState, useEffect } from 'react'
import { LockClosedIcon } from '@heroicons/react/24/outline'

const GATE_PASSWORD = 'Discovery123456789'
const STORAGE_KEY = 'starter_gate_access'

function PasswordGate({ children }) {
  const [hasAccess, setHasAccess] = useState(false)
  const [password, setPassword] = useState('')
  const [error, setError] = useState(false)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    // Check if already authenticated
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === GATE_PASSWORD) {
      setHasAccess(true)
    }
    setChecking(false)
  }, [])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (password === GATE_PASSWORD) {
      localStorage.setItem(STORAGE_KEY, password)
      setHasAccess(true)
      setError(false)
    } else {
      setError(true)
      setPassword('')
    }
  }

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (hasAccess) {
    return children
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-sm w-full bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <LockClosedIcon className="w-8 h-8 text-primary-600" />
          </div>
          <h1 className="text-xl font-semibold text-gray-900">Access Required</h1>
          <p className="text-gray-500 mt-2 text-sm">
            This area is currently restricted. Enter the access code to continue.
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter access code"
              autoFocus
              className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                error ? 'border-red-300 bg-red-50' : 'border-gray-300'
              }`}
            />
            {error && (
              <p className="text-red-600 text-sm mt-2">Incorrect access code</p>
            )}
          </div>

          <button
            type="submit"
            className="w-full px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium"
          >
            Continue
          </button>
        </form>
      </div>
    </div>
  )
}

export default PasswordGate
