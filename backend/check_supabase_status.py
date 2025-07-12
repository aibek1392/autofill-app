#!/usr/bin/env python3
"""
Check current status of all tables in Supabase database
"""
import asyncio
from database.supabase_client import supabase_client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_supabase_status():
    """Check the current status of all Supabase tables"""
    
    if not supabase_client.has_supabase_credentials:
        print("❌ Supabase not available")
        return
    
    print("🔍 Checking Supabase database status...")
    print("=" * 50)
    
    try:
        # Use admin client for checking all data
        client = supabase_client.admin_client if supabase_client.admin_client else supabase_client.client
        
        # Check uploaded_documents table
        print("\n📄 UPLOADED_DOCUMENTS TABLE:")
        try:
            docs_result = client.table('uploaded_documents').select('*').execute()
            if docs_result.data:
                print(f"   📊 Count: {len(docs_result.data)}")
                for doc in docs_result.data:
                    print(f"   📋 {doc.get('filename', 'Unknown')} - User: {doc.get('user_id', 'Unknown')[:8]}... - Status: {doc.get('processing_status', 'Unknown')}")
            else:
                print("   ✅ Empty (0 documents)")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        # Check document_chunks table
        print("\n🧩 VECTOR_CHUNKS TABLE:")
        try:
            chunks_result = client.table('vector_chunks').select('*').execute()
            if chunks_result.data:
                print(f"   📊 Count: {len(chunks_result.data)}")
                # Group by document
                doc_chunks = {}
                for chunk in chunks_result.data:
                    doc_id = chunk.get('doc_id', 'Unknown')
                    if doc_id not in doc_chunks:
                        doc_chunks[doc_id] = 0
                    doc_chunks[doc_id] += 1
                
                for doc_id, count in doc_chunks.items():
                    print(f"   📋 Doc {doc_id[:8]}...: {count} chunks")
            else:
                print("   ✅ Empty (0 chunks)")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        # Check filled_forms table
        print("\n📝 FILLED_FORMS TABLE:")
        try:
            forms_result = client.table('filled_forms').select('*').execute()
            if forms_result.data:
                print(f"   📊 Count: {len(forms_result.data)}")
                for form in forms_result.data:
                    print(f"   📋 {form.get('original_form_name', 'Unknown')} - User: {form.get('user_id', 'Unknown')[:8]}...")
            else:
                print("   ✅ Empty (0 forms)")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        # Check auth.users (if accessible)
        print("\n👤 AUTH.USERS TABLE:")
        try:
            # Try to get user count using a simple query
            users_result = client.auth.admin.list_users()
            if hasattr(users_result, 'users') and users_result.users:
                print(f"   📊 Count: {len(users_result.users)}")
                for user in users_result.users:
                    print(f"   👤 {user.email} - ID: {user.id[:8]}... - Created: {user.created_at}")
            else:
                print("   ✅ Empty (0 users)")
        except Exception as e:
            print(f"   ❌ Error checking users: {str(e)}")
            # Alternative approach - try to query a user-specific table
            try:
                # If we can't access auth.users directly, we can infer from documents
                all_docs = client.table('uploaded_documents').select('user_id').execute()
                if all_docs.data:
                    unique_users = set(doc['user_id'] for doc in all_docs.data)
                    print(f"   📊 Inferred from documents: {len(unique_users)} unique user IDs")
                    for user_id in unique_users:
                        print(f"   👤 User ID: {user_id[:8]}...")
                else:
                    print("   ✅ No user data found in documents")
            except Exception as e2:
                print(f"   ❌ Could not infer user data: {str(e2)}")
        
        print("\n" + "=" * 50)
        print("✅ Supabase status check complete!")
        
    except Exception as e:
        print(f"❌ Failed to check Supabase status: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_supabase_status()) 