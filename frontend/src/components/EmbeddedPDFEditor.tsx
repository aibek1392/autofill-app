import React, { useState, useEffect, useRef } from 'react'
import { X, Eye, Edit, AlertTriangle, ExternalLink, Download, RefreshCw } from 'lucide-react'

interface EmbeddedPDFEditorProps {
  isOpen: boolean
  onClose: () => void
  document: {
    doc_id: string
    filename: string
    type: string
    file_size: number
    uploaded_at: string
    processing_status: string
  } | null
  mode: 'view' | 'edit'
}

const EmbeddedPDFEditor: React.FC<EmbeddedPDFEditorProps> = ({ isOpen, onClose, document, mode }) => {
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [documentUrl, setDocumentUrl] = useState<string | null>(null)
  const [useSimplePDF, setUseSimplePDF] = useState(true)
  const [showFallback, setShowFallback] = useState(false)
  const [documentContent, setDocumentContent] = useState<string | null>(null)
  const iframeRef = useRef<HTMLIFrameElement>(null)

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'

  useEffect(() => {
    if (isOpen && document) {
      loadDocument()
    }
  }, [isOpen, document])

  const getPublicDocumentUrl = () => {
    return `${API_BASE_URL}/api/public/documents/${document?.doc_id}`
  }

  const getAuthenticatedDocumentUrl = () => {
    return `${API_BASE_URL}/api/documents/${document?.doc_id}/download`
  }

  const loadDocument = async () => {
    if (!document) return
    
    setLoading(true)
    setError(null)

    try {
      // First try the public endpoint
      const publicUrl = getPublicDocumentUrl()
      const response = await fetch(publicUrl)
      
      if (response.ok) {
        setDocumentUrl(publicUrl)
        // Convert to blob URL to avoid CORS issues
        const blob = await response.blob()
        const blobUrl = URL.createObjectURL(blob)
        setDocumentContent(blobUrl)
      } else {
        // Fallback to authenticated endpoint
        const authUrl = getAuthenticatedDocumentUrl()
        const authResponse = await fetch(authUrl, {
          headers: {
            'X-User-ID': '35849c20-9fd7-46bd-a56a-d7d95ec3d41e'
          }
        })
        
        if (authResponse.ok) {
          setDocumentUrl(authUrl)
          const blob = await authResponse.blob()
          const blobUrl = URL.createObjectURL(blob)
          setDocumentContent(blobUrl)
        } else {
          throw new Error(`Document not accessible: ${response.status}`)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load document')
      setShowFallback(true)
    } finally {
      setLoading(false)
    }
  }

  const getSimplePDFUrl = () => {
    if (!documentUrl) return null
    
    const encodedUrl = encodeURIComponent(documentUrl)
    
    if (mode === 'edit') {
      return `https://embed.simplepdf.eu/editor?open=${encodedUrl}`
    } else {
      return `https://embed.simplepdf.eu/viewer?open=${encodedUrl}`
    }
  }

  const getPDFJSUrl = () => {
    if (!documentContent) return null
    
    // Use PDF.js viewer with blob URL to avoid CORS issues
    const encodedUrl = encodeURIComponent(documentContent)
    return `https://mozilla.github.io/pdf.js/web/viewer.html?file=${encodedUrl}`
  }

  const getLocalPDFJSUrl = () => {
    if (!documentContent) return null
    
    // Alternative: Use a local PDF.js viewer or different CDN
    const encodedUrl = encodeURIComponent(documentContent)
    return `https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/web/viewer.html?file=${encodedUrl}`
  }

  const handleIframeError = () => {
    setError('Failed to load PDF editor. Switching to fallback viewer.')
    setUseSimplePDF(false)
    setShowFallback(true)
  }

  const handleRetry = () => {
    setError(null)
    setShowFallback(false)
    setUseSimplePDF(true)
    loadDocument()
  }

  const openInNewTab = () => {
    if (documentUrl) {
      const url = useSimplePDF ? getSimplePDFUrl() : getPDFJSUrl()
      if (url) {
        window.open(url, '_blank', 'noopener,noreferrer')
      }
    }
  }

  const isPDFDocument = () => {
    return document?.type === 'application/pdf' || document?.filename.toLowerCase().endsWith('.pdf')
  }

  // Cleanup blob URL on unmount
  useEffect(() => {
    return () => {
      if (documentContent && documentContent.startsWith('blob:')) {
        URL.revokeObjectURL(documentContent)
      }
    }
  }, [documentContent])

  if (!isOpen || !document) return null

  if (!isPDFDocument()) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Non-PDF Document</h2>
            <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full">
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <div className="text-center">
            <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">
              PDF viewer only supports PDF documents. This is a {document.type} file.
            </p>
            <a
              href={getAuthenticatedDocumentUrl()}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Download className="w-4 h-4 mr-2" />
              Download & View
            </a>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full h-full max-w-6xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center space-x-3">
            {mode === 'edit' ? (
              <Edit className="w-5 h-5 text-blue-600" />
            ) : (
              <Eye className="w-5 h-5 text-gray-600" />
            )}
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                {mode === 'edit' ? 'Edit PDF' : 'View PDF'}
              </h2>
              <p className="text-sm text-gray-500">{document.filename}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 relative">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
              <div className="text-center">
                <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
                <p className="text-gray-600">Loading PDF...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
              <div className="text-center max-w-md p-6">
                <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                <p className="text-red-700 mb-4">{error}</p>
                <div className="space-y-2">
                  <button
                    onClick={handleRetry}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Retry
                  </button>
                  <button
                    onClick={() => setUseSimplePDF(!useSimplePDF)}
                    className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                  >
                    Switch to {useSimplePDF ? 'PDF.js' : 'SimplePDF'} Viewer
                  </button>
                  <button
                    onClick={openInNewTab}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    Open in New Tab
                  </button>
                </div>
              </div>
            </div>
          )}

          {!loading && !error && documentContent && (
            <>
              {useSimplePDF && mode === 'edit' ? (
                // Try SimplePDF editor first for edit mode
                <iframe
                  ref={iframeRef}
                  src={getSimplePDFUrl() || ''}
                  className="w-full h-full border-0"
                  title="PDF Editor"
                  onError={handleIframeError}
                  sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-top-navigation"
                />
              ) : (
                // Use PDF.js viewer for view mode or as fallback
                <iframe
                  ref={iframeRef}
                  src={getPDFJSUrl() || ''}
                  className="w-full h-full border-0"
                  title="PDF Viewer"
                  onError={handleIframeError}
                  sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
                />
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={useSimplePDF}
                  onChange={(e) => setUseSimplePDF(e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm text-gray-600">Use SimplePDF (for editing)</span>
              </label>
            </div>
            
            <div className="flex items-center space-x-2">
              <a
                href={getAuthenticatedDocumentUrl()}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
              >
                <Download className="w-4 h-4 mr-1" />
                Download Original
              </a>
              
              <button
                onClick={openInNewTab}
                className="inline-flex items-center px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                <ExternalLink className="w-4 h-4 mr-1" />
                Open in New Tab
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default EmbeddedPDFEditor 