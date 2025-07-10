#!/usr/bin/env python3
"""
Insert a test user into the Supabase 'users' table
"""

import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.supabase_client import SupabaseClient

async def insert_test_user():
    print("👤 Inserting test user into Supabase 'users' table")
    print("=" * 60)
    
    supabase = SupabaseClient()
    user_id = "18e3f9bf-3a9b-4994-90cd-8cc9b08dcedf"
    email = "testuser@example.com"
    name = "Test User"
    
    try:
        # Insert user record
        result = supabase.client.table('users').insert({
            'id': user_id,
            'email': email,
            'name': name
        }).execute()
        print(f"✅ Inserted user: {user_id} ({email})")
        print(f"Result: {result.data}")
    except Exception as e:
        print(f"❌ Error inserting user: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(insert_test_user()) 