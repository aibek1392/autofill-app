import React, { useState, useRef, useEffect, useCallback } from 'react'
import { X, History } from 'lucide-react'
import Chat from './Chat'
import ChatHistory from './ChatHistory'

interface ResizableChatPanelProps {
  isOpen: boolean
  onToggle: () => void
  minWidth?: number
  maxWidth?: number
  defaultWidth?: number
}

const ResizableChatPanel: React.FC<ResizableChatPanelProps> = ({
  isOpen,
  onToggle,
  minWidth = 300,
  maxWidth = 600,
  defaultWidth = 400
}) => {
  const [width, setWidth] = useState(defaultWidth)
  const [isDragging, setIsDragging] = useState(false)
  const [startX, setStartX] = useState(0)
  const [startWidth, setStartWidth] = useState(0)
  const [isMobile, setIsMobile] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(undefined)
  const resizeRef = useRef<HTMLDivElement>(null)

  // Check if we're on mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Handle mouse down on resize handle
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsDragging(true)
    setStartX(e.clientX)
    setStartWidth(width)
  }, [width])

  // Handle mouse move for resizing
  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return

    const deltaX = startX - e.clientX
    const newWidth = Math.max(minWidth, Math.min(maxWidth, startWidth + deltaX))
    setWidth(newWidth)
  }, [isDragging, startX, startWidth, minWidth, maxWidth])

  // Handle mouse up to stop resizing
  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  // Add/remove global mouse event listeners
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
    } else {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [isDragging, handleMouseMove, handleMouseUp])

  // Reset width when panel is closed and reopened
  useEffect(() => {
    if (!isOpen) {
      setWidth(defaultWidth)
    }
  }, [isOpen, defaultWidth])

  return (
    <>
      {/* Toggle Button - Fixed position on the right */}
      <button
        onClick={onToggle}
        className={`
          fixed top-4 right-4 z-50 flex items-center space-x-2 px-3 py-2 rounded-lg shadow-lg transition-all duration-300 ease-in-out
          ${isOpen 
            ? 'bg-gray-800 text-white hover:bg-gray-700' 
            : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 shadow-xl hover:shadow-2xl transform hover:scale-105'
          }
        `}
        title={isOpen ? 'Close AI Assistant' : 'Open AI Assistant'}
      >
        {isOpen ? (
          <X className="w-4 h-4" />
        ) : (
          <>
            <div className="relative">
              <div className="w-4 h-4 bg-white rounded-full flex items-center justify-center">
                <div className="w-2 h-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full"></div>
              </div>
              <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            </div>
            <span className="text-sm font-medium">AI</span>
          </>
        )}
      </button>

      {/* Chat Panel */}
      <div
        className={`
          fixed top-0 right-0 h-full bg-white shadow-2xl border-l border-gray-200
          transition-all duration-300 ease-in-out z-40 flex flex-col
          ${isOpen ? 'translate-x-0' : 'translate-x-full'}
          sm:w-full lg:w-auto
        `}
        style={{ width: isMobile ? '100%' : `${width}px` }}
      >
        {/* Header */}
        <div className="flex-shrink-0 flex items-center justify-between p-3 sm:p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center space-x-2 min-w-0 flex-1">
            {/* AI Assistant Icon - Hidden on mobile to save space */}
            <div className="relative hidden sm:block">
              <div className="w-5 h-5 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
                <div className="w-2.5 h-2.5 bg-white rounded-full"></div>
              </div>
              <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            </div>
            <h3 className="font-medium text-gray-900 truncate text-sm sm:text-base">
              {showHistory ? 'Chat History' : 'AI Assistant'}
            </h3>
          </div>
          <div className="flex items-center space-x-1 sm:space-x-2 flex-shrink-0">
            <button
              onClick={() => setShowHistory(!showHistory)}
              className={`p-2 sm:p-1 rounded-md transition-colors ${
                showHistory ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-200 text-gray-500'
              }`}
              title={showHistory ? 'Show Chat' : 'Show History'}
            >
              <History className="w-5 h-5 sm:w-4 sm:h-4" />
            </button>
            <button
              onClick={onToggle}
              className="p-2 sm:p-1 rounded-md hover:bg-gray-200 transition-colors"
              title="Close Chat"
            >
              <X className="w-5 h-5 sm:w-4 sm:h-4 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-h-0">
          {showHistory ? (
            <ChatHistory
              currentSessionId={currentSessionId}
              onSessionSelect={(sessionId) => {
                setCurrentSessionId(sessionId)
                setShowHistory(false) // Switch back to chat when session is selected
              }}
              onNewSession={() => {
                setCurrentSessionId(undefined)
                setShowHistory(false) // Switch back to chat for new session
              }}
              className="h-full"
            />
          ) : (
            <Chat
              sessionId={currentSessionId}
              onSessionChange={(sessionId) => setCurrentSessionId(sessionId)}
            />
          )}
        </div>

        {/* Resize Handle - Only show on desktop */}
        {!isMobile && (
          <div
            ref={resizeRef}
            className={`
              absolute top-0 left-0 w-1 h-full cursor-col-resize
              hover:bg-blue-500 transition-colors duration-200
              ${isDragging ? 'bg-blue-500' : 'bg-gray-300'}
            `}
            onMouseDown={handleMouseDown}
          >
            {/* Visual indicator for resize handle */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
              <div className="w-1 h-8 bg-gray-400 rounded-full opacity-50"></div>
            </div>
          </div>
        )}
      </div>

      {/* Backdrop for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-25 z-30 lg:hidden"
          onClick={onToggle}
        />
      )}
    </>
  )
}

export default ResizableChatPanel 