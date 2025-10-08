import React, { useState, useEffect, useCallback } from 'react'
import { User } from '@supabase/supabase-js'
import { supabase } from '../lib'
import { getUserStats, getUserDocuments, getFilledForms, deleteDocument, UserStats, Document } from '../lib/api'
import FileUpload from '../components/FileUpload'
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import Chat from '../components/Chat'
import FormFiller from '../components/FormFiller'
import WebFormAutofill from '../components/WebFormAutofill'
import ResizableChatPanel from '../components/ResizableChatPanel'
import AuthStatus from '../components/AuthStatus'
import ConfirmDeleteModal from '../components/ConfirmDeleteModal'
import EmbeddedPDFEditor from '../components/EmbeddedPDFEditor'
import TransactionsList from '../components/TransactionsList'
import { 
  LogOut, 
  Upload, 
  MessageCircle, 
  FileText, 
  BarChart3, 
  Menu,
  X,
  Users,
  Clock,
  CheckCircle,
  AlertCircle,
  Globe,
  Edit,
  DollarSign
} from 'lucide-react'

// Custom DocuChat Icon Component
const DocuChatIcon: React.FC<{ className?: string; size?: number }> = ({ className = "", size = 24 }) => {
  return (
    <div className={`relative ${className}`} style={{ width: size, height: size }}>
      {/* Document Base */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-lg transform rotate-3"></div>
      
      {/* Document Fold */}
      <div className="absolute top-0 right-0 w-3 h-3 bg-gradient-to-br from-blue-400 to-blue-500 rounded-bl-lg transform rotate-45 origin-top-right"></div>
      
      {/* Document Lines */}
      <div className="absolute top-3 left-2 right-4 space-y-1">
        <div className="h-0.5 bg-white/80 rounded-full"></div>
        <div className="h-0.5 bg-white/60 rounded-full w-3/4"></div>
        <div className="h-0.5 bg-white/40 rounded-full w-1/2"></div>
      </div>
      
      {/* Chat Bubble */}
      <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center shadow-lg">
        <div className="w-1.5 h-1.5 bg-white rounded-full"></div>
      </div>
      
      {/* AI Pulse */}
      <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
    </div>
  )
}

interface DashboardProps {
  user?: User | null
}

type ActiveTab = 'upload' | 'chat' | 'forms' | 'web-autofill' | 'analytics' | 'transactions'

const Dashboard: React.FC<DashboardProps> = ({ user = null }) => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('upload')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [chatPanelOpen, setChatPanelOpen] = useState(false)
  const [stats, setStats] = useState<UserStats | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [filledForms, setFilledForms] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [deletingDocId, setDeletingDocId] = useState<string | null>(null)
  const [clearUploadSuccess, setClearUploadSuccess] = useState(false)
  const [showConfirmDeleteModal, setShowConfirmDeleteModal] = useState(false)
  const [documentToDelete, setDocumentToDelete] = useState<{ docId: string; filename: string } | null>(null)
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null)
  const [pdfViewerOpen, setPdfViewerOpen] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [pdfViewerMode, setPdfViewerMode] = useState<'view' | 'edit'>('view')

  // Check if we're in demo mode
  const isDemoMode = !supabase || !user

  useEffect(() => {
    loadDashboardData()
    startPolling()
    
    // Cleanup polling on unmount
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval)
      }
    }
  }, [])

  const loadDashboardData = async () => {
    try {
      const [statsData, documentsData, formsData] = await Promise.all([
        getUserStats(),
        getUserDocuments(),
        getFilledForms()
      ])
      
      setStats(statsData)
      setDocuments(documentsData.documents)
      setFilledForms(formsData.filled_forms)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      
      // Check if it's an authentication error
      if (error instanceof Error && error.message.includes('User not authenticated')) {
        // If user is not authenticated, show a message but don't crash
        console.warn('User not authenticated, some features may not work')
        setStats(null)
        setDocuments([])
        setFilledForms([])
      }
    } finally {
      setLoading(false)
    }
  }

  // Start polling for document status updates
  const startPolling = useCallback(() => {
    // Clear any existing interval
    if (pollingInterval) {
      clearInterval(pollingInterval)
    }
    
    // Poll every 3 seconds for document status updates
    const interval = setInterval(async () => {
      try {
        // Only poll if we have documents that are processing
        const hasProcessingDocs = documents.some(doc => 
          doc.processing_status === 'processing' || doc.processing_status === 'uploaded'
        )
        
        if (hasProcessingDocs) {
          const documentsData = await getUserDocuments()
          setDocuments(documentsData.documents)
          
          // Stop polling if no more processing documents
          const stillProcessing = documentsData.documents.some(doc => 
            doc.processing_status === 'processing' || doc.processing_status === 'uploaded'
          )
          
          if (!stillProcessing) {
            clearInterval(interval)
            setPollingInterval(null)
          }
        } else {
          // No processing documents, stop polling
          clearInterval(interval)
          setPollingInterval(null)
        }
      } catch (error) {
        console.error('Polling error:', error)
        // Continue polling even if there's an error
      }
    }, 3000) // Poll every 3 seconds
    
    setPollingInterval(interval)
  }, [documents, pollingInterval])

  // Update polling when documents change
  useEffect(() => {
    const hasProcessingDocs = documents.some(doc => 
      doc.processing_status === 'processing' || doc.processing_status === 'uploaded'
    )
    
    if (hasProcessingDocs && !pollingInterval) {
      startPolling()
    } else if (!hasProcessingDocs && pollingInterval) {
      clearInterval(pollingInterval)
      setPollingInterval(null)
    }
  }, [documents, pollingInterval, startPolling])

  const handleDeleteDocument = async (docId: string, filename: string) => {
    setDocumentToDelete({ docId, filename })
    setShowConfirmDeleteModal(true)
  }

  const confirmDeleteDocument = async () => {
    if (!documentToDelete) return
    
    try {
      setDeletingDocId(documentToDelete.docId)
      await deleteDocument(documentToDelete.docId)
      
      // Remove document from state
      setDocuments(prev => prev.filter(doc => doc.doc_id !== documentToDelete.docId))
      
      // Show success message
      console.log(`Document "${documentToDelete.filename}" deleted successfully`)
      
      // Refresh data to ensure consistency
      loadDashboardData()
      
    } catch (error) {
      console.error('Failed to delete document:', error)
      // Show error message to user
      alert('Failed to delete document. Please try again.')
    } finally {
      setDeletingDocId(null)
      setShowConfirmDeleteModal(false)
      setDocumentToDelete(null)
    }
  }

  const cancelDeleteDocument = () => {
    setShowConfirmDeleteModal(false)
    setDocumentToDelete(null)
  }

  // PDF Viewer handlers
  const handleEditDocument = (document: Document) => {
    setSelectedDocument(document)
    setPdfViewerMode('edit')
    setPdfViewerOpen(true)
  }

  const handleClosePdfViewer = () => {
    setPdfViewerOpen(false)
    setSelectedDocument(null)
  }

  const handleSignOut = async () => {
    try {
      await supabase?.auth.signOut()
    } catch (error) {
      console.error('Sign out error:', error)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatFileSize = (bytes: number | undefined) => {
    if (bytes === undefined || bytes === null || isNaN(bytes)) return '0 Bytes'
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const navigation = [
    { id: 'upload', name: 'Upload & Chat', icon: Upload },
    { id: 'chat', name: 'Document Chat', icon: MessageCircle },
    { id: 'forms', name: 'PDF Form Autofill', icon: FileText },
    { id: 'web-autofill', name: 'Web Form Autofill', icon: Globe },
    { id: 'transactions', name: 'Financial Transactions', icon: DollarSign },
    { id: 'analytics', name: 'Analytics', icon: BarChart3 },
  ]

  const renderContent = () => {
    switch (activeTab) {
      case 'upload':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="flex justify-center mb-4">
                <DocuChatIcon size={48} className="text-blue-600" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Upload Documents</h1>
              <p className="text-gray-600 max-w-2xl mx-auto">
                Upload your PDF, JPG, JPEG, or PNG documents and ask our AI assistant to help you find information from your uploaded documents and answer questions about them. PDFs can also be edited with our integrated editor for signing, annotating, and filling forms.
              </p>
            </div>
            
            <AuthStatus />
            
            <FileUpload 
              clearSuccess={clearUploadSuccess}
              recentDocuments={documents}
              onUploadComplete={(files) => {
                console.log('Files uploaded successfully:', files)
                // Validate the uploaded files structure
                if (files && Array.isArray(files)) {
                  files.forEach((file, index) => {
                    console.log(`Uploaded file ${index}:`, {
                      filename: file.filename,
                      file_id: file.file_id,
                      status: file.status
                    })
                  })
                } else {
                  console.warn('Invalid files structure received:', files)
                }
                // Reset the clear success flag
                setClearUploadSuccess(false)
                loadDashboardData() // Refresh data
              }}
            />

            {/* Recent Documents */}
            {documents.length > 0 && (
              <div className="card p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Your Documents</h3>
                
                {/* SimplePDF Capabilities Info */}
                <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                    <div className="text-sm text-blue-800">
                      <p className="font-medium mb-1">📄 PDF Editor Features:</p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-1 text-xs">
                        <span>• Sign documents electronically</span>
                        <span>• Add text, images, and shapes</span>
                        <span>• Fill out forms and checkboxes</span>
                        <span>• Highlight and annotate text</span>
                        <span>• Add stamps and watermarks</span>
                        <span>• Merge and split PDFs</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-3">
                  {documents.slice(0, 5).map((doc) => (
                    <div key={doc.doc_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                      <div className="flex items-center space-x-3">
                        <FileText className="w-5 h-5 text-gray-400" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{doc.filename}</p>
                          <p className="text-xs text-gray-500">
                            {formatFileSize(doc.file_size)} • {formatDate(doc.uploaded_at)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          doc.processing_status === 'completed' 
                            ? 'bg-green-100 text-green-800'
                            : doc.processing_status === 'processing'
                            ? 'bg-yellow-100 text-yellow-800'
                            : doc.processing_status === 'uploaded'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {doc.processing_status === 'completed' && <CheckCircle className="w-3 h-3 mr-1" />}
                          {doc.processing_status === 'processing' && (
                            <>
                              <div className="w-3 h-3 border-2 border-yellow-600 border-t-transparent rounded-full animate-spin mr-1" />
                              Processing...
                            </>
                          )}
                          {doc.processing_status === 'uploaded' && (
                            <>
                              <div className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mr-1" />
                              Starting...
                            </>
                          )}
                          {doc.processing_status === 'failed' && <AlertCircle className="w-3 h-3 mr-1" />}
                          {doc.processing_status === 'completed' && doc.processing_status}
                          {doc.processing_status === 'failed' && doc.processing_status}
                        </span>
                        
                        {/* Edit button for documents */}
                        {doc.processing_status === 'completed' && (
                          <button
                            onClick={() => handleEditDocument(doc)}
                            className="p-1 rounded-full bg-blue-100 text-blue-600 hover:bg-blue-200 hover:text-blue-700 transition-colors"
                            title={doc.type === 'application/pdf' ? 'Open PDF Editor - Sign, annotate, fill forms, add images' : 'View Document'}
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                        )}
                        
                        <button
                          onClick={() => handleDeleteDocument(doc.doc_id, doc.filename)}
                          disabled={deletingDocId === doc.doc_id}
                          className={`p-1 rounded-full transition-colors ${
                            deletingDocId === doc.doc_id
                              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                              : 'bg-red-100 text-red-600 hover:bg-red-200 hover:text-red-700'
                          }`}
                          title="Delete document"
                        >
                          {deletingDocId === doc.doc_id ? (
                            <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <X className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )

      case 'chat':
        return (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Document Chat</h1>
              <p className="text-gray-600">
                Ask questions about your uploaded documents. The AI will search through your documents and provide answers based on the content.
              </p>
            </div>
            
            <div className="card p-6">
              <div className="text-center py-8">
                <MessageCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Chat Moved to Side Panel</h3>
                <p className="text-gray-600 mb-4">
                  The AI Assistant chat is now available in a resizable side panel. Click the chat button in the top-right corner to open it.
                </p>
                <button
                  onClick={() => setChatPanelOpen(true)}
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Open Chat Panel
                </button>
              </div>
            </div>
          </div>
        )

      case 'forms':
        return (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Form Autofill</h1>
              <p className="text-gray-600">
                Upload a PDF form and let AI automatically fill it using information from your uploaded documents.
              </p>
            </div>
            
            <FormFiller 
              onFormFilled={(result) => {
                loadDashboardData() // Refresh data
              }}
            />

            {/* Recent Filled Forms */}
            {filledForms.length > 0 && (
              <div className="card p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Filled Forms</h3>
                <div className="space-y-3">
                  {filledForms.slice(0, 5).map((form) => (
                    <div key={form.form_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                      <div className="flex items-center space-x-3">
                        <FileText className="w-5 h-5 text-gray-400" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{form.original_form_name}</p>
                          <p className="text-xs text-gray-500">
                            {formatDate(form.created_at)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-gray-500">
                          {Object.keys(form.filled_fields || {}).length} fields filled
                        </span>
                        <a
                          href={form.filled_form_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-600 hover:text-primary-700 text-sm"
                        >
                          Download
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )

      case 'web-autofill':
        return (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Web Form Autofill</h1>
              <p className="text-gray-600">
                Analyze any web form and generate autofill data from your uploaded documents. 
                Perfect for job applications, surveys, and registration forms on any website.
              </p>
            </div>
            
            <WebFormAutofill />
          </div>
        )

      case 'transactions':
        return (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Financial Transactions</h1>
              <p className="text-gray-600">
                View parsed transactions from your uploaded financial statements and bank documents.
              </p>
            </div>

            {/* Document selector for transactions */}
            {documents.length > 0 ? (
              <div className="card p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Select a Document to View Transactions</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {documents.map((doc) => (
                    <div 
                      key={doc.doc_id} 
                      className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 cursor-pointer transition-colors"
                      onClick={() => setSelectedDocument(doc)}
                    >
                      <div className="flex items-center space-x-3">
                        <DollarSign className="w-8 h-8 text-green-600" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">{doc.filename}</p>
                          <p className="text-xs text-gray-500">
                            {formatFileSize(doc.file_size)} • {formatDate(doc.uploaded_at)}
                          </p>
                        </div>
                      </div>
                      <div className="mt-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          doc.processing_status === 'completed' 
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {doc.processing_status === 'completed' ? 'Processed' : 'Processing'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Show transactions for selected document */}
                {selectedDocument && (
                  <div className="mt-8">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-lg font-medium text-gray-900">
                        Transactions from: {selectedDocument.filename}
                      </h4>
                      <button
                        onClick={() => setSelectedDocument(null)}
                        className="text-sm text-gray-500 hover:text-gray-700"
                      >
                        Clear Selection
                      </button>
                    </div>
                    <TransactionsList 
                      docId={selectedDocument.doc_id} 
                      userId={user?.id || 'demo-user'} 
                    />
                  </div>
                )}
              </div>
            ) : (
              <div className="card p-8 text-center">
                <DollarSign className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Documents Found</h3>
                <p className="text-gray-500 mb-4">
                  Upload financial statements or bank documents to view parsed transactions.
                </p>
                <button
                  onClick={() => setActiveTab('upload')}
                  className="btn-primary"
                >
                  Upload Documents
                </button>
              </div>
            )}
          </div>
        )

      case 'analytics':
        return (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Analytics</h1>
              <p className="text-gray-600">
                Overview of your document processing and form filling activity.
              </p>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="card p-6">
                <div className="flex items-center">
                  <FileText className="w-8 h-8 text-primary-600 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-500">Total Documents</p>
                    <p className="text-2xl font-bold text-gray-900">{stats?.total_documents || 0}</p>
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <div className="flex items-center">
                  <CheckCircle className="w-8 h-8 text-green-600 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-500">Filled Forms</p>
                    <p className="text-2xl font-bold text-gray-900">{stats?.total_filled_forms || 0}</p>
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <div className="flex items-center">
                  <Clock className="w-8 h-8 text-blue-600 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-500">Processing</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {documents.filter(d => d.processing_status === 'processing').length}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <div className="flex items-center">
                  <Users className="w-8 h-8 text-purple-600 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-500">Account Type</p>
                    <p className="text-lg font-bold text-gray-900">Free</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="card p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Documents</h3>
                <div className="space-y-3">
                  {stats?.recent_documents.slice(0, 5).map((doc) => (
                    <div key={doc.doc_id} className="flex items-center space-x-3">
                      <FileText className="w-4 h-4 text-gray-400" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{doc.filename}</p>
                        <p className="text-xs text-gray-500">{formatDate(doc.uploaded_at)}</p>
                      </div>
                    </div>
                  )) || []}
                </div>
              </div>

              <div className="card p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Forms</h3>
                <div className="space-y-3">
                  {stats?.recent_filled_forms.slice(0, 5).map((form, index) => (
                    <div key={index} className="flex items-center space-x-3">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{form.original_form_name}</p>
                        <p className="text-xs text-gray-500">{formatDate(form.created_at)}</p>
                      </div>
                    </div>
                  )) || []}
                </div>
              </div>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="loading-dots mx-auto mb-4">
            <div></div>
            <div></div>
            <div></div>
            <div></div>
          </div>
          <p className="text-gray-500">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Resizable Chat Panel */}
      <ResizableChatPanel
        isOpen={chatPanelOpen}
        onToggle={() => setChatPanelOpen(!chatPanelOpen)}
        minWidth={300}
        maxWidth={600}
        defaultWidth={400}
      />

      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:relative lg:transform-none
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <DocuChatIcon size={32} className="text-primary-600" />
            <span className="text-xl font-bold text-gray-900">DocuChat</span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="mt-8">
          <div className="px-4 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id as ActiveTab)
                    setSidebarOpen(false)
                  }}
                  className={`
                    w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-200 cursor-pointer
                    ${activeTab === item.id
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }
                  `}
                  type="button"
                >
                  <Icon className="w-5 h-5 mr-3" />
                  {item.name}
                </button>
              )
            })}
          </div>
        </nav>

        {/* User Profile */}
        <div className="absolute bottom-0 w-full p-4 border-t border-gray-200">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
              <span className="text-sm font-medium text-white">
                {isDemoMode ? 'D' : user?.email?.charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {isDemoMode ? 'Demo User' : user?.email}
              </p>
              {isDemoMode && (
                <p className="text-xs text-gray-500">Demo Mode</p>
              )}
            </div>
          </div>
          <button
            onClick={handleSignOut}
            className="w-full flex items-center px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md cursor-pointer"
            type="button"
          >
            <LogOut className="w-4 h-4 mr-3" />
            {isDemoMode ? 'Exit Demo' : 'Sign Out'}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
              title="Open menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                Last updated: {new Date().toLocaleTimeString()}
              </div>
              <button
                onClick={() => setChatPanelOpen(!chatPanelOpen)}
                className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
                title={chatPanelOpen ? 'Close AI Assistant' : 'Open AI Assistant'}
              >
                <div className="relative">
                  <div className="w-4 h-4 bg-white rounded-full flex items-center justify-center">
                    <div className="w-2 h-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full"></div>
                  </div>
                  <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                </div>
                <span className="text-sm font-medium">AI Assistant</span>
              </button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-auto">
          {/* Demo Mode Banner */}
          {isDemoMode && (
            <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-blue-600 mr-2" />
                <div>
                  <h3 className="text-sm font-medium text-blue-800">Demo Mode</h3>
                  <p className="text-sm text-blue-700 mt-1">
                    You're using the app in demo mode. {!supabase ? 'Supabase is not configured.' : 'Not authenticated.'} 
                    {' '}Some features may not work as expected. 
                    <a href="/login" className="underline hover:text-blue-900">Set up authentication</a> for full functionality.
                  </p>
                </div>
              </div>
            </div>
          )}
          
          {renderContent()}
        </main>
      </div>

      {/* Confirm Delete Modal */}
      <ConfirmDeleteModal
        isOpen={showConfirmDeleteModal}
        onClose={cancelDeleteDocument}
        onConfirm={confirmDeleteDocument}
        filename={documentToDelete?.filename}
        loading={deletingDocId !== null}
      />

      {/* PDF Viewer */}
      {selectedDocument && (
        <EmbeddedPDFEditor
          isOpen={pdfViewerOpen}
          onClose={handleClosePdfViewer}
          document={selectedDocument}
          mode={pdfViewerMode}
        />
      )}
    </div>
  )
}

export default Dashboard 