/**
 * OrganizationSection
 *
 * Organization settings including team members management.
 */
import { useState, useEffect } from 'react'
import { useAuth } from '../../../context/AuthContext'
import { organizationApi } from '../../../services/api'
import {
  UserPlusIcon,
  TrashIcon,
  XMarkIcon,
  EnvelopeIcon,
  ClockIcon,
  BuildingOfficeIcon,
} from '@heroicons/react/24/outline'
import { formatDistanceToNow } from 'date-fns'

export default function OrganizationSection() {
  const { team, fetchTeam, canManageTeam } = useAuth()
  const [members, setMembers] = useState([])
  const [invites, setInvites] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Invite modal state
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('viewer')
  const [inviting, setInviting] = useState(false)

  useEffect(() => {
    loadTeamData()
  }, [team?.id])

  const loadTeamData = async () => {
    if (!team?.id) return

    setLoading(true)
    try {
      const [membersRes, invitesRes] = await Promise.all([
        organizationApi.getMembers(team.id),
        organizationApi.getInvites(team.id).catch(() => ({ data: [] })),
      ])
      setMembers(membersRes.data)
      setInvites(invitesRes.data || [])
    } catch (err) {
      setError('Failed to load team data')
    } finally {
      setLoading(false)
    }
  }

  const handleInvite = async (e) => {
    e.preventDefault()
    setInviting(true)
    try {
      await organizationApi.inviteMember(team.id, inviteEmail, inviteRole)
      setInviteEmail('')
      setShowInviteModal(false)
      loadTeamData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send invite')
    } finally {
      setInviting(false)
    }
  }

  const handleRemoveMember = async (memberId) => {
    if (!confirm('Are you sure you want to remove this member?')) return

    try {
      await organizationApi.removeMember(team.id, memberId)
      loadTeamData()
    } catch (err) {
      setError('Failed to remove member')
    }
  }

  const handleCancelInvite = async (inviteId) => {
    try {
      await organizationApi.cancelInvite(team.id, inviteId)
      loadTeamData()
    } catch (err) {
      setError('Failed to cancel invite')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Organization</h2>
          <p className="text-sm text-gray-500 mt-1">
            Manage your team members and settings
          </p>
        </div>
        {canManageTeam && (
          <button
            onClick={() => setShowInviteModal(true)}
            className="inline-flex items-center px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700"
          >
            <UserPlusIcon className="w-5 h-5 mr-2" />
            Invite Member
          </button>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Organization Info */}
      <div className="bg-gray-50 rounded-lg p-4 flex items-center gap-4">
        <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
          <BuildingOfficeIcon className="w-6 h-6 text-primary-600" />
        </div>
        <div>
          <p className="font-medium text-gray-900">{team?.name}</p>
          <p className="text-sm text-gray-500">
            {members.length} member{members.length !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* Team Members */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-3">Team Members</h3>
        <div className="space-y-2">
          {members.map((member) => (
            <div
              key={member.id}
              className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-gray-600">
                    {member.user?.name?.[0] || member.user?.email?.[0]?.toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="font-medium text-gray-900">
                    {member.user?.name || member.user?.email}
                  </p>
                  <p className="text-sm text-gray-500">{member.user?.email}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  member.role === 'admin'
                    ? 'bg-purple-100 text-purple-700'
                    : member.role === 'editor'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-700'
                }`}>
                  {member.role}
                </span>
                {canManageTeam && member.role !== 'admin' && (
                  <button
                    onClick={() => handleRemoveMember(member.user_id)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Pending Invites */}
      {invites.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">Pending Invites</h3>
          <div className="space-y-2">
            {invites.map((invite) => (
              <div
                key={invite.id}
                className="flex items-center justify-between p-4 bg-yellow-50 border border-yellow-200 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center">
                    <EnvelopeIcon className="w-5 h-5 text-yellow-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{invite.email}</p>
                    <p className="text-sm text-gray-500 flex items-center gap-1">
                      <ClockIcon className="w-4 h-4" />
                      Sent {formatDistanceToNow(new Date(invite.created_at), { addSuffix: true })}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-700">
                    {invite.role}
                  </span>
                  {canManageTeam && (
                    <button
                      onClick={() => handleCancelInvite(invite.id)}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      <XMarkIcon className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center p-4">
            <div
              className="fixed inset-0 bg-black/50"
              onClick={() => setShowInviteModal(false)}
            />
            <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900">
                  Invite Team Member
                </h3>
                <button
                  onClick={() => setShowInviteModal(false)}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded-lg"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleInvite} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    required
                    placeholder="colleague@company.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Role
                  </label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="viewer">Viewer - Can view only</option>
                    <option value="editor">Editor - Can view and edit</option>
                  </select>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowInviteModal(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={inviting}
                    className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg disabled:opacity-50"
                  >
                    {inviting ? 'Sending...' : 'Send Invite'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
