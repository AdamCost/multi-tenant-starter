import { Link } from 'react-router-dom'

function TermsPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">S</span>
                </div>
                <span className="ml-3 text-xl font-semibold text-gray-900">Starter</span>
              </Link>
            </div>
            <div className="flex items-center">
              <Link
                to="/login"
                className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium"
              >
                Sign In
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Terms of Service</h1>

        <div className="prose prose-gray max-w-none">
          <p className="text-gray-600 mb-6">
            Last updated: {new Date().toLocaleDateString()}
          </p>

          <h2 className="text-xl font-semibold text-gray-900 mt-8 mb-4">1. Acceptance of Terms</h2>
          <p className="text-gray-600 mb-4">
            By accessing and using this service, you accept and agree to be bound by the terms
            and provision of this agreement.
          </p>

          <h2 className="text-xl font-semibold text-gray-900 mt-8 mb-4">2. Use License</h2>
          <p className="text-gray-600 mb-4">
            Permission is granted to temporarily use this service for personal, non-commercial
            transitory viewing only.
          </p>

          <h2 className="text-xl font-semibold text-gray-900 mt-8 mb-4">3. Disclaimer</h2>
          <p className="text-gray-600 mb-4">
            The materials on this service are provided on an 'as is' basis. We make no warranties,
            expressed or implied, and hereby disclaim and negate all other warranties including,
            without limitation, implied warranties or conditions of merchantability, fitness for
            a particular purpose, or non-infringement of intellectual property.
          </p>

          <h2 className="text-xl font-semibold text-gray-900 mt-8 mb-4">4. Limitations</h2>
          <p className="text-gray-600 mb-4">
            In no event shall we or our suppliers be liable for any damages arising out of the
            use or inability to use the materials on this service.
          </p>

          <h2 className="text-xl font-semibold text-gray-900 mt-8 mb-4">5. Governing Law</h2>
          <p className="text-gray-600 mb-4">
            These terms and conditions are governed by and construed in accordance with
            applicable laws and you irrevocably submit to the exclusive jurisdiction of
            the courts in that location.
          </p>
        </div>

        <div className="mt-12 pt-8 border-t border-gray-200">
          <Link to="/" className="text-primary-600 hover:text-primary-700">
            &larr; Back to Home
          </Link>
        </div>
      </div>
    </div>
  )
}

export default TermsPage
