#!/usr/bin/env python3
"""
Delete all PDF documents from Supabase and Pinecone
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.supabase_client import SupabaseClient
from database.pinecone_client import PineconeClient

async def delete_all_pdfs():
    print("🗑️  Deleting all PDF documents from databases")
    print("=" * 60)
    
    supabase = SupabaseClient()
    pinecone = PineconeClient()
    
    try:
        # Step 1: Get all documents from Supabase
        print("🔍 Step 1: Getting all documents from Supabase...")
        all_documents = await supabase.get_user_documents("18e3f9bf-3a9b-4994-90cd-8cc9b08dcedf")
        
        pdf_documents = [doc for doc in all_documents if doc.get('type') == 'application/pdf']
        print(f"📊 Found {len(pdf_documents)} PDF documents:")
        
        for doc in pdf_documents:
            print(f"   - {doc.get('filename', 'Unknown')} (ID: {doc.get('doc_id', 'No ID')})")
        
        if not pdf_documents:
            print("✅ No PDF documents found in Supabase")
            return
        
        # Step 2: Delete from Pinecone
        print(f"\n🔍 Step 2: Deleting vectors from Pinecone...")
        for doc in pdf_documents:
            doc_id = doc.get('doc_id')
            if doc_id:
                try:
                    await pinecone.delete_document_vectors(doc_id)
                    print(f"   ✅ Deleted vectors for document: {doc.get('filename', 'Unknown')}")
                except Exception as e:
                    print(f"   ❌ Failed to delete vectors for {doc.get('filename', 'Unknown')}: {e}")
        
        # Step 3: Delete from Supabase
        print(f"\n🔍 Step 3: Deleting documents from Supabase...")
        for doc in pdf_documents:
            doc_id = doc.get('doc_id')
            if doc_id:
                try:
                    # Delete chunks first
                    chunks = await supabase.get_document_chunks(doc_id)
                    print(f"   📄 Found {len(chunks)} chunks for {doc.get('filename', 'Unknown')}")
                    
                    # Delete chunks
                    await supabase.delete_document_chunks(doc_id)
                    print(f"   ✅ Deleted chunks for: {doc.get('filename', 'Unknown')}")
                    
                    # Delete document record
                    result = supabase.client.table('uploaded_documents').delete().eq('doc_id', doc_id).execute()
                    print(f"   ✅ Deleted document record: {doc.get('filename', 'Unknown')}")
                    
                except Exception as e:
                    print(f"   ❌ Failed to delete document {doc.get('filename', 'Unknown')}: {e}")
        
        print(f"\n🎉 Cleanup complete!")
        print(f"   - Deleted {len(pdf_documents)} PDF documents from Supabase")
        print(f"   - Deleted corresponding vectors from Pinecone")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(delete_all_pdfs()) 