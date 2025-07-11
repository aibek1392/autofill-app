import React from 'react'
import { AlertCircle, ExternalLink } from 'lucide-react'

interface AuthStatusProps {
  className?: string
}

const AuthStatus: React.FC<AuthStatusProps> = ({ className = '' }) => {
  const hasSupabaseCredentials = process.env.REACT_APP_SUPABASE_URL && 
                                process.env.REACT_APP_SUPABASE_ANON_KEY &&
                                process.env.REACT_APP_SUPABASE_URL !== 'https://placeholder.supabase.co'

  if (hasSupabaseCredentials) {
    return null // Don't show anything if credentials are properly configured
  }

  return (
    <div className={`bg-yellow-50 border border-yellow-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
        <div className="flex-1">
          <h3 className="text-sm font-medium text-yellow-800 mb-2">
            Authentication Setup Required
          </h3>
          <div className="text-sm text-yellow-700 space-y-2">
            <p>
              To use document upload and other features, you need to configure Supabase authentication.
            </p>
            <div className="space-y-1">
              <p className="font-medium">Setup Steps:</p>
              <ol className="list-decimal list-inside space-y-1 ml-2">
                <li>Create a Supabase project at <a href="https://supabase.com" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 underline inline-flex items-center">supabase.com <ExternalLink className="w-3 h-3 ml-1" /></a></li>
                <li>Get your project URL and anon key from the project settings</li>
                <li>Create a <code className="bg-yellow-100 px-1 py-0.5 rounded">.env</code> file in the frontend directory</li>
                <li>Add the following environment variables:</li>
              </ol>
              <pre className="bg-yellow-100 p-2 rounded text-xs overflow-x-auto mt-2">
{`REACT_APP_SUPABASE_URL=https://your-project-id.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-supabase-anon-key
REACT_APP_API_URL=https://autofill-backend-a64u.onrender.com`}
              </pre>
            </div>
            <p className="text-xs mt-3">
              After adding these variables, restart the development server.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AuthStatus 