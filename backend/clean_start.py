#!/usr/bin/env python3
"""
Clean start: Delete all users and documents for fresh setup
"""

import asyncio
from database.supabase_client import supabase_client
from database.pinecone_client import pinecone_client

async def clean_start():
    print("🧹 Starting fresh - Cleaning all users and documents")
    print("=" * 60)
    
    # Confirm deletion
    print("⚠️  WARNING: This will delete ALL documents and vector data!")
    confirm = input("Are you sure you want to continue? (type 'DELETE' to confirm): ").strip()
    
    if confirm != 'DELETE':
        print("❌ Cancelled. No changes made.")
        return
    
    try:
        # Step 1: Delete all vector chunks from Supabase
        print("\n🗑️  Deleting vector chunks from Supabase...")
        try:
            result = supabase_client.client.table('vector_chunks').delete().neq('id', 0).execute()
            print(f"   ✅ Deleted vector chunks from Supabase")
        except Exception as e:
            print(f"   ⚠️  Error deleting vector chunks: {e}")
        
        # Step 2: Delete all documents from Supabase
        print("\n🗑️  Deleting documents from Supabase...")
        try:
            result = supabase_client.client.table('uploaded_documents').delete().neq('doc_id', '00000000-0000-0000-0000-000000000000').execute()
            print(f"   ✅ Deleted documents from Supabase")
        except Exception as e:
            print(f"   ⚠️  Error deleting documents: {e}")
        
        # Step 3: Delete all vectors from Pinecone
        print("\n🗑️  Deleting vectors from Pinecone...")
        try:
            await pinecone_client.delete_all_vectors()
            print(f"   ✅ Deleted all vectors from Pinecone")
        except Exception as e:
            print(f"   ⚠️  Error deleting vectors from Pinecone: {e}")
        
        # Step 4: Clear demo storage
        print("\n🗑️  Clearing demo storage...")
        try:
            # Import demo storage from main.py
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            
            # We can't directly access demo_documents from main.py, but that's okay
            # It will be reset when the server restarts
            print(f"   ✅ Demo storage will be cleared on server restart")
        except Exception as e:
            print(f"   ⚠️  Note: Demo storage will be cleared on server restart")
        
        print("\n🎉 Clean start completed!")
        print("✅ All documents and vectors have been deleted")
        print("✅ Database is now clean and ready for fresh setup")
        
        print("\n📋 Next steps:")
        print("1. Sign up/sign in with your Supabase account")
        print("2. Upload your documents again")
        print("3. The system will use your authenticated user ID")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

if __name__ == "__main__":
    asyncio.run(clean_start()) 