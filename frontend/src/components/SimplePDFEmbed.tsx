import React, { useState } from 'react'
import { X, Eye, Edit, AlertTriangle, ExternalLink } from 'lucide-react'

interface SimplePDFEmbedProps {
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

const SimplePDFEmbed: React.FC<SimplePDFEmbedProps> = ({ isOpen, onClose, document, mode }) => {
  const [error, setError] = useState<string | null>(null)

  if (!isOpen || !document) return null

  const getPublicDocumentUrl = () => {
    const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://autofill-backend-a64u.onrender.com'
    return `${API_BASE_URL}/api/public/documents/${document.doc_id}`
  }

  const getDocumentUrl = () => {
    const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://autofill-backend-a64u.onrender.com'
    return `${API_BASE_URL}/documents/${document.doc_id}/download`
  }

  const getSimplePDFUrl = () => {
    const documentUrl = getPublicDocumentUrl()
    const encodedUrl = encodeURIComponent(documentUrl)
    
    if (mode === 'edit') {
      return `https://embed.simplepdf.eu/editor?open=${encodedUrl}`
    } else {
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

  const testDocumentAccess = async () => {
    try {
      const response = await fetch(getPublicDocumentUrl())
      if (!response.ok) {
        setError(`Document access failed: ${response.status} ${response.statusText}`)
        return false
      }
      return true
    } catch (err) {
      setError(`Network error: ${err instanceof Error ? err.message : 'Unknown error'}`)
      return false
    }
  }

  const handleOpenSimplePDF = async () => {
    // Test document access first
    const canAccess = await testDocumentAccess()
    if (canAccess) {
      openInNewTab()
    }
  }

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
              SimplePDF only supports PDF documents. This is a {document.type} file.
            </p>
            <a
              href={getDocumentUrl()}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Eye className="w-4 h-4 mr-2" />
              Download & View
            </a>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            {mode === 'edit' ? (
              <Edit className="w-6 h-6 text-blue-600" />
            ) : (
              <Eye className="w-6 h-6 text-gray-600" />
            )}
            <div>
              <h2 className="text-lg font-semibold">
                {mode === 'edit' ? 'Edit PDF' : 'View PDF'}
              </h2>
              <p className="text-sm text-gray-500">{document.filename}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="text-center">
          <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
            {mode === 'edit' ? (
              <Edit className="w-10 h-10 text-blue-600" />
            ) : (
              <Eye className="w-10 h-10 text-blue-600" />
            )}
          </div>
          
          <h3 className="text-xl font-semibold mb-2">
            {mode === 'edit' ? 'Edit with SimplePDF' : 'View with SimplePDF'}
          </h3>
          
          <p className="text-gray-600 mb-6">
            {mode === 'edit' 
              ? 'Open this PDF in SimplePDF editor to add signatures, annotations, and make edits.'
              : 'Open this PDF in SimplePDF viewer for an enhanced viewing experience.'
            }
          </p>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          <div className="space-y-3">
            <button
              onClick={handleOpenSimplePDF}
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
              <strong>Note:</strong> SimplePDF will open in a new tab. You may need to allow pop-ups for this site.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SimplePDFEmbed 