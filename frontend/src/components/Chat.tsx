import React, { useState, useRef, useEffect } from 'react'
import { Send, User, FileText } from 'lucide-react'
import { chatWithDocuments, chatWithDocumentsStream, ChatResponse, createChatSession, getSessionMessages, saveChatMessage } from '../lib/api'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  sources?: Array<{
    filename: string
    score: number
  }>
  timestamp: Date
  isLoading?: boolean
  isStreaming?: boolean
}

interface ChatProps {
  sessionId?: string
  onNewMessage?: (message: Message) => void
  onSessionChange?: (sessionId: string) => void
}

const Chat: React.FC<ChatProps> = ({ sessionId, onNewMessage, onSessionChange }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: "Hi! I'm your AI assistant. I can help you find information from your uploaded documents and answer questions about them. What would you like to know?",
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [useStreaming, setUseStreaming] = useState(true)
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(sessionId)
  const [savingToHistory, setSavingToHistory] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Load chat history when sessionId changes
  useEffect(() => {
    if (sessionId && sessionId !== currentSessionId) {
      loadChatHistory(sessionId)
      setCurrentSessionId(sessionId)
    }
  }, [sessionId, currentSessionId])

  const loadChatHistory = async (sessionIdToLoad: string) => {
    try {
      const historyMessages = await getSessionMessages(sessionIdToLoad)
      
      // Convert history messages to our Message format
      const convertedMessages: Message[] = []
      
      // Add welcome message
      convertedMessages.push({
        id: '1',
        type: 'assistant',
        content: "Hi! I'm your AI assistant. I can help you find information from your uploaded documents and answer questions about them. What would you like to know?",
        timestamp: new Date()
      })

      // Add history messages
      historyMessages.forEach((histMsg, index) => {
        // Add user message
        convertedMessages.push({
          id: `history_user_${index}`,
          type: 'user',
          content: histMsg.message,
          timestamp: new Date(histMsg.created_at)
        })

        // Add assistant response
        convertedMessages.push({
          id: `history_assistant_${index}`,
          type: 'assistant',
          content: histMsg.response,
          sources: histMsg.sources,
          timestamp: new Date(histMsg.created_at)
        })
      })

      setMessages(convertedMessages)
    } catch (error) {
      console.error('Failed to load chat history:', error)
      // Keep current messages if loading fails
    }
  }

  const saveMessageToHistory = async (userMessage: string, assistantResponse: string, sources?: Array<{ filename: string; score: number }>) => {
    if (!currentSessionId) return

    try {
      setSavingToHistory(true)
      await saveChatMessage(currentSessionId, userMessage, assistantResponse, sources)
    } catch (error) {
      console.error('Failed to save message to history:', error)
      // Don't block the user experience if saving fails
    } finally {
      setSavingToHistory(false)
    }
  }

  const createNewSession = async () => {
    try {
      const newSession = await createChatSession()
      setCurrentSessionId(newSession.session_id)
      onSessionChange?.(newSession.session_id)
      
      // Reset to welcome message
      setMessages([{
        id: '1',
        type: 'assistant',
        content: "Hi! I'm your AI assistant. I can help you find information from your uploaded documents and answer questions about them. What would you like to know?",
        timestamp: new Date()
      }])
    } catch (error) {
      console.error('Failed to create new session:', error)
    }
  }

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    // Add loading/streaming message
    const loadingMessageId = (Date.now() + 1).toString()
    const loadingMessage: Message = {
      id: loadingMessageId,
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: !useStreaming,
      isStreaming: useStreaming
    }
    setMessages(prev => [...prev, loadingMessage])

    try {
      if (useStreaming) {
        // Use streaming response
        let fullContent = ''
        let sources: Array<{ filename: string; score: number }> = []

        await chatWithDocumentsStream(
          inputValue,
          (chunk) => {
            if (chunk.type === 'metadata') {
              sources = chunk.sources || []
            } else if (chunk.type === 'content') {
              fullContent = chunk.full_content || fullContent + (chunk.content || '')
              // Update the streaming message with new content
              setMessages(prev => prev.map(msg => 
                msg.id === loadingMessageId 
                  ? { ...msg, content: fullContent, isLoading: false, isStreaming: true }
                  : msg
              ))
            } else if (chunk.type === 'done') {
              // Finalize the message
              setMessages(prev => prev.map(msg => 
                msg.id === loadingMessageId 
                  ? { 
                      ...msg, 
                      content: chunk.full_content || fullContent,
                      sources: sources,
                      isLoading: false,
                      isStreaming: false
                    }
                  : msg
              ))
            } else if (chunk.type === 'error') {
              setMessages(prev => prev.map(msg => 
                msg.id === loadingMessageId 
                  ? { 
                      ...msg, 
                      content: chunk.content || 'An error occurred while processing your request.',
                      sources: chunk.sources || [],
                      isLoading: false,
                      isStreaming: false
                    }
                  : msg
              ))
            }
          },
          (error) => {
            console.error('Streaming error:', error)
            setMessages(prev => prev.map(msg => 
              msg.id === loadingMessageId 
                ? { 
                    ...msg, 
                    content: `I'm sorry, I encountered an error: ${error}`,
                    isLoading: false,
                    isStreaming: false
                  }
                : msg
            ))
          },
          async () => {
            // Stream completed - save to history
            setIsLoading(false)
            
            // Create session if we don't have one
            if (!currentSessionId) {
              try {
                const newSession = await createChatSession()
                setCurrentSessionId(newSession.session_id)
                onSessionChange?.(newSession.session_id)
              } catch (error) {
                console.error('Failed to create session for history:', error)
                return
              }
            }

            // Save the completed conversation to history
            const finalMessage = messages.find(msg => msg.id === loadingMessageId)
            if (finalMessage && finalMessage.content) {
              await saveMessageToHistory(userMessage.content, finalMessage.content, finalMessage.sources)
            }
          }
        )
      } else {
        // Use traditional non-streaming response
        const response: ChatResponse = await chatWithDocuments(inputValue)
        
        const assistantMessage: Message = {
          id: (Date.now() + 2).toString(),
          type: 'assistant',
          content: response.answer,
          sources: response.sources,
          timestamp: new Date()
        }

        // Remove loading message and add real response
        setMessages(prev => prev.slice(0, -1).concat(assistantMessage))
        onNewMessage?.(assistantMessage)

        // Save to history for non-streaming
        if (!currentSessionId) {
          try {
            const newSession = await createChatSession()
            setCurrentSessionId(newSession.session_id)
            onSessionChange?.(newSession.session_id)
          } catch (error) {
            console.error('Failed to create session for history:', error)
          }
        }
        
        if (currentSessionId) {
          await saveMessageToHistory(userMessage.content, response.answer, response.sources)
        }
      }
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        type: 'assistant',
        content: "I'm sorry, I encountered an error while processing your question. Please try again or check if you have uploaded any documents.",
        timestamp: new Date()
      }
      setMessages(prev => prev.slice(0, -1).concat(errorMessage))
    } finally {
      if (!useStreaming) {
        setIsLoading(false)
      }
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="flex flex-col h-full bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center">
          <div className="relative mr-2">
            <div className="w-5 h-5 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
              <div className="w-2.5 h-2.5 bg-white rounded-full"></div>
            </div>
            <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          </div>
          <h3 className="font-medium text-gray-900">Document Chat</h3>
        </div>
        <div className="flex items-center space-x-2">
          <label className="flex items-center space-x-2 text-sm">
            <input
              type="checkbox"
              checked={useStreaming}
              onChange={(e) => setUseStreaming(e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="text-gray-600">Streaming</span>
          </label>
          <button
            onClick={createNewSession}
            className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded border"
          >
            New Chat
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`
                max-w-3xl flex items-start space-x-2
                ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}
              `}
            >
              {/* Avatar */}
              <div
                className={`
                  flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
                  ${message.type === 'user' 
                    ? 'bg-primary-600 text-white' 
                    : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                  }
                `}
              >
                {message.type === 'user' ? (
                  <User className="w-4 h-4" />
                ) : (
                  <div className="relative">
                    <div className="w-3 h-3 bg-white rounded-full"></div>
                    <div className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></div>
                  </div>
                )}
              </div>

              {/* Message Content */}
              <div
                className={`
                  px-4 py-2 rounded-lg max-w-md
                  ${message.type === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                  }
                `}
              >
                {message.isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-sm text-gray-500">Searching documents...</span>
                  </div>
                ) : (
                  <>
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    
                    {/* Streaming indicator */}
                    {message.isStreaming && (
                      <div className="flex items-center space-x-2 mt-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                        <span className="text-xs text-gray-500">Streaming...</span>
                      </div>
                    )}
                    
                    {/* Sources */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-xs text-gray-500 mb-2">Sources:</p>
                        <div className="space-y-1">
                          {message.sources.map((source, index) => (
                            <div key={index} className="flex items-center space-x-2">
                              <FileText className="w-3 h-3 text-gray-400" />
                              <span className="text-xs text-gray-600">
                                {source.filename} ({(source.score * 100).toFixed(0)}% relevance)
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
                
                <p className={`text-xs mt-1 ${message.type === 'user' ? 'text-primary-200' : 'text-gray-500'}`}>
                  {formatTimestamp(message.timestamp)}
                </p>
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about your documents..."
            className="flex-1 input-field"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <div className="flex items-center justify-between mt-2">
          <p className="text-xs text-gray-500">
            Press Enter to send • Shift+Enter for new line
          </p>
          {savingToHistory && (
            <p className="text-xs text-blue-500 flex items-center">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse mr-1"></div>
              Saving to history...
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

export default Chat 