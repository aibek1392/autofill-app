import { createClient } from '@supabase/supabase-js'

// Use fallback values for development if environment variables are not set
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY || 'placeholder-key'

// Create client with fallback values to prevent build errors
export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Log status for debugging
if (process.env.NODE_ENV === 'development') {
  const hasRealCredentials = process.env.REACT_APP_SUPABASE_URL && process.env.REACT_APP_SUPABASE_ANON_KEY
  console.warn(
    hasRealCredentials 
      ? 'Supabase client initialized successfully' 
      : 'Supabase client initialized with placeholder values - add REACT_APP_SUPABASE_URL and REACT_APP_SUPABASE_ANON_KEY to frontend/.env file'
  )
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