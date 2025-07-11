import { createClient } from '@supabase/supabase-js'

// Use fallback values for development if environment variables are not set
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY || 'placeholder-key'

// Check if we have real credentials
const hasRealCredentials = supabaseUrl !== 'https://placeholder.supabase.co' && supabaseAnonKey !== 'placeholder-key'

// Create client with fallback values to prevent build errors
export const supabase = hasRealCredentials ? createClient(supabaseUrl, supabaseAnonKey) : null

// Log status for debugging
if (process.env.NODE_ENV === 'development') {
  console.log('=== Supabase Client Debug ===')
  console.log('REACT_APP_SUPABASE_URL:', process.env.REACT_APP_SUPABASE_URL || 'NOT SET')
  console.log('REACT_APP_SUPABASE_ANON_KEY:', process.env.REACT_APP_SUPABASE_ANON_KEY ? 'SET' : 'NOT SET')
  console.log('Has real credentials:', hasRealCredentials)
  console.log('Supabase client created:', !!supabase)
  
  if (hasRealCredentials) {
    console.log('✅ Supabase client initialized successfully')
  } else {
    console.warn('❌ Supabase client NOT initialized - using placeholder values')
    console.warn('Add REACT_APP_SUPABASE_URL and REACT_APP_SUPABASE_ANON_KEY to frontend/.env file')
  }
}

// Make supabase available on window for debugging (development only)
if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
  (window as any).supabase = supabase
  console.log('Supabase client attached to window.supabase for debugging')
}

export type Database = {
  public: {
    Tables: {
      uploaded_documents: {
        Row: {
          doc_id: string
          user_id: string
          filename: string
          type: string
          file_size: number
          uploaded_at: string
          processed_at: string | null
          processing_status: string
          metadata: Record<string, any>
          created_at: string
          updated_at: string
        }
        Insert: {
          doc_id?: string
          user_id: string
          filename: string
          type: string
          file_size: number
          uploaded_at?: string
          processed_at?: string | null
          processing_status?: string
          metadata?: Record<string, any>
          created_at?: string
          updated_at?: string
        }
        Update: {
          doc_id?: string
          user_id?: string
          filename?: string
          type?: string
          file_size?: number
          uploaded_at?: string
          processed_at?: string | null
          processing_status?: string
          metadata?: Record<string, any>
          created_at?: string
          updated_at?: string
        }
      }
      filled_forms: {
        Row: {
          form_id: string
          user_id: string
          original_form_name: string
          filled_form_url: string
          filled_fields: Record<string, any>
          missing_fields: string[]
          confidence_scores: Record<string, any>
          processing_metadata: Record<string, any>
          created_at: string
          updated_at: string
        }
        Insert: {
          form_id?: string
          user_id: string
          original_form_name: string
          filled_form_url: string
          filled_fields?: Record<string, any>
          missing_fields?: string[]
          confidence_scores?: Record<string, any>
          processing_metadata?: Record<string, any>
          created_at?: string
          updated_at?: string
        }
        Update: {
          form_id?: string
          user_id?: string
          original_form_name?: string
          filled_form_url?: string
          filled_fields?: Record<string, any>
          missing_fields?: string[]
          confidence_scores?: Record<string, any>
          processing_metadata?: Record<string, any>
          created_at?: string
          updated_at?: string
        }
      }
    }
  }
} 