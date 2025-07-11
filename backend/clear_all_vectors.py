#!/usr/bin/env python3
"""
Clear all vectors from Pinecone index
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.pinecone_client import pinecone_client
import asyncio

async def clear_all_vectors():
    """Delete all vectors from Pinecone index"""
    try:
        print("🧹 Starting Pinecone cleanup...")
        
        # Get current stats
        stats = await pinecone_client.get_index_stats()
        print(f"📊 Current Pinecone stats: {stats}")
        
        if stats.get('total_vector_count', 0) == 0:
            print("✅ Pinecone index is already empty")
            return
        
        # Delete all vectors using the correct API
        print("🗑️  Deleting all vectors from Pinecone...")
        
        # Use the delete_all method from Pinecone
        if pinecone_client.index:
            pinecone_client.index.delete(delete_all=True)
            print("✅ Delete command sent to Pinecone")
        else:
            print("❌ Pinecone index not available")
            return
        
        # Verify deletion (wait a bit for propagation)
        print("🔍 Waiting for deletion to propagate...")
        await asyncio.sleep(5)  # Wait for deletion to propagate
        
        final_stats = await pinecone_client.get_index_stats()
        print(f"📊 Final Pinecone stats: {final_stats}")
        
        if final_stats.get('total_vector_count', 0) == 0:
            print("✅ All vectors deleted successfully from Pinecone!")
        else:
            print(f"⚠️  Warning: {final_stats.get('total_vector_count', 0)} vectors still remain")
            print("   (This might be due to propagation delay - check again in a few minutes)")
            
    except Exception as e:
        print(f"❌ Error clearing Pinecone vectors: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(clear_all_vectors()) 