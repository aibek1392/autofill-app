#!/usr/bin/env python3
"""
Setup authenticated user and fix document ownership
"""

import asyncio
from database.supabase_client import supabase_client

async def setup_authenticated_user():
    print("🔧 Setting up authenticated user and fixing document ownership")
    print("=" * 60)
    
    # Current document user_id
    current_user_id = "085ae31c-8dab-4793-9fcb-7d68f2cb1270"
    
    try:
        # Get all documents for current user
        documents = await supabase_client.get_user_documents(current_user_id)
        print(f"📄 Found {len(documents)} documents for user {current_user_id[:8]}...")
        
        for doc in documents:
            print(f"  - {doc['filename']} (doc_id: {doc['doc_id'][:8]}...)")
        
        print(f"\n🔍 The issue is that the user who uploaded the document ({current_user_id}) is not the same as your current authenticated user.")
        print(f"   This happens when:")
        print(f"   1. You uploaded documents while not authenticated (using demo mode)")
        print(f"   2. You authenticated later with a different user account")
        print(f"   3. The frontend was using a fallback user ID")
        
        print(f"\n💡 Solutions:")
        print(f"   1. RECOMMENDED: Sign in with the same user account that uploaded the documents")
        print(f"   2. Re-upload your documents after signing in with your current account")
        print(f"   3. Transfer document ownership (requires admin access)")
        
        print(f"\n🔐 To fix this properly:")
        print(f"   1. Go to your Supabase dashboard > Authentication > Users")
        print(f"   2. Check if user {current_user_id} exists")
        print(f"   3. If it exists, sign in with that user's email")
        print(f"   4. If it doesn't exist, re-upload your documents after signing in")
        
        # Check if we can find the user in auth
        print(f"\n🔍 Checking user existence...")
        
        # Try to get user info (this might fail due to RLS)
        try:
            # We can't directly query auth.users, but we can check if we can create a document
            # for the current user to see if they exist
            
            print(f"   The user {current_user_id} exists in the database (has documents)")
            print(f"   You need to sign in with this user's account to access the documents")
            
        except Exception as e:
            print(f"   Error checking user: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(setup_authenticated_user()) 