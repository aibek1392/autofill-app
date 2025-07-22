import React, { useCallback, useState, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { File, X, CheckCircle, AlertCircle, Upload, ArrowUp } from 'lucide-react'
import { uploadDocuments, UploadedFile, Document } from '../lib/api'



// Simple Arrow Up Icon Component
const UploadIcon: React.FC<{ isDragActive?: boolean; className?: string }> = ({ isDragActive = false, className = "" }) => {
  return (
    <div className={`relative ${className} group`}>
      <div className="relative w-16 h-16 mx-auto mb-4">
        {/* Background Circle with Gradient */}
        <div className={`
          absolute inset-0 rounded-full transition-all duration-500 ease-in-out flex items-center justify-center
          ${isDragActive 
            ? 'bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 shadow-lg transform scale-110' 
            : 'bg-gradient-to-r from-blue-100 via-purple-100 to-pink-100 group-hover:from-blue-200 group-hover:via-purple-200 group-hover:to-pink-200'
          }
        `}>
          {/* Arrow Up Icon */}
          <ArrowUp 
            className={`
              w-8 h-8 transition-all duration-300 ease-in-out
              ${isDragActive 
                ? 'text-white transform scale-110' 
                : 'text-purple-600 group-hover:text-purple-700 group-hover:scale-110'
              }
            `}
          />
        </div>
        
        {/* Hover Ring Effect */}
        {!isDragActive && (
          <div className="absolute inset-0 rounded-full border-2 border-transparent group-hover:border-purple-300 transition-all duration-300"></div>
        )}
      </div>
    </div>
  )
}

interface FileUploadProps {
  onUploadComplete?: (files: UploadedFile[]) => void
  accept?: string[]
  maxFiles?: number
  maxSize?: number
  clearSuccess?: boolean // New prop to clear success notification
  recentDocuments?: Document[] // New prop to show real processing status
}

interface FileWithStatus extends File {
  id: string
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
}

const FileUpload: React.FC<FileUploadProps> = ({
  onUploadComplete,
  accept = ['.pdf', '.jpg', '.jpeg', '.png'],
  maxFiles = 10,
  maxSize = 10 * 1024 * 1024, // 10MB
  clearSuccess = false, // New prop
  recentDocuments = [], // New prop
}) => {
  const [files, setFiles] = useState<FileWithStatus[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])

  // Clear success notification when clearSuccess prop changes
  useEffect(() => {
    if (clearSuccess) {
      setUploadedFiles([])
    }
  }, [clearSuccess])

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return
    
    setIsUploading(true)
    
    try {
      const result = await uploadDocuments(acceptedFiles)
      
      if (result.files && result.files.length > 0) {
        setUploadedFiles(result.files)
        onUploadComplete?.(result.files)
      }
    } catch (error) {
      console.error('Upload failed:', error)
      
      // Check if it's an authentication error
      if (error instanceof Error && error.message.includes('User not authenticated')) {
        alert('Please log in to upload documents. You need to be authenticated to use this feature.')
      } else {
        alert(error instanceof Error ? error.message : 'Upload failed')
      }
    } finally {
      setIsUploading(false)
    }
  }, [onUploadComplete])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png']
    },
    maxFiles,
    maxSize,
    multiple: true
  })

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(file => file.id !== id))
  }

  const uploadFiles = async () => {
    const filesToUpload = files.filter(f => f.status === 'pending')
    if (filesToUpload.length === 0) return

    setIsUploading(true)

    try {
      // Update status to uploading
      setFiles(prev => prev.map(f => 
        filesToUpload.some(ftd => ftd.id === f.id) 
          ? { ...f, status: 'uploading' } 
          : f
      ))

      // Since FormData.append() accepts File objects, and FileWithStatus extends File,
      // we can pass them directly. The FormData will extract the file content properly.
      const result = await uploadDocuments(filesToUpload)

      // Update status to success and clear pending files
      setFiles([]) // Clear the pending files since upload is complete
      
      // Store uploaded files information
      setUploadedFiles(result.files)
      
      onUploadComplete?.(result.files)
    } catch (error) {
      // Update status to error
      setFiles(prev => prev.map(f => 
        filesToUpload.some(ftd => ftd.id === f.id) 
          ? { ...f, status: 'error', error: 'Upload failed' } 
          : f
      ))
      console.error('Upload failed:', error)
    } finally {
      setIsUploading(false)
    }
  }

  const clearAll = () => {
    setFiles([])
    setUploadedFiles([])
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'uploading':
        return <div className="w-4 h-4 border-2 border-gradient-to-r from-blue-500 to-purple-500 border-t-transparent rounded-full animate-spin" />
      default:
        return <File className="w-4 h-4 text-gradient-to-r from-blue-500 to-purple-500" />
    }
  }

  const formatFileSize = (bytes: number | undefined) => {
    if (bytes === undefined || bytes === null || isNaN(bytes)) return '0 Bytes'
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // Get processing status from recent documents
  const getProcessingStatus = (filename: string) => {
    const doc = recentDocuments.find(d => d.filename === filename)
    return doc?.processing_status || 'uploaded'
  }

  // Get processing status icon with better visual feedback
  const getProcessingStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'processing':
        return (
          <div className="flex items-center space-x-1">
            <div className="w-4 h-4 border-2 border-gradient-to-r from-yellow-500 to-orange-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-xs text-gradient-to-r from-yellow-600 to-orange-600 font-medium">Processing...</span>
          </div>
        )
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'uploaded':
        return (
          <div className="flex items-center space-x-1">
            <div className="w-4 h-4 border-2 border-gradient-to-r from-blue-500 to-purple-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-xs text-gradient-to-r from-blue-600 to-purple-600 font-medium">Starting...</span>
          </div>
        )
      default:
        return <div className="w-4 h-4 border-2 border-gradient-to-r from-gray-400 to-gray-500 border-t-transparent rounded-full animate-spin" />
    }
  }

  // Get status text with more descriptive messages
  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Ready to use'
      case 'processing':
        return 'Processing document...'
      case 'failed':
        return 'Processing failed'
      case 'uploaded':
        return 'Preparing to process...'
      default:
        return status
    }
  }

  return (
    <div className="w-full">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300
          ${isDragActive 
            ? 'border-blue-500 bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 shadow-lg scale-[1.02]' 
            : 'border-gray-300 hover:border-blue-400 hover:bg-gradient-to-br hover:from-blue-50 hover:via-purple-50 hover:to-pink-50 hover:shadow-md'
          }
        `}
      >
        <input {...getInputProps()} />
        <UploadIcon isDragActive={isDragActive} />
        <p className="text-lg font-semibold text-gray-900 mb-2">
          {isDragActive ? 'Drop files here' : 'Upload your documents'}
        </p>
        <p className="text-sm text-gray-600 mb-4">
          Drag and drop files here, or click to browse
        </p>
        <div className="flex items-center justify-center space-x-4 text-xs text-gray-500">
          <span className="flex items-center">
            <div className="w-2 h-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full mr-1"></div>
            PDF, JPG, JPEG, PNG
          </span>
          <span className="flex items-center">
            <div className="w-2 h-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full mr-1"></div>
            Max {formatFileSize(maxSize)}
          </span>
          <span className="flex items-center">
            <div className="w-2 h-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full mr-1"></div>
            Max {maxFiles} files
          </span>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Selected Files ({files.length})
            </h3>
            <button
              onClick={clearAll}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Clear all
            </button>
          </div>

          <div className="space-y-3 max-h-64 overflow-y-auto">
            {files.map((file) => (
              <div
                key={file.id}
                className={`
                  flex items-center justify-between p-4 rounded-xl border transition-all duration-200
                  ${file.status === 'success' ? 'border-green-300 bg-gradient-to-r from-green-50 via-emerald-50 to-teal-50 shadow-sm' :
                    file.status === 'error' ? 'border-red-300 bg-gradient-to-r from-red-50 via-pink-50 to-rose-50 shadow-sm' :
                    file.status === 'uploading' ? 'border-blue-300 bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 shadow-sm' :
                    'border-gray-200 bg-white hover:shadow-md hover:border-gray-300'
                  }
                `}
              >
                <div className="flex items-center space-x-3 flex-1">
                  {getStatusIcon(file.status)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {file.size !== undefined && file.size !== null ? formatFileSize(file.size) : 'Size unknown'}
                    </p>
                    {file.error && (
                      <p className="text-xs text-red-600 mt-1">{file.error}</p>
                    )}
                  </div>
                </div>

                <button
                  onClick={() => removeFile(file.id)}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded"
                  disabled={file.status === 'uploading'}
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          {/* Upload Button */}
          <div className="mt-4 flex justify-end space-x-3">
            <button
              onClick={clearAll}
              className="btn-secondary"
              disabled={isUploading}
            >
              Clear All
            </button>
            <button
              onClick={uploadFiles}
              disabled={isUploading || !files.some(f => f.status === 'pending')}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUploading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                  Uploading...
                </>
              ) : (
                `Upload ${files.filter(f => f.status === 'pending').length} Files`
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default FileUpload 