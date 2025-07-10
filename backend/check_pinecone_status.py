#!/usr/bin/env python3
"""
Check Pinecone status and see what vectors are stored
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.pinecone_client import PineconeClient

async def check_pinecone_status():
    print("🔍 Checking Pinecone status")
    print("=" * 60)
    
    pinecone = PineconeClient()
    
    try:
        # Get index stats
        print("📊 Getting Pinecone index statistics...")
        stats = await pinecone.get_index_stats()
        print(f"   Total vectors: {stats.get('total_vector_count', 0)}")
        print(f"   Dimension: {stats.get('dimension', 'Unknown')}")
        print(f"   Index fullness: {stats.get('index_fullness', 'Unknown')}")
        
        if stats.get('total_vector_count', 0) == 0:
            print("\n✅ Pinecone is clean - no vectors found!")
        else:
            print(f"\n⚠️  Found {stats.get('total_vector_count', 0)} vectors in Pinecone")
            print("   You may want to run a cleanup script to remove them.")
        
    except Exception as e:
        print(f"❌ Error checking Pinecone status: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_pinecone_status()) 