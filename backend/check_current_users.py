#!/usr/bin/env python3
"""
Check what users currently exist in Supabase auth
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.supabase_client import supabase_client

async def check_current_users():
    print("👥 Checking Current Users in Supabase Auth")
    print("=" * 60)
    
    try:
        if not supabase_client.has_supabase_credentials:
            print("❌ Supabase not connected!")
            return
        
        # Try to get users from auth.users (this requires service role key)
        print("🔍 Attempting to list users...")
        
        try:
            # This might not work depending on RLS policies
            result = supabase_client.client.auth.admin.list_users()
            
            if result.users:
                print(f"✅ Found {len(result.users)} users:")
                for user in result.users:
                    print(f"   - ID: {user.id}")
                    print(f"     Email: {user.email}")
                    print(f"     Created: {user.created_at}")
                    print(f"     Confirmed: {user.email_confirmed_at is not None}")
                    print()
            else:
                print("❌ No users found in auth system")
                
        except Exception as e:
            print(f"❌ Could not list users directly: {e}")
            print("💡 This is normal if you don't have admin permissions")
            
            # Alternative: try to get user count from a different approach
            print("\n🔍 Trying alternative approach...")
            try:
                # Check if we can query any tables that might have user references
                docs_result = supabase_client.client.table('uploaded_documents').select('user_id').execute()
                chunks_result = supabase_client.client.table('vector_chunks').select('user_id').execute()
                
                all_user_ids = set()
                if docs_result.data:
                    all_user_ids.update([doc['user_id'] for doc in docs_result.data if doc['user_id']])
                if chunks_result.data:
                    all_user_ids.update([chunk['user_id'] for chunk in chunks_result.data if chunk['user_id']])
                
                if all_user_ids:
                    print(f"✅ Found {len(all_user_ids)} unique user IDs in database:")
                    for user_id in all_user_ids:
                        print(f"   - {user_id}")
                else:
                    print("❌ No user IDs found in database tables")
                    
            except Exception as e2:
                print(f"❌ Alternative approach failed: {e2}")
        
        print(f"\n💡 To fix the upload issue:")
        print(f"   1. Sign up again at: https://autofill-app-henna.vercel.app")
        print(f"   2. Upload a document")
        print(f"   3. Check browser console for the actual user ID being used")
        print(f"   4. Update the debug script with the correct user ID")
        
    except Exception as e:
        print(f"❌ Error checking users: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_current_users()) 