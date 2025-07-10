#!/usr/bin/env python3
"""
Insert test user into existing users table
"""

import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.supabase_client import SupabaseClient

async def insert_user_simple():
    print("👤 Inserting test user into existing users table")
    print("=" * 60)
    
    supabase = SupabaseClient()
    user_id = "18e3f9bf-3a9b-4994-90cd-8cc9b08dcedf"
    email = "testuser@example.com"
    name = "Test User"
    
    try:
        # First check if user already exists
        print("🔍 Checking if user already exists...")
        existing_user = supabase.client.table('users').select('*').eq('id', user_id).execute()
        
        if existing_user.data:
            print(f"✅ User already exists: {existing_user.data[0]}")
            return
        
        # Insert user record
        print("➕ Inserting new user...")
        result = supabase.client.table('users').insert({
            'id': user_id,
            'email': email,
            'name': name
        }).execute()
        
        print(f"✅ Successfully inserted user: {user_id}")
        print(f"Result: {result.data}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 If you're still getting errors, try running this SQL directly in Supabase:")
        print(f"""
        INSERT INTO users (id, email, name)
        VALUES ('{user_id}', '{email}', '{name}')
        ON CONFLICT (id) DO NOTHING;
        """)

if __name__ == "__main__":
    asyncio.run(insert_user_simple()) 