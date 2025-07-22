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
                # Delete in batches to avoid timeout
                batch_size = 100
                for i in range(0, len(ids_to_delete), batch_size):
                    batch = ids_to_delete[i:i + batch_size]
                    self.index.delete(ids=batch)
                    logger.info(f"Deleted batch {i//batch_size + 1}: {len(batch)} vectors")
                
                logger.info(f"Document vectors deleted - doc_id: {doc_id}, count: {len(ids_to_delete)}")
                
                # Wait a moment for deletion to propagate
                import asyncio
                await asyncio.sleep(1)
                
                # Verify deletion
                verify_results = self.index.query(
                    vector=[0] * 1536,
                    filter={'doc_id': doc_id},
                    top_k=10,
                    include_metadata=False,
                    include_values=False
                )
                
                if verify_results.matches:
                    logger.warning(f"Deletion verification failed - {len(verify_results.matches)} vectors still exist for doc_id: {doc_id}")
                    return False
                else:
                    logger.info(f"Deletion verified - all vectors removed for doc_id: {doc_id}")
                    return True
            else:
                logger.info(f"No vectors found to delete for doc_id: {doc_id}")
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

    async def delete_document_vectors_comprehensive(self, doc_id: str, user_id: str, filename: str) -> bool:
        """Comprehensive deletion of document vectors using multiple strategies"""
        try:
            logger.info(f"Starting comprehensive deletion for doc_id: {doc_id}, user_id: {user_id}, filename: {filename}")
            
            total_deleted = 0
            
            # Strategy 1: Delete by doc_id
            try:
                doc_vectors = self.index.query(
                    vector=[0.0] * 1536,
                    filter={'doc_id': doc_id},
                    top_k=10000,
                    include_metadata=False,
                    include_values=False
                )
                
                if doc_vectors.matches:
                    doc_ids = [match.id for match in doc_vectors.matches]
                    self.index.delete(ids=doc_ids)
                    total_deleted += len(doc_ids)
                    logger.info(f"Strategy 1: Deleted {len(doc_ids)} vectors by doc_id")
                else:
                    logger.info("Strategy 1: No vectors found by doc_id")
                    
            except Exception as e:
                logger.warning(f"Strategy 1 failed: {str(e)}")
            
            # Strategy 2: Delete by user_id + filename
            try:
                user_filename_vectors = self.index.query(
                    vector=[0.0] * 1536,
                    filter={'user_id': user_id, 'filename': filename},
                    top_k=10000,
                    include_metadata=False,
                    include_values=False
                )
                
                if user_filename_vectors.matches:
                    user_filename_ids = [match.id for match in user_filename_vectors.matches]
                    self.index.delete(ids=user_filename_ids)
                    total_deleted += len(user_filename_ids)
                    logger.info(f"Strategy 2: Deleted {len(user_filename_ids)} vectors by user_id+filename")
                else:
                    logger.info("Strategy 2: No vectors found by user_id+filename")
                    
            except Exception as e:
                logger.warning(f"Strategy 2 failed: {str(e)}")
            
            # Strategy 3: Delete by filename only (fallback)
            try:
                filename_vectors = self.index.query(
                    vector=[0.0] * 1536,
                    filter={'filename': filename},
                    top_k=10000,
                    include_metadata=False,
                    include_values=False
                )
                
                if filename_vectors.matches:
                    filename_ids = [match.id for match in filename_vectors.matches]
                    self.index.delete(ids=filename_ids)
                    total_deleted += len(filename_ids)
                    logger.info(f"Strategy 3: Deleted {len(filename_ids)} vectors by filename only")
                else:
                    logger.info("Strategy 3: No vectors found by filename only")
                    
            except Exception as e:
                logger.warning(f"Strategy 3 failed: {str(e)}")
            
            # Wait for deletion to propagate
            import asyncio
            await asyncio.sleep(2)
            
            # Final verification
            remaining_vectors = self.index.query(
                vector=[0.0] * 1536,
                filter={'doc_id': doc_id},
                top_k=10,
                include_metadata=False,
                include_values=False
            )
            
            if remaining_vectors.matches:
                logger.warning(f"Deletion incomplete - {len(remaining_vectors.matches)} vectors still exist")
                return False
            else:
                logger.info(f"Comprehensive deletion successful - {total_deleted} vectors deleted")
                return True
                
        except Exception as e:
            logger.error(f"Comprehensive deletion failed: {str(e)}")
            return False

# Global instance
pinecone_client = PineconeClient() 