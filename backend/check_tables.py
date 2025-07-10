#!/usr/bin/env python3
"""
Check what tables exist in the Supabase database
"""

import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.supabase_client import SupabaseClient

async def check_tables():
    print("🔍 Checking existing tables in Supabase")
    print("=" * 60)
    
    supabase = SupabaseClient()
    
    try:
        # Try different table names and schemas
        possible_tables = [
            'users',
            'public.users',
            'auth.users',
            'uploaded_documents',
            'public.uploaded_documents',
            'vector_chunks',
            'public.vector_chunks',
            'filled_forms',
            'public.filled_forms'
        ]
        
        for table_name in possible_tables:
            try:
                print(f"🔍 Checking table: {table_name}")
                result = supabase.client.table(table_name).select('*').limit(1).execute()
                print(f"✅ Table exists: {table_name}")
                print(f"   Columns: {list(result.data[0].keys()) if result.data else 'No data'}")
            except Exception as e:
                print(f"❌ Table does not exist: {table_name}")
        
        # Try to get table list via RPC
        print("\n🔍 Trying to get table list via RPC...")
        try:
            result = supabase.client.rpc('get_schema_tables').execute()
            print(f"Tables via RPC: {result.data}")
        except Exception as e:
            print(f"RPC failed: {e}")
        
        print("\n💡 If no tables are found, you may need to:")
        print("1. Check your Supabase dashboard for the correct table names")
        print("2. Create the tables manually in the SQL editor")
        print("3. Check if you're using a different schema (e.g., 'auth' instead of 'public')")
        
    except Exception as e:
        print(f"❌ Error checking tables: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_tables()) 