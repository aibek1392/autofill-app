#!/usr/bin/env python3
"""
Setup database tables for the application
"""

import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.supabase_client import SupabaseClient

async def setup_database():
    print("🗄️  Setting up database tables")
    print("=" * 60)
    
    supabase = SupabaseClient()
    
    try:
        # Check what tables exist
        print("🔍 Checking existing tables...")
        
        # Try to get table information
        try:
            # List all tables in the public schema
            result = supabase.client.rpc('get_tables').execute()
            print(f"Tables found: {result.data}")
        except:
            print("Could not list tables via RPC, trying direct queries...")
        
        # Create users table
        print("\n🔧 Creating users table...")
        create_users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        try:
            supabase.client.rpc('exec_sql', {'sql': create_users_sql}).execute()
            print("✅ Users table created")
        except Exception as e:
            print(f"❌ Could not create users table via RPC: {e}")
            print("   You may need to create it manually in the Supabase SQL editor:")
            print(create_users_sql)
        
        # Create uploaded_documents table if it doesn't exist
        print("\n🔧 Creating uploaded_documents table...")
        create_documents_sql = """
        CREATE TABLE IF NOT EXISTS uploaded_documents (
            id SERIAL PRIMARY KEY,
            doc_id UUID UNIQUE,
            user_id UUID REFERENCES users(id),
            filename TEXT NOT NULL,
            type TEXT NOT NULL,
            file_size INTEGER,
            processing_status TEXT DEFAULT 'uploaded',
            uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            processed_at TIMESTAMP WITH TIME ZONE
        );
        """
        
        try:
            supabase.client.rpc('exec_sql', {'sql': create_documents_sql}).execute()
            print("✅ Uploaded documents table created")
        except Exception as e:
            print(f"❌ Could not create documents table via RPC: {e}")
            print("   You may need to create it manually in the Supabase SQL editor:")
            print(create_documents_sql)
        
        # Create vector_chunks table if it doesn't exist
        print("\n🔧 Creating vector_chunks table...")
        create_chunks_sql = """
        CREATE TABLE IF NOT EXISTS vector_chunks (
            id SERIAL PRIMARY KEY,
            chunk_id TEXT UNIQUE NOT NULL,
            doc_id UUID REFERENCES uploaded_documents(doc_id),
            user_id UUID REFERENCES users(id),
            text TEXT NOT NULL,
            chunk_index INTEGER,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        try:
            supabase.client.rpc('exec_sql', {'sql': create_chunks_sql}).execute()
            print("✅ Vector chunks table created")
        except Exception as e:
            print(f"❌ Could not create chunks table via RPC: {e}")
            print("   You may need to create it manually in the Supabase SQL editor:")
            print(create_chunks_sql)
        
        # Create filled_forms table if it doesn't exist
        print("\n🔧 Creating filled_forms table...")
        create_forms_sql = """
        CREATE TABLE IF NOT EXISTS filled_forms (
            id SERIAL PRIMARY KEY,
            user_id UUID REFERENCES users(id),
            original_form_name TEXT NOT NULL,
            filled_form_url TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        try:
            supabase.client.rpc('exec_sql', {'sql': create_forms_sql}).execute()
            print("✅ Filled forms table created")
        except Exception as e:
            print(f"❌ Could not create forms table via RPC: {e}")
            print("   You may need to create it manually in the Supabase SQL editor:")
            print(create_forms_sql)
        
        print("\n🎉 Database setup completed!")
        print("If any tables failed to create via RPC, please run the SQL manually in the Supabase SQL editor.")
        
    except Exception as e:
        print(f"❌ Error during database setup: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(setup_database()) 