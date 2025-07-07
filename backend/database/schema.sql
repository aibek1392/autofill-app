-- AI Autofill Form App Database Schema
-- This file contains the SQL commands to create tables in Supabase

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (Supabase Auth handles this, but we can add custom fields)
-- This table will be automatically created by Supabase Auth
-- We can add custom user fields here if needed

-- Documents uploaded by users
CREATE TABLE uploaded_documents (
    doc_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL, -- MIME type
    file_size INTEGER NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vector chunks from processed documents
CREATE TABLE vector_chunks (
    chunk_id VARCHAR(255) PRIMARY KEY,
    doc_id UUID REFERENCES uploaded_documents(doc_id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Filled forms history
CREATE TABLE filled_forms (
    form_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    original_form_name VARCHAR(255) NOT NULL,
    filled_form_url VARCHAR(500) NOT NULL,
    filled_fields JSONB DEFAULT '{}',
    missing_fields JSONB DEFAULT '[]',
    confidence_scores JSONB DEFAULT '{}',
    processing_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat sessions (optional, for tracking conversations)
CREATE TABLE chat_sessions (
    session_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    session_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat messages (optional, for storing chat history)
CREATE TABLE chat_messages (
    message_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    response TEXT,
    sources JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX idx_uploaded_documents_user_id ON uploaded_documents(user_id);
CREATE INDEX idx_uploaded_documents_status ON uploaded_documents(processing_status);
CREATE INDEX idx_vector_chunks_user_id ON vector_chunks(user_id);
CREATE INDEX idx_vector_chunks_doc_id ON vector_chunks(doc_id);
CREATE INDEX idx_filled_forms_user_id ON filled_forms(user_id);
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_user_id ON chat_messages(user_id);

-- Row Level Security (RLS) policies
ALTER TABLE uploaded_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE vector_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE filled_forms ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- RLS policies for uploaded_documents
CREATE POLICY "Users can view their own documents" ON uploaded_documents
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own documents" ON uploaded_documents
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own documents" ON uploaded_documents
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own documents" ON uploaded_documents
    FOR DELETE USING (auth.uid() = user_id);

-- RLS policies for vector_chunks
CREATE POLICY "Users can view their own chunks" ON vector_chunks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own chunks" ON vector_chunks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own chunks" ON vector_chunks
    FOR DELETE USING (auth.uid() = user_id);

-- RLS policies for filled_forms
CREATE POLICY "Users can view their own filled forms" ON filled_forms
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own filled forms" ON filled_forms
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own filled forms" ON filled_forms
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own filled forms" ON filled_forms
    FOR DELETE USING (auth.uid() = user_id);

-- RLS policies for chat_sessions
CREATE POLICY "Users can view their own chat sessions" ON chat_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own chat sessions" ON chat_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own chat sessions" ON chat_sessions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own chat sessions" ON chat_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- RLS policies for chat_messages
CREATE POLICY "Users can view their own messages" ON chat_messages
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own messages" ON chat_messages
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Functions for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at timestamps
CREATE TRIGGER update_uploaded_documents_updated_at BEFORE UPDATE ON uploaded_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_filled_forms_updated_at BEFORE UPDATE ON filled_forms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Storage bucket for file uploads (if using Supabase storage)
INSERT INTO storage.buckets (id, name, public) VALUES ('documents', 'documents', false);
INSERT INTO storage.buckets (id, name, public) VALUES ('forms', 'forms', false);
INSERT INTO storage.buckets (id, name, public) VALUES ('filled-forms', 'filled-forms', false);

-- Storage policies
CREATE POLICY "Users can upload their own documents" ON storage.objects
    FOR INSERT WITH CHECK (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can view their own documents" ON storage.objects
    FOR SELECT USING (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can delete their own documents" ON storage.objects
    FOR DELETE USING (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Similar policies for forms and filled-forms buckets
CREATE POLICY "Users can upload their own forms" ON storage.objects
    FOR INSERT WITH CHECK (bucket_id = 'forms' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can view their own forms" ON storage.objects
    FOR SELECT USING (bucket_id = 'forms' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can upload filled forms" ON storage.objects
    FOR INSERT WITH CHECK (bucket_id = 'filled-forms' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can view their filled forms" ON storage.objects
    FOR SELECT USING (bucket_id = 'filled-forms' AND auth.uid()::text = (storage.foldername(name))[1]); 