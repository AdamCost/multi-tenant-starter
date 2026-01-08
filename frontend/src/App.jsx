import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import ErrorBoundary, { RouteErrorFallback } from './components/ErrorBoundary'

// Page loader component for Suspense fallback
const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
  </div>
)

// Lazy load pages for code splitting
// Public pages
const LandingPage = lazy(() => import('./pages/LandingPage'))
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'))
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage'))
const AcceptInvitePage = lazy(() => import('./pages/AcceptInvitePage'))
const TermsPage = lazy(() => import('./pages/TermsPage'))
const PrivacyPage = lazy(() => import('./pages/PrivacyPage'))

// Protected pages
const DashboardPage = lazy(() => import('./pages/DashboardPage'))

// Settings pages
const SettingsPage = lazy(() => import('./pages/settings/SettingsPage'))
const ProfileSection = lazy(() => import('./pages/settings/profile/ProfileSection'))
const OrganizationSection = lazy(() => import('./pages/settings/organization/OrganizationSection'))

// Layout components
import Layout from './components/Layout'
import PasswordGate from './components/PasswordGate'

// Wrapper component for lazy loaded pages with Suspense
const LazyPage = ({ children }) => (
  <ErrorBoundary fallback={<RouteErrorFallback />}>
    <Suspense fallback={<PageLoader />}>
      {children}
    </Suspense>
  </ErrorBoundary>
)

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/" replace />
  }

  return children
}

function App() {
  return (
    <ErrorBoundary>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<LazyPage><LandingPage /></LazyPage>} />
        <Route path="/forgot-password" element={<LazyPage><ForgotPasswordPage /></LazyPage>} />
        <Route path="/reset-password" element={<LazyPage><ResetPasswordPage /></LazyPage>} />
        <Route path="/invite/:token" element={<LazyPage><AcceptInvitePage /></LazyPage>} />
        <Route path="/terms" element={<LazyPage><TermsPage /></LazyPage>} />
        <Route path="/privacy" element={<LazyPage><PrivacyPage /></LazyPage>} />

        {/* Protected routes - nested under /app */}
        <Route
          path="/app"
          element={
            <ProtectedRoute>
              <PasswordGate>
                <Layout />
              </PasswordGate>
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/app/dashboard" replace />} />
          <Route path="dashboard" element={<LazyPage><DashboardPage /></LazyPage>} />

          {/* Settings */}
          <Route path="settings" element={<LazyPage><SettingsPage /></LazyPage>}>
            <Route index element={<Navigate to="/app/settings/profile" replace />} />
            <Route path="profile" element={<LazyPage><ProfileSection /></LazyPage>} />
            <Route path="organization" element={<LazyPage><OrganizationSection /></LazyPage>} />
          </Route>
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ErrorBoundary>
  )
}

export default App
