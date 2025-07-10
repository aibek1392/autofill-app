#!/usr/bin/env python3
"""
Delete ALL vectors from Pinecone - complete cleanup
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.pinecone_client import PineconeClient

async def delete_all_vectors():
    print("🗑️  Deleting ALL vectors from Pinecone")
    print("=" * 60)
    
    pinecone = PineconeClient()
    
    try:
        # Get current stats
        print("📊 Getting current Pinecone statistics...")
        stats = await pinecone.get_index_stats()
        total_vectors = stats.get('total_vector_count', 0)
        print(f"   Total vectors: {total_vectors}")
        
        if total_vectors == 0:
            print("✅ Pinecone is already clean!")
            return
        
        # Confirm deletion
        print(f"\n⚠️  WARNING: This will delete ALL {total_vectors} vectors from Pinecone!")
        print("   This action cannot be undone.")
        
        # For safety, let's delete in batches by getting all vector IDs first
        print(f"\n🔍 Getting all vector IDs...")
        
        # Use a dummy vector to search for all vectors (no filter)
        dummy_vector = [0.0] * 1536  # 1536-dimensional zero vector
        
        # Search with a very large top_k to get all vectors
        results = pinecone.index.query(
            vector=dummy_vector,
            top_k=10000,  # Large number to get all vectors
            include_metadata=False,
            include_values=False
        )
        
        vector_ids = [match.id for match in results.matches]
        print(f"📄 Found {len(vector_ids)} vectors to delete")
        
        if len(vector_ids) < total_vectors:
            print(f"⚠️  Warning: Found {len(vector_ids)} vectors but total count is {total_vectors}")
            print("   Some vectors may not be deleted in this batch.")
        
        if not vector_ids:
            print("✅ No vectors found to delete!")
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
        remaining_vectors = final_stats.get('total_vector_count', 0)
        print(f"   Remaining vectors: {remaining_vectors}")
        
        if remaining_vectors == 0:
            print(f"\n🎉 Complete cleanup successful!")
            print(f"   - Deleted {deleted_count} vectors from Pinecone")
            print(f"   - Pinecone is now completely clean")
        else:
            print(f"\n⚠️  Partial cleanup completed")
            print(f"   - Deleted {deleted_count} vectors from Pinecone")
            print(f"   - {remaining_vectors} vectors still remain")
            print(f"   - You may need to run this script again or manually clean up")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(delete_all_vectors()) 