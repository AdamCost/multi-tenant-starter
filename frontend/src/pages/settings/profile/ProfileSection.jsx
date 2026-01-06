/**
 * ProfileSection
 *
 * User profile settings including name display, email, and password change.
 */
import { useState } from 'react'
import { useAuth } from '../../../context/AuthContext'
import {
  UserCircleIcon,
  EnvelopeIcon,
  KeyIcon,
  PencilIcon,
} from '@heroicons/react/24/outline'
import ChangePasswordModal from './ChangePasswordModal'

export default function ProfileSection() {
  const { user } = useAuth()
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [name, setName] = useState(user?.name || '')
  const [saving, setSaving] = useState(false)

  const handleSaveName = async () => {
    setSaving(true)
    await new Promise(resolve => setTimeout(resolve, 500))
    setSaving(false)
    setIsEditing(false)
  }

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Profile</h2>
        <p className="text-sm text-gray-500 mt-1">
          Manage your personal information
        </p>
      </div>

      {/* Avatar Section */}
      <div className="flex items-center gap-4 pb-6 border-b border-gray-200">
        <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center">
          {user?.name ? (
            <span className="text-2xl font-semibold text-primary-700">
              {user.name.charAt(0).toUpperCase()}
            </span>
          ) : (
            <UserCircleIcon className="w-12 h-12 text-primary-400" />
          )}
        </div>
        <div>
          <p className="text-sm text-gray-500">Profile picture</p>
          <p className="text-xs text-gray-400 mt-1">
            Avatar is generated from your name
          </p>
        </div>
      </div>

      {/* Name Field */}
      <div className="flex items-center justify-between py-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <UserCircleIcon className="w-5 h-5 text-gray-400" />
          <div>
            <p className="text-sm font-medium text-gray-700">Name</p>
            {isEditing ? (
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-1 text-sm border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                autoFocus
              />
            ) : (
              <p className="text-sm text-gray-900">{user?.name || 'Not set'}</p>
            )}
          </div>
        </div>
        {isEditing ? (
          <div className="flex gap-2">
            <button
              onClick={() => {
                setIsEditing(false)
                setName(user?.name || '')
              }}
              className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveName}
              disabled={saving}
              className="px-3 py-1.5 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        ) : (
          <button
            onClick={() => setIsEditing(true)}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            <PencilIcon className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Email Field */}
      <div className="flex items-center justify-between py-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <EnvelopeIcon className="w-5 h-5 text-gray-400" />
          <div>
            <p className="text-sm font-medium text-gray-700">Email</p>
            <p className="text-sm text-gray-900">{user?.email}</p>
          </div>
        </div>
        <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
          Cannot be changed
        </span>
      </div>

      {/* Password Field */}
      <div className="flex items-center justify-between py-4">
        <div className="flex items-center gap-3">
          <KeyIcon className="w-5 h-5 text-gray-400" />
          <div>
            <p className="text-sm font-medium text-gray-700">Password</p>
            <p className="text-sm text-gray-500">••••••••</p>
          </div>
        </div>
        <button
          onClick={() => setShowPasswordModal(true)}
          className="px-4 py-2 text-sm font-medium text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded-lg transition-colors"
        >
          Change password
        </button>
      </div>

      {/* Password Change Modal */}
      <ChangePasswordModal
        isOpen={showPasswordModal}
        onClose={() => setShowPasswordModal(false)}
      />
    </div>
  )
}
