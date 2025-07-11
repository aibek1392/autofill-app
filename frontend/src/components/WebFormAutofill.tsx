import React, { useState, useEffect } from 'react'
import { Copy, Check, ExternalLink, Loader2, AlertCircle, CheckCircle, Globe, Code, Bookmark } from 'lucide-react'
import { getUserId } from '../lib/api'  // Import the centralized getUserId function

interface WebFormAutofillProps {
  onClose?: () => void
  className?: string
}

interface BookmarkletResponse {
  bookmarklet: string
  instructions: string[]
  html_instructions: string
}

interface FormAnalysis {
  url: string
  forms_count: number
  forms: Array<{
    form_index: number
    action: string
    method: string
    fields: Array<{
      type: string
      input_type: string
      name: string
      id: string
      label: string
      placeholder: string
      required: boolean
      purpose: string
      selector: string
    }>
  }>
  metadata: {
    title: string
    domain: string
  }
}

interface AutofillResult {
  autofill_data: Record<string, Record<string, string>>
  confidence_scores: Record<string, number>
  missing_fields: string[]
  field_mapping: Record<string, string>
  form_analysis: FormAnalysis
}

const WebFormAutofill: React.FC<WebFormAutofillProps> = ({ className = '' }) => {
  const [url, setUrl] = useState('https://jobs.ashbyhq.com/wander/121c24e0-eeff-49a8-ac56-793d2dbc9fcd/application')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isGeneratingAutofill, setIsGeneratingAutofill] = useState(false)
  const [formAnalysis, setFormAnalysis] = useState<FormAnalysis | null>(null)
  const [autofillResult, setAutofillResult] = useState<AutofillResult | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [bookmarklet, setBookmarklet] = useState<BookmarkletResponse | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [isLoadingBookmarklet, setIsLoadingBookmarklet] = useState(false)
  const [copiedBookmarklet, setCopiedBookmarklet] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [autofillData, setAutofillData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [matchedFields, setMatchedFields] = useState<any>({})
  const [confidence, setConfidence] = useState<number>(0)

  const analyzeForm = async () => {
    if (!url) return

    setIsAnalyzing(true)
    setError(null)
    try {
      const response = await fetch('http://localhost:8000/api/analyze-web-form', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url })
      })

      if (response.ok) {
        const analysis = await response.json()
        setFormAnalysis(analysis)
        console.log('Form analysis:', analysis)
      } else {
        const errorData = await response.json().catch(() => ({}))
        setError(`Failed to analyze form: ${errorData.detail || response.statusText}`)
        console.error('Failed to analyze form:', errorData)
      }
    } catch (error) {
      setError(`Error analyzing form: ${error instanceof Error ? error.message : 'Unknown error'}`)
      console.error('Error analyzing form:', error)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const generateAutofill = async () => {
    if (!url) return

    setIsGeneratingAutofill(true)
    setError(null)
    try {
      const userId = await getUserId()
      const response = await fetch('http://localhost:8000/api/generate-web-autofill', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({ url })
      })

      if (response.ok) {
        const result = await response.json()
        console.log('Backend response:', result)
        
        // The backend returns: { form_analysis, autofill_data, url }
        // We need to transform this into the expected format
        const transformedResult = {
          autofill_data: result.autofill_data.autofill_data || result.autofill_data,
          confidence_scores: result.autofill_data.confidence_scores || {},
          missing_fields: result.autofill_data.missing_fields || [],
          field_mapping: result.autofill_data.field_mapping || {},
          form_analysis: result.form_analysis
        }
        
        setAutofillResult(transformedResult)
        setFormAnalysis(result.form_analysis)
        setAutofillData(result.autofill_data)
        
        // Calculate overall confidence
        const confidenceValues = Object.values(transformedResult.confidence_scores) as number[]
        const avgConfidence = confidenceValues.length > 0 
          ? confidenceValues.reduce((a: number, b: number) => a + b, 0) / confidenceValues.length 
          : 0
        setConfidence(avgConfidence)
        
        // Set matched fields for display
        setMatchedFields(transformedResult.field_mapping)
        
      } else {
        const errorData = await response.json().catch(() => ({}))
        setError(`Failed to generate autofill: ${errorData.detail || response.statusText}`)
        console.error('Failed to generate autofill:', errorData)
      }
    } catch (error) {
      setError(`Error generating autofill: ${error instanceof Error ? error.message : 'Unknown error'}`)
      console.error('Error generating autofill:', error)
    } finally {
      setIsGeneratingAutofill(false)
    }
  }

  const generateBookmarkletScript = () => {
    const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'
    
    return `
(function() {
  // Content script for form autofill
  const API_BASE = '${API_BASE_URL}';
  
  // Get user ID from authentication or use demo fallback
  async function getUserId() {
    // Try to get from Supabase auth if available
    if (window.supabase) {
      const { data: { user } } = await window.supabase.auth.getUser();
      if (user?.id) return user.id;
    }
    // Fallback to demo user
    return '550e8400-e29b-41d4-a716-446655440000';
  }
  
  // Create autofill UI
  function createAutofillUI() {
    // Remove existing UI if present
    const existing = document.getElementById('ai-autofill-panel');
    if (existing) existing.remove();
    
    const panel = document.createElement('div');
    panel.id = 'ai-autofill-panel';
    panel.style.cssText = \`
      position: fixed;
      top: 20px;
      right: 20px;
      width: 320px;
      background: white;
      border: 2px solid #3b82f6;
      border-radius: 8px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.15);
      z-index: 10000;
      font-family: system-ui, -apple-system, sans-serif;
      font-size: 14px;
    \`;
    
    panel.innerHTML = \`
      <div style="padding: 16px; border-bottom: 1px solid #e5e7eb;">
        <div style="display: flex; justify-content: between; align-items: center;">
          <h3 style="margin: 0; color: #1f2937; font-size: 16px;">AI Form Autofill</h3>
          <button id="close-autofill" style="background: none; border: none; font-size: 18px; cursor: pointer;">&times;</button>
        </div>
      </div>
      <div id="autofill-content" style="padding: 16px;">
        <button id="scan-form" style="width: 100%; padding: 8px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer;">
          Scan & Autofill Form
        </button>
        <div id="autofill-status" style="margin-top: 12px; font-size: 12px; color: #6b7280;"></div>
        <div id="field-matches" style="margin-top: 12px;"></div>
      </div>
    \`;
    
    document.body.appendChild(panel);
    
    // Add event listeners
    document.getElementById('close-autofill').onclick = () => panel.remove();
    document.getElementById('scan-form').onclick = scanAndAutofillForm;
    
    return panel;
  }
  
  // Extract form fields from the page
  function extractFormFields() {
    const fields = [];
    const forms = document.querySelectorAll('form');
    
    forms.forEach((form, formIndex) => {
      const inputs = form.querySelectorAll('input, textarea, select');
      
      inputs.forEach(input => {
        if (input.type === 'hidden' || input.type === 'submit' || input.type === 'button') return;
        
        const fieldInfo = {
          name: input.name || input.id || \`field_\${fields.length}\`,
          type: input.type || 'text',
          label: findFieldLabel(input),
          placeholder: input.placeholder || '',
          required: input.required,
          selector: generateSelector(input),
          element: input
        };
        
        fields.push(fieldInfo);
      });
    });
    
    return fields;
  }
  
  // Find label for a form field
  function findFieldLabel(element) {
    // Check for explicit label
    if (element.id) {
      const label = document.querySelector(\`label[for="\${element.id}"]\`);
      if (label) return label.textContent.trim();
    }
    
    // Check for wrapping label
    const parentLabel = element.closest('label');
    if (parentLabel) {
      const labelText = parentLabel.textContent.replace(element.value || '', '').trim();
      if (labelText) return labelText;
    }
    
    // Check for nearby text
    const prevSibling = element.previousElementSibling;
    if (prevSibling && ['LABEL', 'SPAN', 'DIV'].includes(prevSibling.tagName)) {
      const text = prevSibling.textContent.trim();
      if (text.length < 100) return text;
    }
    
    return element.placeholder || element.name || 'Unknown Field';
  }
  
  // Generate CSS selector for element
  function generateSelector(element) {
    if (element.id) return \`#\${element.id}\`;
    if (element.name) return \`[name="\${element.name}"]\`;
    return element.tagName.toLowerCase();
  }
  
  // Scan form and get autofill data
  async function scanAndAutofillForm() {
    const statusDiv = document.getElementById('autofill-status');
    const matchesDiv = document.getElementById('field-matches');
    
    statusDiv.textContent = 'Scanning form fields...';
    matchesDiv.innerHTML = '';
    
    try {
      const fields = extractFormFields();
      
      if (fields.length === 0) {
        statusDiv.textContent = 'No fillable form fields found on this page.';
        return;
      }
      
      statusDiv.textContent = \`Found \${fields.length} fields. Getting matches...\`;
      
      // Prepare fields for bulk matching
      const fieldsForMatching = fields.map(field => ({
        name: field.name,
        label: field.label,
        type: field.type,
        context: field.placeholder,
        selector: field.selector
      }));
      
      // Call bulk field matching API
      const response = await fetch(\`\${API_BASE}/api/match-fields-bulk\`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': await getUserId()
        },
        body: JSON.stringify({
          fields: fieldsForMatching,
          user_id: await getUserId()
        })
      });
      
      if (!response.ok) {
        throw new Error(\`API error: \${response.status}\`);
      }
      
      const result = await response.json();
      const matchedFields = result.matched_fields;
      
      statusDiv.textContent = \`Matched \${result.matched_count} of \${result.total_fields} fields\`;
      
      // Display matches and autofill
      let autofillCount = 0;
      matchesDiv.innerHTML = '<div style="max-height: 200px; overflow-y: auto;">';
      
      for (const field of fields) {
        const match = matchedFields[field.name];
        if (match && match.matched && match.confidence > 0.3) {
          // Autofill the field
          const element = field.element;
          if (element) {
            element.value = match.value;
            element.dispatchEvent(new Event('input', { bubbles: true }));
            element.dispatchEvent(new Event('change', { bubbles: true }));
            autofillCount++;
          }
          
          // Add to UI
          const matchDiv = document.createElement('div');
          matchDiv.style.cssText = 'margin-bottom: 8px; padding: 8px; background: #f0f9ff; border-radius: 4px; border-left: 3px solid #3b82f6;';
          matchDiv.innerHTML = \`
            <div style="font-weight: 500; color: #1f2937;">\${field.label}</div>
            <div style="color: #3b82f6; font-size: 12px;">\${match.value}</div>
            <div style="color: #6b7280; font-size: 11px;">Confidence: \${(match.confidence * 100).toFixed(0)}% | Source: \${match.source || 'Unknown'}</div>
          \`;
          matchesDiv.appendChild(matchDiv);
        } else if (match) {
          // Show low confidence matches
          const matchDiv = document.createElement('div');
          matchDiv.style.cssText = 'margin-bottom: 8px; padding: 8px; background: #fef3f2; border-radius: 4px; border-left: 3px solid #ef4444;';
          matchDiv.innerHTML = \`
            <div style="font-weight: 500; color: #1f2937;">\${field.label}</div>
            <div style="color: #ef4444; font-size: 12px;">No confident match found</div>
            <div style="color: #6b7280; font-size: 11px;">Best: \${match.value || 'None'} (Confidence: \${(match.confidence * 100).toFixed(0)}%)</div>
          \`;
          matchesDiv.appendChild(matchDiv);
        }
      }
      
      matchesDiv.innerHTML += '</div>';
      
      if (autofillCount > 0) {
        statusDiv.innerHTML = \`<span style="color: #10b981;">✓ Autofilled \${autofillCount} fields successfully!</span>\`;
      } else {
        statusDiv.innerHTML = \`<span style="color: #f59e0b;">⚠ No fields could be autofilled with high confidence</span>\`;
      }
      
    } catch (error) {
      console.error('Autofill error:', error);
      statusDiv.innerHTML = \`<span style="color: #ef4444;">Error: \${error.message}</span>\`;
    }
  }
  
  // Initialize the autofill UI
  createAutofillUI();
  
})();`;
  };

  const generateBookmarklet = () => {
    const script = generateBookmarkletScript();
    return `javascript:${encodeURIComponent(script)}`;
  };

  const copyBookmarkletToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(generateBookmarklet());
      setCopiedBookmarklet(true);
      setTimeout(() => setCopiedBookmarklet(false), 2000);
    } catch (err) {
      console.error('Failed to copy bookmarklet:', err);
      alert('Failed to copy bookmarklet. Please try again.');
    }
  };

  const testFieldMatching = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Test with sample form fields from the Ashby form
      const sampleFields = [
        { name: 'first_name', label: 'First Name', type: 'text', context: 'Enter your first name' },
        { name: 'last_name', label: 'Last Name', type: 'text', context: 'Enter your last name' },
        { name: 'email', label: 'Email Address', type: 'email', context: 'Enter your email address' },
        { name: 'phone', label: 'Phone Number', type: 'tel', context: 'Enter your phone number' },
        { name: 'linkedin', label: 'LinkedIn Profile', type: 'url', context: 'Enter your LinkedIn profile URL' },
        { name: 'portfolio', label: 'Portfolio Website', type: 'url', context: 'Enter your portfolio website URL' },
        { name: 'cover_letter', label: 'Cover Letter', type: 'textarea', context: 'Tell us why you are interested in this role' }
      ];

      const userId = await getUserId();
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/match-fields-bulk`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({
          fields: sampleFields,
          user_id: userId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setMatchedFields(result.matched_fields);
      setConfidence(result.matched_count / result.total_fields);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const generateWebAutofill = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/generate-web-autofill`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': localStorage.getItem('user_id') || '550e8400-e29b-41d4-a716-446655440000'
        },
        body: JSON.stringify({
          url: url,
          user_id: localStorage.getItem('user_id') || '550e8400-e29b-41d4-a716-446655440000'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setAutofillData(result);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600'
    if (score >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getConfidenceBadge = (score: number) => {
    if (score >= 0.8) return 'bg-green-100 text-green-800'
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  return (
    <div className={`w-full space-y-6 ${className}`}>
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <Globe className="w-8 h-8 text-blue-600 mr-3" />
          <h2 className="text-2xl font-bold text-gray-900">Web Form Autofill</h2>
        </div>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Analyze any web form and generate autofill data from your uploaded documents. 
          Perfect for job applications, surveys, and registration forms.
        </p>
      </div>

      {/* URL Input Section */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Enter Form URL</h3>
        <div className="flex space-x-3">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/job-application"
            className="flex-1 input-field"
          />
          <div className="flex space-x-4">
            <button
              onClick={analyzeForm}
              disabled={!url || isAnalyzing}
              className="btn-primary"
            >
              {isAnalyzing ? 'Analyzing...' : 'Analyze Form'}
            </button>
            <button
              onClick={generateAutofill}
              disabled={!url || isGeneratingAutofill}
              className="btn-primary"
            >
              {isGeneratingAutofill ? 'Generating...' : 'Generate Autofill'}
            </button>
            <button
              onClick={testFieldMatching}
              disabled={isLoading}
              className="btn-secondary"
            >
              {isLoading ? 'Testing...' : 'Test Field Matching'}
            </button>
          </div>
        </div>
        
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">Example URLs to try:</h4>
          <div className="space-y-1 text-sm">
            <button 
              onClick={() => setUrl('https://jobs.ashbyhq.com/wander/121c24e0-eeff-49a8-ac56-793d2dbc9fcd/application')}
              className="block text-blue-600 hover:text-blue-800 underline"
            >
              Wander Job Application (Ashby)
            </button>
            <button 
              onClick={() => setUrl('https://apply.workable.com/posthog/j/examples')}
              className="block text-blue-600 hover:text-blue-800 underline"
            >
              PostHog Job Application (Workable)
            </button>
          </div>
        </div>
      </div>

      {/* Bookmarklet Section */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Bookmark className="w-5 h-5 text-purple-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">AI Autofill Bookmarklet</h3>
          </div>
          <button
            onClick={copyBookmarkletToClipboard}
            disabled={isLoadingBookmarklet}
            className="btn-secondary"
          >
            {isLoadingBookmarklet ? 'Generating...' : 'Copy Bookmarklet'}
          </button>
        </div>
        
        <p className="text-gray-600 mb-4">
          Get a one-click bookmarklet that can autofill any form on any website using your uploaded documents.
        </p>

        {bookmarklet && (
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">Bookmarklet Code</h4>
                <button
                  onClick={copyBookmarkletToClipboard}
                  className="flex items-center space-x-2 text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded hover:bg-blue-200"
                >
                  {copiedBookmarklet ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  <span>{copiedBookmarklet ? 'Copied!' : 'Copy'}</span>
                </button>
              </div>
              <code className="text-xs bg-white p-2 border rounded block overflow-x-auto">
                {bookmarklet.bookmarklet}
              </code>
            </div>

            <div className="bg-green-50 p-4 rounded-lg">
              <h4 className="font-medium text-green-900 mb-2">How to use:</h4>
              <ol className="text-sm text-green-800 space-y-1 list-decimal list-inside">
                {bookmarklet.instructions.map((instruction, index) => (
                  <li key={index}>{instruction.replace(/^\d+\.\s*/, '')}</li>
                ))}
              </ol>
            </div>

            <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
              <div className="flex items-start space-x-2">
                <Code className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-yellow-900 mb-1">Quick Setup</h4>
                  <p className="text-sm text-yellow-800 mb-3">
                    Drag this button to your bookmarks bar for instant access:
                  </p>
                  <a
                    href={bookmarklet.bookmarklet}
                    className="inline-flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium"
                    onDragStart={(e) => {
                      e.dataTransfer.setData('text/plain', bookmarklet.bookmarklet)
                    }}
                  >
                    <Globe className="w-4 h-4" />
                    <span>🤖 AI Autofill</span>
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Form Analysis Results */}
      {formAnalysis && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Form Analysis</h3>
            <a
              href={formAnalysis.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-1 text-blue-600 hover:text-blue-800 text-sm"
            >
              <ExternalLink className="w-4 h-4" />
              <span>View Form</span>
            </a>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{formAnalysis.forms_count}</div>
              <div className="text-sm text-blue-800">Forms Found</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {formAnalysis.forms.reduce((total, form) => total + form.fields.length, 0)}
              </div>
              <div className="text-sm text-green-800">Total Fields</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-lg font-medium text-purple-600 truncate">
                {formAnalysis.metadata.domain}
              </div>
              <div className="text-sm text-purple-800">Domain</div>
            </div>
          </div>

          {formAnalysis.forms.map((form, formIndex) => (
            <div key={formIndex} className="border rounded-lg p-4 mb-4 last:mb-0">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-900">Form {formIndex + 1}</h4>
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>Method: {form.method}</span>
                  <span>Fields: {form.fields.length}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {form.fields.map((field, fieldIndex) => (
                  <div key={fieldIndex} className="bg-gray-50 p-3 rounded border">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-sm text-gray-900">
                        {field.label || field.name || field.id || 'Unnamed Field'}
                      </span>
                      <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                        {field.purpose}
                      </span>
                    </div>
                    <div className="text-xs text-gray-600 space-y-1">
                      <div>Type: {field.input_type}</div>
                      {field.placeholder && <div>Placeholder: {field.placeholder}</div>}
                      {field.required && <div className="text-red-600">Required</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Autofill Results */}
      {autofillResult && (
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Autofill Results</h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {Object.keys(autofillResult.confidence_scores).length}
              </div>
              <div className="text-sm text-green-800">Fields Filled</div>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">
                {autofillResult.missing_fields.length}
              </div>
              <div className="text-sm text-yellow-800">Missing Fields</div>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {Math.round(
                  Object.values(autofillResult.confidence_scores).reduce((a, b) => a + b, 0) /
                  Object.values(autofillResult.confidence_scores).length * 100
                ) || 0}%
              </div>
              <div className="text-sm text-blue-800">Avg Confidence</div>
            </div>
          </div>

          {/* Filled Fields */}
          {Object.keys(autofillResult.autofill_data).map((formKey) => (
            <div key={formKey} className="border rounded-lg p-4 mb-4">
              <h4 className="font-medium text-gray-900 mb-3 capitalize">
                {formKey.replace('_', ' ')} - Filled Fields
              </h4>
              <div className="space-y-3">
                {Object.entries(autofillResult.autofill_data[formKey]).map(([selector, value]) => {
                  const confidence = autofillResult.confidence_scores[selector] || 0
                  const source = autofillResult.field_mapping[selector] || 'Unknown'
                  
                  return (
                    <div key={selector} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <div className="flex-1">
                        <div className="font-medium text-sm text-gray-900">{selector}</div>
                        <div className="text-gray-700">{value}</div>
                        <div className="text-xs text-gray-500">Source: {source}</div>
                      </div>
                      <div className="text-right">
                        <span className={`text-xs px-2 py-1 rounded ${getConfidenceBadge(confidence)}`}>
                          {Math.round(confidence * 100)}%
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}

          {/* Missing Fields */}
          {autofillResult.missing_fields.length > 0 && (
            <div className="border border-yellow-200 rounded-lg p-4 bg-yellow-50">
              <h4 className="font-medium text-yellow-900 mb-3">Missing Fields</h4>
              <div className="flex flex-wrap gap-2">
                {autofillResult.missing_fields.map((field, index) => (
                  <span
                    key={index}
                    className="text-xs bg-yellow-200 text-yellow-800 px-2 py-1 rounded"
                  >
                    {field}
                  </span>
                ))}
              </div>
              <p className="text-sm text-yellow-700 mt-3">
                These fields couldn't be filled automatically. You may need to upload more documents 
                or fill these fields manually.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Field Matching Results */}
      {Object.keys(matchedFields).length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-4">
            Field Matching Results (Overall Confidence: {(confidence * 100).toFixed(1)}%)
          </h3>
          <div className="space-y-3">
            {Object.entries(matchedFields).map(([fieldName, match]: [string, any]) => (
              <div key={fieldName} className="p-4 border border-gray-200 rounded-lg">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-medium">{fieldName}</h4>
                  <span className={`px-2 py-1 rounded text-xs ${
                    match.matched && match.confidence > 0.7
                      ? 'bg-green-100 text-green-800'
                      : match.matched && match.confidence > 0.3
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {match.matched ? `${(match.confidence * 100).toFixed(0)}%` : 'No Match'}
                  </span>
                </div>
                {match.matched && (
                  <>
                    <p className="text-blue-600 font-medium">{match.value}</p>
                    <p className="text-gray-500 text-sm">Source: {match.source || 'Unknown'}</p>
                    <p className="text-gray-400 text-xs">Type: {match.field_type}</p>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Autofill Data Display */}
      {autofillData && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-4">Form Analysis Results</h3>
          <div className="bg-gray-50 p-4 rounded-lg">
            <pre className="text-sm overflow-auto">
              {JSON.stringify(autofillData, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-600">{error}</p>
        </div>
      )}
    </div>
  )
}

export default WebFormAutofill 