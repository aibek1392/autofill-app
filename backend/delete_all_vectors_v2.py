#!/usr/bin/env python3
"""
Delete ALL vectors from Pinecone - alternative approach
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.pinecone_client import PineconeClient
from config import settings
from pinecone import ServerlessSpec

async def delete_all_vectors_v2():
    print("🗑️  Deleting ALL vectors from Pinecone (Alternative Method)")
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
        
        print(f"\n⚠️  WARNING: This will delete ALL {total_vectors} vectors from Pinecone!")
        print("   This action cannot be undone.")
        
        # Method 1: Try to delete all vectors using delete_all
        print(f"\n🔍 Attempting to delete all vectors...")
        try:
            # Try to delete all vectors without specifying IDs
            pinecone.index.delete(delete_all=True)
            print("   ✅ Used delete_all=True method")
        except Exception as e:
            print(f"   ❌ delete_all method failed: {e}")
            
            # Method 2: Try to delete by namespace
            print(f"\n🔍 Trying to delete by namespace...")
            try:
                # Get all namespaces
                index_stats = pinecone.index.describe_index_stats()
                namespaces = index_stats.namespaces
                
                if namespaces:
                    for namespace in namespaces.keys():
                        print(f"   🗑️  Deleting namespace: {namespace}")
                        pinecone.index.delete(namespace=namespace)
                    print("   ✅ Deleted all namespaces")
                else:
                    print("   ℹ️  No namespaces found")
            except Exception as e2:
                print(f"   ❌ Namespace deletion failed: {e2}")
                
                # Method 3: Recreate the index
                print(f"\n🔍 Attempting to recreate the index...")
                try:
                    index_name = settings.PINECONE_INDEX_NAME
                    print(f"   🗑️  Deleting index: {index_name}")
                    pinecone.pc.delete_index(index_name)
                    print(f"   ✅ Deleted index: {index_name}")
                    
                    print(f"   🔄 Recreating index: {index_name}")
                    pinecone.pc.create_index(
                        name=index_name,
                        dimension=1536,
                        metric='cosine',
                        spec=ServerlessSpec(
                            cloud='aws',
                            region='us-east-1'
                        )
                    )
                    print(f"   ✅ Recreated index: {index_name}")
                    
                    # Reinitialize the client
                    pinecone._initialize()
                    
                except Exception as e3:
                    print(f"   ❌ Index recreation failed: {e3}")
                    print(f"   💡 You may need to manually delete the index from Pinecone console")
        
        # Verify deletion
        print(f"\n🔍 Verifying deletion...")
        await asyncio.sleep(5)  # Wait for eventual consistency
        final_stats = await pinecone.get_index_stats()
        remaining_vectors = final_stats.get('total_vector_count', 0)
        print(f"   Remaining vectors: {remaining_vectors}")
        
        if remaining_vectors == 0:
            print(f"\n🎉 Complete cleanup successful!")
            print(f"   - All vectors have been deleted from Pinecone")
        else:
            print(f"\n⚠️  Cleanup may not be complete")
            print(f"   - {remaining_vectors} vectors still remain")
            print(f"   - You may need to manually clean up from Pinecone console")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(delete_all_vectors_v2()) 