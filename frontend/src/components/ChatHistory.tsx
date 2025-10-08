import React, { useState, useEffect } from 'react'
import { MessageCircle, Plus, Trash2, Clock, Search, Loader2, AlertCircle } from 'lucide-react'
import { getChatSessions, createChatSession, deleteChatSession, ChatSession } from '../lib/api'

interface ChatHistoryProps {
  currentSessionId?: string
  onSessionSelect: (sessionId: string) => void
  onNewSession: () => void
  className?: string
}

const ChatHistory: React.FC<ChatHistoryProps> = ({ 
  currentSessionId, 
  onSessionSelect, 
  onNewSession,
  className = '' 
}) => {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [creatingSession, setCreatingSession] = useState(false)
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null)

  const loadSessions = async () => {
    try {
      setLoading(true)
      setError(null)
      const chatSessions = await getChatSessions()
      setSessions(chatSessions)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load chat sessions')
      console.error('Failed to load chat sessions:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSessions()
  }, [])

  const handleNewSession = async () => {
    try {
      setCreatingSession(true)
      const newSession = await createChatSession()
      setSessions(prev => [newSession, ...prev])
      onSessionSelect(newSession.session_id)
      onNewSession()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create new session')
      console.error('Failed to create new session:', err)
    } finally {
      setCreatingSession(false)
    }
  }

  const handleDeleteSession = async (sessionId: string, sessionName: string) => {
    if (!window.confirm(`Are you sure you want to delete "${sessionName}"? This action cannot be undone.`)) {
      return
    }

    try {
      setDeletingSessionId(sessionId)
      await deleteChatSession(sessionId)
      setSessions(prev => prev.filter(s => s.session_id !== sessionId))
      
      // If we deleted the current session, create a new one
      if (currentSessionId === sessionId) {
        onNewSession()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete session')
      console.error('Failed to delete session:', err)
    } finally {
      setDeletingSessionId(null)
    }
  }

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

      if (diffDays === 0) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      } else if (diffDays === 1) {
        return 'Yesterday'
      } else if (diffDays < 7) {
        return `${diffDays} days ago`
      } else {
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
      }
    } catch {
      return dateStr
    }
  }

  const filteredSessions = sessions.filter(session =>
    session.session_name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <Loader2 className="w-6 h-6 animate-spin text-blue-600 mr-2" />
        <span className="text-gray-600">Loading chat history...</span>
      </div>
    )
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg overflow-hidden ${className}`}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <MessageCircle className="w-5 h-5 mr-2 text-blue-600" />
            Chat History
          </h3>
          <button
            onClick={handleNewSession}
            disabled={creatingSession}
            className="flex items-center px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            {creatingSession ? (
              <Loader2 className="w-4 h-4 animate-spin mr-1" />
            ) : (
              <Plus className="w-4 h-4 mr-1" />
            )}
            New Chat
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border-b border-red-200">
          <div className="flex items-center text-red-800">
            <AlertCircle className="w-4 h-4 mr-2" />
            <span className="text-sm">{error}</span>
          </div>
          <button 
            onClick={loadSessions}
            className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Sessions List */}
      <div className="max-h-96 overflow-y-auto">
        {filteredSessions.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            {searchTerm ? (
              <>
                <Search className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p>No conversations found matching "{searchTerm}"</p>
              </>
            ) : (
              <>
                <MessageCircle className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p>No chat history yet</p>
                <p className="text-sm mt-1">Start a conversation to see it here</p>
              </>
            )}
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredSessions.map((session) => (
              <div
                key={session.session_id}
                className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                  currentSessionId === session.session_id ? 'bg-blue-50 border-r-2 border-blue-500' : ''
                }`}
                onClick={() => onSessionSelect(session.session_id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium text-gray-900 truncate">
                      {session.session_name}
                    </h4>
                    <div className="flex items-center mt-1 text-xs text-gray-500">
                      <Clock className="w-3 h-3 mr-1" />
                      {formatDate(session.updated_at)}
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteSession(session.session_id, session.session_name)
                    }}
                    disabled={deletingSessionId === session.session_id}
                    className="ml-2 p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                    title="Delete conversation"
                  >
                    {deletingSessionId === session.session_id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatHistory
