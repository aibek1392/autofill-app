#!/usr/bin/env python3
"""
List all documents for the user and their chunking information
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.supabase_client import supabase_client
from database.pinecone_client import pinecone_client

async def list_user_docs():
    print("📋 Listing all documents for user")
    print("=" * 60)
    
    user_id = "18e3f9bf-3a9b-4994-90cd-8cc9b08dcedf"
    
    # Get all user documents
    docs = await supabase_client.get_user_documents(user_id)
    print(f"Found {len(docs)} documents:")
    
    for i, doc in enumerate(docs):
        print(f"\n--- Document {i+1} ---")
        print(f"Doc ID: {doc['doc_id']}")
        print(f"Filename: {doc['filename']}")
        print(f"Type: {doc['type']}")
        print(f"Status: {doc['processing_status']}")
        
        # Get chunks for this document
        chunks = await supabase_client.get_document_chunks(doc['doc_id'])
        print(f"Chunks in Supabase: {len(chunks)}")
        
        # Get vectors in Pinecone for this document
        try:
            results = pinecone_client.index.query(
                vector=[0] * 1536,
                filter={'doc_id': doc['doc_id']},
                top_k=1000,
                include_metadata=True,
                include_values=False
            )
            print(f"Vectors in Pinecone: {len(results.matches)}")
            
            # Show first few chunks
            for j, match in enumerate(results.matches[:3]):
                meta = match.metadata
                text = meta.get('text', '')[:200] + "..." if len(meta.get('text', '')) > 200 else meta.get('text', '')
                print(f"  Chunk {j+1}: {text}")
                
        except Exception as e:
            print(f"Error querying Pinecone: {e}")

if __name__ == "__main__":
    asyncio.run(list_user_docs()) 