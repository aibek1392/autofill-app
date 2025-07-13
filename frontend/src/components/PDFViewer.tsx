import React, { useState, useEffect } from 'react'
import { X, Eye, Edit, AlertTriangle, ExternalLink } from 'lucide-react'

interface PDFViewerProps {
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

const PDFViewer: React.FC<PDFViewerProps> = ({ isOpen, onClose, document, mode }) => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen && document) {
      setLoading(true)
      setError(null)
      
      // Simulate loading time
      const timer = setTimeout(() => {
        setLoading(false)
      }, 1000)
      
      return () => clearTimeout(timer)
    }
  }, [isOpen, document])

  if (!isOpen || !document) return null

  const getDocumentUrl = () => {
    // Construct the URL to access the uploaded document
    const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://autofill-backend-a64u.onrender.com'
    return `${API_BASE_URL}/documents/${document.doc_id}/download`
  }

  const getPublicDocumentUrl = () => {
    // Construct the public URL for SimplePDF to access the document
    const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://autofill-backend-a64u.onrender.com'
    return `${API_BASE_URL}/api/public/documents/${document.doc_id}`
  }

  const getSimplePDFUrl = () => {
    const documentUrl = getPublicDocumentUrl()
    const encodedUrl = encodeURIComponent(documentUrl)
    
    if (mode === 'edit') {
      // For editing mode, use the SimplePDF editor
      return `https://embed.simplepdf.eu/editor?open=${encodedUrl}`
    } else {
      // For viewing mode, use the SimplePDF viewer
      return `https://embed.simplepdf.eu/viewer?open=${encodedUrl}`
    }
  }

  const isPDFDocument = () => {
    return document.type === 'application/pdf' || document.filename.toLowerCase().endsWith('.pdf')
  }

  const openInNewTab = () => {
    const simplePdfUrl = getSimplePDFUrl()
    window.open(simplePdfUrl, '_blank', 'noopener,noreferrer')
  }

  const renderContent = () => {
    if (loading) {
      return (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600">Loading document...</p>
          </div>
        </div>
      )
    }

    if (error) {
      return (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <X className="w-6 h-6 text-red-600" />
            </div>
            <p className="text-red-600 font-medium mb-2">Error loading document</p>
            <p className="text-gray-600 text-sm">{error}</p>
          </div>
        </div>
      )
    }

    if (!isPDFDocument()) {
      return (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-6 h-6 text-yellow-600" />
            </div>
            <p className="text-yellow-600 font-medium mb-2">Non-PDF Document</p>
            <p className="text-gray-600 text-sm mb-4">
              SimplePDF editor only supports PDF documents. This is a {document.type} file.
            </p>
            <a
              href={getDocumentUrl()}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Eye className="w-4 h-4 mr-2" />
              Download & View
            </a>
          </div>
        </div>
      )
    }

    // For PDF documents, show options to open in SimplePDF
    return (
      <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
            {mode === 'edit' ? (
              <Edit className="w-8 h-8 text-blue-600" />
            ) : (
              <Eye className="w-8 h-8 text-blue-600" />
            )}
          </div>
          
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {mode === 'edit' ? 'Edit PDF with SimplePDF' : 'View PDF with SimplePDF'}
          </h3>
          
          <p className="text-gray-600 text-sm mb-6">
            {mode === 'edit' 
              ? 'Open this PDF in SimplePDF editor to add signatures, annotations, and make edits.'
              : 'Open this PDF in SimplePDF viewer for an enhanced viewing experience.'
            }
          </p>

          <div className="space-y-3">
            <button
              onClick={openInNewTab}
              className="w-full inline-flex items-center justify-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <ExternalLink className="w-5 h-5 mr-2" />
              {mode === 'edit' ? 'Open in SimplePDF Editor' : 'Open in SimplePDF Viewer'}
            </button>
            
            <a
              href={getDocumentUrl()}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full inline-flex items-center justify-center px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <Eye className="w-5 h-5 mr-2" />
              Download Original PDF
            </a>
          </div>

          <div className="mt-6 p-4 bg-yellow-50 rounded-lg">
            <p className="text-xs text-yellow-800">
              <strong>Note:</strong> SimplePDF will open in a new tab due to security restrictions. 
              You may need to allow pop-ups for this site.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full h-full max-w-4xl max-h-[80vh] flex flex-col">
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
        <div className="flex-1 relative" style={{ height: '500px' }}>
          {renderContent()}
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              {isPDFDocument() ? (
                mode === 'edit' ? (
                  <span>✏️ SimplePDF editor provides full PDF editing capabilities</span>
                ) : (
                  <span>👁️ SimplePDF viewer offers enhanced PDF viewing experience</span>
                )
              ) : (
                <span>📄 Non-PDF document - use download link to view</span>
              )}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PDFViewer 