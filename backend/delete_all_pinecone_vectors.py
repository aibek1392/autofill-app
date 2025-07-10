#!/usr/bin/env python3
"""
Delete all vectors from Pinecone for a specific user
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.pinecone_client import PineconeClient

async def delete_all_pinecone_vectors():
    print("🗑️  Deleting all vectors from Pinecone")
    print("=" * 60)
    
    user_id = "18e3f9bf-3a9b-4994-90cd-8cc9b08dcedf"
    pinecone = PineconeClient()
    
    try:
        # Get current stats
        print("📊 Getting current Pinecone statistics...")
        stats = await pinecone.get_index_stats()
        print(f"   Total vectors: {stats.get('total_vector_count', 0)}")
        
        if stats.get('total_vector_count', 0) == 0:
            print("✅ Pinecone is already clean!")
            return
        
        # Search for all vectors for this user
        print(f"\n🔍 Searching for vectors for user: {user_id}")
        
        # Use a dummy vector to search for all vectors for this user
        dummy_vector = [0.0] * 1536  # 1536-dimensional zero vector
        
        # Search with a large top_k to get all vectors
        results = pinecone.index.query(
            vector=dummy_vector,
            filter={'user_id': user_id},
            top_k=10000,  # Large number to get all vectors
            include_metadata=False,
            include_values=False
        )
        
        vector_ids = [match.id for match in results.matches]
        print(f"📄 Found {len(vector_ids)} vectors for user {user_id}")
        
        if not vector_ids:
            print("✅ No vectors found for this user!")
            return
        
        # Delete vectors in batches
        print(f"\n🗑️  Deleting {len(vector_ids)} vectors...")
        batch_size = 100
        deleted_count = 0
        
        for i in range(0, len(vector_ids), batch_size):
            batch = vector_ids[i:i + batch_size]
            pinecone.index.delete(ids=batch)
            deleted_count += len(batch)
            print(f"   ✅ Deleted batch {i//batch_size + 1}: {len(batch)} vectors")
        
        # Verify deletion
        print(f"\n🔍 Verifying deletion...")
        final_stats = await pinecone.get_index_stats()
        print(f"   Remaining vectors: {final_stats.get('total_vector_count', 0)}")
        
        print(f"\n🎉 Cleanup complete!")
        print(f"   - Deleted {deleted_count} vectors from Pinecone")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(delete_all_pinecone_vectors()) 