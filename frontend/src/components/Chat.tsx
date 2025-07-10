import React, { useState, useRef, useEffect } from 'react'
import { Send, MessageCircle, FileText, Bot, User } from 'lucide-react'
import { chatWithDocuments, chatWithDocumentsStream, ChatResponse } from '../lib/api'

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
  onNewMessage?: (message: Message) => void
}

const Chat: React.FC<ChatProps> = ({ onNewMessage }) => {
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
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

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
          () => {
            // Stream completed
            setIsLoading(false)
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
          <MessageCircle className="w-5 h-5 text-primary-600 mr-2" />
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
            onClick={() => setMessages([{
              id: '1',
              type: 'assistant',
              content: "Hi! I'm your AI assistant. I can help you find information from your uploaded documents and answer questions about them. What would you like to know?",
              timestamp: new Date()
            }])}
            className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded border"
          >
            Clear Chat
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
                    : 'bg-gray-200 text-gray-600'
                  }
                `}
              >
                {message.type === 'user' ? (
                  <User className="w-4 h-4" />
                ) : (
                  <Bot className="w-4 h-4" />
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
        <p className="text-xs text-gray-500 mt-2">
          Press Enter to send • Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}

export default Chat 