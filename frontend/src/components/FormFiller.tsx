import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { FileText, Upload, Download, AlertCircle, CheckCircle } from 'lucide-react'
import { uploadForm, FormFillResult, getMissingFieldSuggestions, downloadFile } from '../lib/api'

interface FormFillerProps {
  onFormFilled?: (result: FormFillResult) => void
}

const FormFiller: React.FC<FormFillerProps> = ({ onFormFilled }) => {
  const [isUploading, setIsUploading] = useState(false)
  const [formResult, setFormResult] = useState<FormFillResult | null>(null)
  const [editingFields, setEditingFields] = useState<Record<string, string>>({})
  const [suggestions, setSuggestions] = useState<Record<string, string>>({})
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    const file = acceptedFiles[0]
    setIsUploading(true)

    try {
      const result = await uploadForm(file)
      setFormResult(result)
      setEditingFields({ ...result.filled_fields })
      onFormFilled?.(result)

      // Load suggestions for missing fields
      if (result.missing_fields.length > 0) {
        setLoadingSuggestions(true)
        try {
          const suggestionsResult = await getMissingFieldSuggestions(result.missing_fields)
          setSuggestions(suggestionsResult.suggestions)
        } catch (error) {
          console.error('Failed to get suggestions:', error)
        } finally {
          setLoadingSuggestions(false)
        }
      }
    } catch (error) {
      console.error('Form upload failed:', error)
      // You might want to show an error toast here
    } finally {
      setIsUploading(false)
    }
  }, [onFormFilled])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    multiple: false
  })

  const handleFieldEdit = (fieldName: string, value: string) => {
    setEditingFields(prev => ({
      ...prev,
      [fieldName]: value
    }))
  }

  const applySuggestion = (fieldName: string, suggestion: string) => {
    setEditingFields(prev => ({
      ...prev,
      [fieldName]: suggestion
    }))
  }

  const handleDownload = async () => {
    if (!formResult) return

    try {
      const filename = formResult.filled_form_url.split('/').pop()
      if (filename) {
        const blob = await downloadFile(filename)
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
    } catch (error) {
      console.error('Download failed:', error)
    }
  }

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600'
    if (score >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getConfidenceText = (score: number) => {
    if (score >= 0.8) return 'High confidence'
    if (score >= 0.6) return 'Medium confidence'
    return 'Low confidence'
  }

  return (
    <div className="w-full">
      {!formResult ? (
        /* Upload Area */
        <div
          {...getRootProps()}
          className={`
            relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors duration-200
            ${isDragActive 
              ? 'border-primary-500 bg-primary-50' 
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
            }
          `}
        >
          <input {...getInputProps()} />
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          
          {isUploading ? (
            <div className="space-y-4">
              <div className="loading-dots mx-auto">
                <div></div>
                <div></div>
                <div></div>
                <div></div>
              </div>
              <p className="text-lg font-medium text-gray-900">Processing your form...</p>
              <p className="text-sm text-gray-500">This may take a few moments while we analyze the form and fill it with your data.</p>
            </div>
          ) : (
            <>
              <p className="text-xl font-medium text-gray-900 mb-2">
                {isDragActive ? 'Drop your PDF form here' : 'Upload a PDF form to autofill'}
              </p>
              <p className="text-gray-500 mb-4">
                Drag and drop a PDF form, or click to browse
              </p>
              <div className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-primary-700 bg-primary-100 hover:bg-primary-200">
                <Upload className="w-4 h-4 mr-2" />
                Select PDF Form
              </div>
              <p className="text-xs text-gray-400 mt-4">
                Only PDF files are supported
              </p>
            </>
          )}
        </div>
      ) : (
        /* Form Results */
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                Form Analysis Complete
              </h3>
              <p className="text-sm text-gray-500">
                {formResult.original_form_name}
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setFormResult(null)}
                className="btn-secondary"
              >
                Upload New Form
              </button>
              <button
                onClick={handleDownload}
                className="btn-primary"
              >
                <Download className="w-4 h-4 mr-2" />
                Download Filled Form
              </button>
            </div>
          </div>

          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card p-4">
              <div className="flex items-center">
                <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                <div>
                  <p className="text-sm font-medium text-gray-900">Filled Fields</p>
                  <p className="text-2xl font-bold text-green-600">
                    {Object.keys(formResult.filled_fields).length}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="card p-4">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-yellow-500 mr-2" />
                <div>
                  <p className="text-sm font-medium text-gray-900">Missing Fields</p>
                  <p className="text-2xl font-bold text-yellow-600">
                    {formResult.missing_fields.length}
                  </p>
                </div>
              </div>
            </div>

            <div className="card p-4">
              <div className="flex items-center">
                <FileText className="w-5 h-5 text-blue-500 mr-2" />
                <div>
                  <p className="text-sm font-medium text-gray-900">Overall Status</p>
                  <p className="text-sm font-bold text-blue-600">
                    {formResult.processing_status === 'completed' ? 'Complete' : 'Processing'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Filled Fields */}
          {Object.keys(formResult.filled_fields).length > 0 && (
            <div className="card p-6">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Filled Fields</h4>
              <div className="space-y-4">
                {Object.entries(formResult.filled_fields).map(([fieldName, fieldValue]) => {
                  const confidence = formResult.confidence_scores[fieldName] || 0
                  return (
                    <div key={fieldName} className="flex items-center space-x-4">
                      <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          {fieldName}
                        </label>
                        <input
                          type="text"
                          value={editingFields[fieldName] || fieldValue}
                          onChange={(e) => handleFieldEdit(fieldName, e.target.value)}
                          className="input-field"
                        />
                      </div>
                      <div className="text-right">
                        <p className={`text-xs font-medium ${getConfidenceColor(confidence)}`}>
                          {getConfidenceText(confidence)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {(confidence * 100).toFixed(0)}%
                        </p>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Missing Fields */}
          {formResult.missing_fields.length > 0 && (
            <div className="card p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-medium text-gray-900">Missing Fields</h4>
                {loadingSuggestions && (
                  <div className="text-sm text-gray-500">Loading suggestions...</div>
                )}
              </div>
              <div className="space-y-4">
                {formResult.missing_fields.map((fieldName) => (
                  <div key={fieldName} className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">
                      {fieldName}
                    </label>
                    <div className="flex space-x-2">
                      <input
                        type="text"
                        value={editingFields[fieldName] || ''}
                        onChange={(e) => handleFieldEdit(fieldName, e.target.value)}
                        placeholder={`Enter ${fieldName.toLowerCase()}...`}
                        className="flex-1 input-field"
                      />
                      {suggestions[fieldName] && suggestions[fieldName] !== 'No suggestion available' && (
                        <button
                          onClick={() => applySuggestion(fieldName, suggestions[fieldName])}
                          className="px-3 py-2 text-xs bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
                          title={`Suggestion: ${suggestions[fieldName]}`}
                        >
                          Use Suggestion
                        </button>
                      )}
                    </div>
                    {suggestions[fieldName] && (
                      <p className="text-xs text-gray-500">
                        Suggestion: {suggestions[fieldName]}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Field Mapping */}
          {Object.keys(formResult.field_mapping).length > 0 && (
            <div className="card p-6">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Data Sources</h4>
              <div className="space-y-2">
                {Object.entries(formResult.field_mapping).map(([fieldName, source]) => (
                  <div key={fieldName} className="flex justify-between text-sm">
                    <span className="font-medium text-gray-700">{fieldName}:</span>
                    <span className="text-gray-500">{source}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default FormFiller 