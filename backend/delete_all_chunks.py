#!/usr/bin/env python3
"""
Delete all rows from the vector_chunks table in Supabase
"""

import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.supabase_client import SupabaseClient

async def delete_all_chunks():
    print("🗑️  Deleting all rows from vector_chunks table in Supabase")
    print("=" * 60)
    
    supabase = SupabaseClient()
    try:
        result = supabase.client.table('vector_chunks').delete().neq('chunk_id', '').execute()
        print(f"✅ Deleted all rows from vector_chunks. Result: {result.data}")
    except Exception as e:
        print(f"❌ Error deleting chunks: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(delete_all_chunks()) 