#!/usr/bin/env python3

"""
Clear ALL vectors from Pinecone to remove any stored documents
"""

import asyncio
import logging
from database.pinecone_client import pinecone_client
from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clear_all_vectors():
    """Clear ALL vectors from Pinecone"""
    try:
        logger.info("🗑️  Clearing ALL vectors from Pinecone...")
        
        # Get all vectors without any filter
        results = await pinecone_client.search_similar_with_filter(
            query_embedding=[0.0] * 1536,
            filter={},  # No filter = get all vectors
            top_k=10000  # Get a large number
        )
        
        if results:
            ids_to_delete = [result['id'] for result in results]
            success = await pinecone_client.delete_vectors(ids_to_delete)
            logger.info(f"✅ Deleted {len(ids_to_delete)} vectors from Pinecone")
            logger.info("💡 All stored documents have been removed")
        else:
            logger.info("ℹ️  No vectors found in Pinecone")
        
    except Exception as e:
        logger.error(f"❌ Failed to clear vectors: {str(e)}")

if __name__ == "__main__":
    asyncio.run(clear_all_vectors()) 