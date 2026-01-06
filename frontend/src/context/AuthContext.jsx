import { createContext, useContext, useState, useEffect } from 'react'
import api, { organizationApi } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [team, setTeam] = useState(null)
  const [loading, setLoading] = useState(true)

  // Fetch user's team (they only have one)
  const fetchTeam = async () => {
    try {
      const response = await organizationApi.list()
      const teams = response.data
      if (teams.length > 0) {
        return teams[0]
      }
      return null
    } catch (error) {
      console.error('Failed to fetch team:', error)
      return null
    }
  }

  // Select/set the team
  const selectTeam = (teamData) => {
    if (teamData) {
      localStorage.setItem('team', JSON.stringify(teamData))
      api.defaults.headers.common['X-Organization-ID'] = teamData.id
      setTeam(teamData)
    }
  }

  useEffect(() => {
    const initAuth = async () => {
      // Check for saved user info (token is now in httpOnly cookie)
      const savedUser = localStorage.getItem('user')
      const savedTeam = localStorage.getItem('team') || localStorage.getItem('organization')

      if (savedUser) {
        setUser(JSON.parse(savedUser))

        // Fetch team to verify session is still valid
        try {
          const teamData = await fetchTeam()

          if (teamData) {
            // Session is valid, set up team
            if (savedTeam) {
              const savedTeamData = JSON.parse(savedTeam)
              // Verify team is still valid
              if (teamData.id === savedTeamData.id) {
                selectTeam(teamData)
              } else {
                selectTeam(teamData)
              }
            } else {
              selectTeam(teamData)
            }
          } else {
            // No team returned - might be logged out
            // Clear local state but let API interceptor handle 401
          }
        } catch (error) {
          // If fetch fails with 401, interceptor will clear state
          console.error('Session validation failed:', error)
          if (error.response?.status === 401) {
            localStorage.removeItem('user')
            localStorage.removeItem('team')
            setUser(null)
          }
        }

        // Clean up old localStorage key
        localStorage.removeItem('organization')
      }

      setLoading(false)
    }

    initAuth()
  }, [])

  const login = async (email, password) => {
    const response = await api.post('/api/auth/login', { email, password })
    const { access_token, user: userData } = response.data

    // Store token and user info in localStorage (for cross-origin support)
    if (access_token) {
      localStorage.setItem('token', access_token)
    }
    localStorage.setItem('user', JSON.stringify(userData))

    setUser(userData)

    // Fetch and select team
    const teamData = await fetchTeam()
    if (teamData) {
      selectTeam(teamData)
    }

    return userData
  }

  const register = async (email, password, name) => {
    const response = await api.post('/api/auth/register', { email, password, name })
    const { access_token, user: userData } = response.data

    // Store token and user info in localStorage (for cross-origin support)
    if (access_token) {
      localStorage.setItem('token', access_token)
    }
    localStorage.setItem('user', JSON.stringify(userData))

    setUser(userData)

    // Fetch and select team
    const teamData = await fetchTeam()
    if (teamData) {
      selectTeam(teamData)
    }

    return userData
  }

  const logout = async () => {
    try {
      // Call logout endpoint to clear httpOnly cookie
      await api.post('/api/auth/logout')
    } catch (error) {
      console.error('Logout error:', error)
    }

    // Clear local state
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('team')
    localStorage.removeItem('organization')
    delete api.defaults.headers.common['X-Organization-ID']
    setUser(null)
    setTeam(null)
  }

  // Permission helpers
  const canManageTeam = team?.role === 'admin'
  const canEditCampaigns = ['admin', 'editor'].includes(team?.role)
  const canView = ['admin', 'editor', 'viewer'].includes(team?.role)

  const value = {
    user,
    team,
    // Legacy compatibility
    organization: team,
    organizations: team ? [team] : [],
    loading,
    login,
    register,
    logout,
    selectOrganization: selectTeam,
    fetchOrganizations: fetchTeam,
    fetchTeam,
    isAuthenticated: !!user,
    // Permission helpers
    canManageTeam,
    canEditCampaigns,
    canView,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
