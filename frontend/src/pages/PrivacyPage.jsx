import { Link } from 'react-router-dom'

function PrivacyPage() {
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
                to="/"
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
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Privacy Policy</h1>

        <div className="prose prose-gray max-w-none">
          <p className="text-gray-600 mb-6">
            Last updated: {new Date().toLocaleDateString()}
          </p>

          <h2 className="text-xl font-semibold text-gray-900 mt-8 mb-4">1. Information We Collect</h2>
          <p className="text-gray-600 mb-4">
            We collect information you provide directly to us, such as when you create an account,
            use our services, or contact us for support.
          </p>

          <h2 className="text-xl font-semibold text-gray-900 mt-8 mb-4">2. How We Use Your Information</h2>
          <p className="text-gray-600 mb-4">
            We use the information we collect to provide, maintain, and improve our services,
            process transactions, send communications, and comply with legal obligations.
          </p>

          <h2 className="text-xl font-semibold text-gray-900 mt-8 mb-4">3. Information Sharing</h2>
          <p className="text-gray-600 mb-4">
            We do not share your personal information with third parties except as described
            in this policy, with your consent, or as required by law.
          </p>

          <h2 className="text-xl font-semibold text-gray-900 mt-8 mb-4">4. Data Security</h2>
          <p className="text-gray-600 mb-4">
            We take reasonable measures to help protect your personal information from loss,
            theft, misuse, unauthorized access, disclosure, alteration, and destruction.
          </p>

          <h2 className="text-xl font-semibold text-gray-900 mt-8 mb-4">5. Your Rights</h2>
          <p className="text-gray-600 mb-4">
            You may access, update, or delete your account information at any time through
            your account settings. You may also contact us to request access to, correction of,
            or deletion of your personal information.
          </p>

          <h2 className="text-xl font-semibold text-gray-900 mt-8 mb-4">6. Contact Us</h2>
          <p className="text-gray-600 mb-4">
            If you have any questions about this Privacy Policy, please contact us.
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

export default PrivacyPage
