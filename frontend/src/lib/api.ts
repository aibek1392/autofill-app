import axios from 'axios'
import { supabase } from './supabase'

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'

// Helper function to get user ID consistently
const getUserId = async (): Promise<string> => {
  if (supabase) {
    const { data: { user } } = await supabase.auth.getUser()
    return user?.id || '550e8400-e29b-41d4-a716-446655440000'
  }
  return '550e8400-e29b-41d4-a716-446655440000'
}

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for file uploads
})

// Add auth interceptor only if supabase is available
api.interceptors.request.use(async (config) => {
  if (supabase) {
    const { data: { session } } = await supabase.auth.getSession()
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`
    }
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && supabase) {
      // Redirect to login or refresh token
      supabase.auth.signOut()
    }
    return Promise.reject(error)
  }
)

export interface UploadedFile {
  filename: string
  file_id: string
  status: string
  size?: number
  type?: string
}

export interface Document {
  doc_id: string
  filename: string
  type: string
  file_size: number
  uploaded_at: string
  processing_status: string
}

export interface ChatMessage {
  message: string
  user_id: string
}

export interface ChatResponse {
  answer: string
  sources: Array<{
    filename: string
    score: number
  }>
  context_used: number
}

export interface FormFillResult {
  filled_form_path: string
  filled_form_url: string
  original_form_name: string
  filled_fields: Record<string, string>
  missing_fields: string[]
  confidence_scores: Record<string, number>
  field_mapping: Record<string, string>
  user_id: string
  processing_status: string
}

export interface UserStats {
  total_documents: number
  total_filled_forms: number
  recent_documents: Document[]
  recent_filled_forms: any[]
}

// API functions
export const uploadDocuments = async (files: FileList | File[]): Promise<{ files: UploadedFile[], total: number }> => {
  const formData = new FormData()
  
  // Handle both FileList and File array
  const fileArray = Array.isArray(files) ? files : Array.from(files)
  
  fileArray.forEach((file, index) => {
    // Validate file before appending
    if (!file || !file.name || file.size === undefined || file.size === null) {
      console.error('Invalid file detected:', file)
      throw new Error(`Invalid file at index ${index}: ${file?.name || 'unnamed file'}`)
    }
    
    console.log(`Validating file ${index}:`, {
      name: file.name,
      size: file.size,
      type: file.type
    })
    
    formData.append('files', file)
  })

  // Get user ID for demo mode
  let userId = '550e8400-e29b-41d4-a716-446655440000'
  if (supabase) {
    const { data: { user } } = await supabase.auth.getUser()
    userId = user?.id || '550e8400-e29b-41d4-a716-446655440000'
  }
  
  console.log('Uploading files:', {
    fileCount: fileArray.length,
    userId: userId,
    fileNames: fileArray.map(f => f.name)
  })
  
  const response = await api.post('/api/upload', formData, {
    headers: {
      // Let axios set Content-Type automatically for multipart/form-data
      'X-User-ID': userId,
    },
  })
  
  console.log('Upload response:', response.data)
  return response.data
}

export const getUserDocuments = async (): Promise<{ documents: Document[] }> => {
  // Get user ID for demo mode
  let userId = '550e8400-e29b-41d4-a716-446655440000'
  if (supabase) {
    const { data: { user } } = await supabase.auth.getUser()
    userId = user?.id || '550e8400-e29b-41d4-a716-446655440000'
  }

  const response = await api.get('/api/documents', {
    headers: {
      'X-User-ID': userId,
    },
  })
  return response.data
}

export const chatWithDocuments = async (message: string): Promise<ChatResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': await getUserId(),
      },
      body: JSON.stringify({
        message,
        user_id: await getUserId(),
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to chat with documents: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error chatting with documents:', error);
    throw error;
  }
};

export const chatWithDocumentsStream = async (
  message: string,
  onChunk: (chunk: any) => void,
  onError?: (error: string) => void,
  onComplete?: () => void
): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': await getUserId(),
      },
      body: JSON.stringify({
        message,
        user_id: await getUserId(),
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to start streaming chat: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body reader available');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          onComplete?.();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              onChunk(data);
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', line, parseError);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  } catch (error) {
    console.error('Error in streaming chat:', error);
    onError?.(error instanceof Error ? error.message : 'Unknown error occurred');
  }
};

export const uploadForm = async (file: File): Promise<FormFillResult> => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post('/api/upload-form', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const getFilledForms = async (): Promise<{ filled_forms: any[] }> => {
  // Get user ID for demo mode
  let userId = '550e8400-e29b-41d4-a716-446655440000'
  if (supabase) {
    const { data: { user } } = await supabase.auth.getUser()
    userId = user?.id || '550e8400-e29b-41d4-a716-446655440000'
  }

  const response = await api.get('/api/filled-forms', {
    headers: {
      'X-User-ID': userId,
    },
  })
  return response.data
}

export const getMissingFieldSuggestions = async (missingFields: string[]): Promise<{ suggestions: Record<string, string> }> => {
  const response = await api.post('/api/missing-field-suggestions', missingFields)
  return response.data
}

export const getUserStats = async (): Promise<UserStats> => {
  // Get user ID for demo mode
  let userId = '550e8400-e29b-41d4-a716-446655440000'
  if (supabase) {
    const { data: { user } } = await supabase.auth.getUser()
    userId = user?.id || '550e8400-e29b-41d4-a716-446655440000'
  }

  const response = await api.get('/api/stats', {
    headers: {
      'X-User-ID': userId,
    },
  })
  return response.data
}

export const downloadFile = async (filename: string): Promise<Blob> => {
  const response = await api.get(`/api/download/${filename}`, {
    responseType: 'blob'
  })
  return response.data
}

export const getHealthStatus = async (): Promise<any> => {
  const response = await api.get('/api/health')
  return response.data
}

export default api 