import React, { useState, useEffect } from 'react'
import { X, Eye, Edit, AlertTriangle, Download, ExternalLink, RefreshCw } from 'lucide-react'

interface SimplePDFViewerProps {
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

const SimplePDFViewer: React.FC<SimplePDFViewerProps> = ({ isOpen, onClose, document, mode }) => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'

  useEffect(() => {
    if (isOpen && document) {
      loadPDF()
    }
    
    // Cleanup on unmount
    return () => {
      if (pdfUrl && pdfUrl.startsWith('blob:')) {
        URL.revokeObjectURL(pdfUrl)
      }
    }
  }, [isOpen, document])

  const loadPDF = async () => {
    if (!document) return
    
    setLoading(true)
    setError(null)

    try {
      // Try public endpoint first
      const publicUrl = `${API_BASE_URL}/api/public/documents/${document.doc_id}`
      const response = await fetch(publicUrl)
      
      if (response.ok) {
        const blob = await response.blob()
        const blobUrl = URL.createObjectURL(blob)
        setPdfUrl(blobUrl)
      } else {
        // Fallback to authenticated endpoint
        const authUrl = `${API_BASE_URL}/api/documents/${document.doc_id}/download`
        const authResponse = await fetch(authUrl, {
          headers: {
            'X-User-ID': 'test-user-123',
            'Authorization': 'Bearer test-token'
          }
        })
        
        if (authResponse.ok) {
          const blob = await authResponse.blob()
          const blobUrl = URL.createObjectURL(blob)
          setPdfUrl(blobUrl)
        } else {
          throw new Error(`Failed to load PDF: ${response.status}`)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load PDF')
    } finally {
      setLoading(false)
    }
  }

  const getSimplePDFUrl = () => {
    if (!pdfUrl) return null
    
    const encodedUrl = encodeURIComponent(pdfUrl)
    
    if (mode === 'edit') {
      return `https://embed.simplepdf.eu/editor?open=${encodedUrl}`
    } else {
      return `https://embed.simplepdf.eu/viewer?open=${encodedUrl}`
    }
  }

  const openInNewTab = () => {
    if (pdfUrl) {
      const simplePdfUrl = getSimplePDFUrl()
      if (simplePdfUrl) {
        window.open(simplePdfUrl, '_blank', 'noopener,noreferrer')
      }
    }
  }

  const downloadOriginal = () => {
    const downloadUrl = `${API_BASE_URL}/api/documents/${document?.doc_id}/download`
    window.open(downloadUrl, '_blank', 'noopener,noreferrer')
  }

  const isPDFDocument = () => {
    return document?.type === 'application/pdf' || document?.filename.toLowerCase().endsWith('.pdf')
  }

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
            <button
              onClick={downloadOriginal}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Download className="w-4 h-4 mr-2" />
              Download & View
            </button>
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
                    onClick={loadPDF}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    <RefreshCw className="w-4 h-4 mr-2 inline" />
                    Retry
                  </button>
                  <button
                    onClick={openInNewTab}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    <ExternalLink className="w-4 h-4 mr-2 inline" />
                    Open in New Tab
                  </button>
                  <button
                    onClick={downloadOriginal}
                    className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                  >
                    <Download className="w-4 h-4 mr-2 inline" />
                    Download Original
                  </button>
                </div>
              </div>
            </div>
          )}

          {!loading && !error && pdfUrl && (
            <div className="h-full flex flex-col">
              {/* PDF Display Options */}
              <div className="p-4 bg-gray-50 border-b">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-600">
                      {mode === 'edit' ? 'Edit with SimplePDF' : 'View with SimplePDF'}
                    </span>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={downloadOriginal}
                      className="inline-flex items-center px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                    >
                      <Download className="w-4 h-4 mr-1" />
                      Download
                    </button>
                    
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

              {/* PDF Content */}
              <div className="flex-1 relative">
                <iframe
                  src={getSimplePDFUrl() || ''}
                  className="w-full h-full border-0"
                  title="PDF Viewer"
                  sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-top-navigation"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SimplePDFViewer 