from typing import List, Dict, Any, Optional
import logging
from pinecone import Pinecone, ServerlessSpec
from config import settings
import uuid

logger = logging.getLogger(__name__)

class PineconeClient:
    def __init__(self):
        self.pc = None
        self.index = None
        self.index_name = settings.PINECONE_INDEX_NAME
        self._initialize()
    
    def _initialize(self):
        """Initialize Pinecone client and index"""
        try:
            if not settings.PINECONE_API_KEY:
                logger.warning("Pinecone API key not provided. Vector search will be disabled.")
                return
            
            # Initialize Pinecone client (modern API)
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Check if index exists
            existing_indexes = self.pc.list_indexes()
            index_names = [idx.name for idx in existing_indexes]
            
            if self.index_name not in index_names:
                logger.error(f"Pinecone index '{self.index_name}' not found. Available indexes: {index_names}")
                logger.info("Run 'python setup_pinecone.py' to create the index")
                return
            
            # Connect to existing index
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Successfully connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Pinecone initialization failed: {str(e)}. Vector search will be limited.")
            self.pc = None
            self.index = None
    
    async def upsert_embeddings(self, vectors: List[Dict[str, Any]]) -> bool:
        """Upsert embeddings to Pinecone"""
        if not self.pc:
            logger.warning("Cannot upsert embeddings - Pinecone client not initialized")
            return False
            
        try:
            # Format vectors for Pinecone
            formatted_vectors = []
            for vector in vectors:
                formatted_vectors.append({
                    'id': vector['id'],
                    'values': vector['embedding'],
                    'metadata': vector['metadata']
                })
            
            # Upsert in batches of 100
            batch_size = 100
            for i in range(0, len(formatted_vectors), batch_size):
                batch = formatted_vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
            
            logger.info(f"Embeddings upserted successfully - count: {len(vectors)}")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert embeddings: {str(e)}")
            raise
    
    async def search_similar(self, query_embedding: List[float], user_id: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        try:
            if top_k is None:
                top_k = settings.TOP_K
            
            # Search with user_id filter
            results = self.index.query(
                vector=query_embedding,
                filter={'user_id': user_id},
                top_k=top_k,
                include_metadata=True,
                include_values=False
            )
            
            # Format results
            formatted_results = []
            for match in results.matches:
                if match.score >= settings.SIMILARITY_THRESHOLD:
                    formatted_results.append({
                        'id': match.id,
                        'score': match.score,
                        'metadata': match.metadata
                    })
            
            logger.info(f"Vector search completed - user_id: {user_id}, results_count: {len(formatted_results)}")
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to search vectors: {str(e)}")
            raise
    
    async def delete_document_vectors(self, doc_id: str) -> bool:
        """Delete all vectors for a specific document"""
        try:
            # Query to get all vectors for this document
            results = self.index.query(
                vector=[0] * 1536,  # Dummy vector for query
                filter={'doc_id': doc_id},
                top_k=10000,  # Large number to get all
                include_metadata=False,
                include_values=False
            )
            
            # Extract IDs and delete
            ids_to_delete = [match.id for match in results.matches]
            if ids_to_delete:
                self.index.delete(ids=ids_to_delete)
                logger.info(f"Document vectors deleted - doc_id: {doc_id}, count: {len(ids_to_delete)}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete document vectors: {str(e)}")
            raise
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vector_count': stats.total_vector_count,
                'dimension': stats.dimension,
                'index_fullness': stats.index_fullness
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {str(e)}")
            raise
    
    def generate_vector_id(self, doc_id: str, chunk_index: int) -> str:
        """Generate a unique vector ID"""
        return f"{doc_id}_{chunk_index}_{uuid.uuid4().hex[:8]}"

    async def search_similar_with_filter(self, query_embedding: List[float], filter: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar embeddings with custom filter"""
        try:
            # Search with custom filter
            results = self.index.query(
                vector=query_embedding,
                filter=filter,
                top_k=top_k,
                include_metadata=True,
                include_values=False
            )
            
            # Format results
            formatted_results = []
            for match in results.matches:
                if match.score >= settings.SIMILARITY_THRESHOLD:
                    formatted_results.append({
                        'id': match.id,
                        'score': match.score,
                        'metadata': match.metadata
                    })
            
            logger.info(f"Vector search with filter completed - filter: {filter}, results_count: {len(formatted_results)}")
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to search vectors with filter: {str(e)}")
            raise

# Global instance
pinecone_client = PineconeClient() 