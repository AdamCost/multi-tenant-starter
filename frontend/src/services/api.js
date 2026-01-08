import axios from 'axios'

// API base URL - uses environment variable or defaults to local proxy
const API_BASE = import.meta.env.VITE_API_BASE || ''

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  // Enable cookies for httpOnly token authentication
  withCredentials: true,
})

// Request interceptor to add auth token and organization header
api.interceptors.request.use(
  (config) => {
    // Auth token from localStorage (fallback for cross-origin when cookies don't work)
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }

    // Organization ID header
    const org = localStorage.getItem('team') || localStorage.getItem('organization')
    if (org) {
      try {
        const orgData = JSON.parse(org)
        config.headers['X-Organization-ID'] = orgData.id
      } catch {
        // Invalid JSON, ignore
      }
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear local state on unauthorized
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('team')
      localStorage.removeItem('organization')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

// Organization API
export const organizationApi = {
  list: () => api.get('/api/organizations'),
  getMembers: (orgId) => api.get(`/api/organizations/${orgId}/members`),
  addMember: (orgId, data) => api.post(`/api/organizations/${orgId}/members`, data),
  updateMember: (orgId, userId, data) =>
    api.patch(`/api/organizations/${orgId}/members/${userId}`, data),
  removeMember: (orgId, userId) =>
    api.delete(`/api/organizations/${orgId}/members/${userId}`),

  // Invites
  getInvites: (orgId) => api.get(`/api/organizations/${orgId}/invites`),
  inviteMember: (orgId, email, role) =>
    api.post(`/api/organizations/${orgId}/invites`, { email, role }),
  cancelInvite: (orgId, inviteId) =>
    api.delete(`/api/organizations/${orgId}/invites/${inviteId}`),
}

// Invite API (for accepting invites)
export const inviteApi = {
  getInfo: (token) => api.get(`/api/invites/${token}`),
  accept: (token) => api.post(`/api/invites/${token}/accept`),
}

export default api
