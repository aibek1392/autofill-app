import React, { useCallback, useState, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react'
import { uploadDocuments, UploadedFile, Document } from '../lib/api'

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
        return <div className="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      default:
        return <File className="w-4 h-4 text-gray-500" />
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
            <div className="w-4 h-4 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-xs text-yellow-600 font-medium">Processing...</span>
          </div>
        )
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'uploaded':
        return (
          <div className="flex items-center space-x-1">
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-xs text-blue-600 font-medium">Starting...</span>
          </div>
        )
      default:
        return <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
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
          relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-200
          ${isDragActive 
            ? 'border-primary-500 bg-primary-50' 
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }
        `}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-lg font-medium text-gray-900 mb-2">
          {isDragActive ? 'Drop files here' : 'Upload your documents'}
        </p>
        <p className="text-sm text-gray-500 mb-4">
          Drag and drop files here, or click to browse
        </p>
        <p className="text-xs text-gray-400">
          Supports PDF, JPG, JPEG, PNG • Max {formatFileSize(maxSize)} per file • Max {maxFiles} files
        </p>
      </div>

      {/* Success Message - Show uploaded files */}
      {uploadedFiles.length > 0 && (
        <div className="mt-6">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-medium text-green-900">
                ✅ Upload Successful
              </h3>
              <button
                onClick={() => setUploadedFiles([])}
                className="text-green-700 hover:text-green-900 p-1"
                title="Dismiss notification"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-2">
              {uploadedFiles.map((file, index) => {
                const processingStatus = getProcessingStatus(file.filename)
                return (
                  <div key={file.file_id} className="flex items-center justify-between p-2 bg-white rounded border">
                    <div className="flex items-center space-x-3">
                      {getProcessingStatusIcon(processingStatus)}
                      <div>
                        <p className="text-sm font-medium text-gray-900">{file.filename}</p>
                        <p className="text-xs text-gray-500">
                          {file.size ? formatFileSize(file.size) : 'Size unknown'} • Status: {getStatusText(processingStatus)}
                        </p>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

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

          <div className="space-y-2 max-h-64 overflow-y-auto">
            {files.map((file) => (
              <div
                key={file.id}
                className={`
                  flex items-center justify-between p-3 rounded-lg border
                  ${file.status === 'success' ? 'border-green-200 bg-green-50' :
                    file.status === 'error' ? 'border-red-200 bg-red-50' :
                    file.status === 'uploading' ? 'border-primary-200 bg-primary-50' :
                    'border-gray-200 bg-white'
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