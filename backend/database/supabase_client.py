from supabase import create_client, Client
from typing import Dict, List, Optional, Any
import logging
from config import settings

logger = logging.getLogger(__name__)

class SupabaseClient:
    def __init__(self):
        # Check if Supabase credentials are available
        self.has_supabase_credentials = bool(
            settings.SUPABASE_URL and settings.SUPABASE_URL != "" and
            settings.SUPABASE_SERVICE_ROLE_KEY and settings.SUPABASE_SERVICE_ROLE_KEY != ""
        )
        
        if self.has_supabase_credentials:
            try:
                # Initialize without any extra parameters that might cause issues
                self.client: Client = create_client(
                    supabase_url=settings.SUPABASE_URL,
                    supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY
                )
                
                # Simple validation - just check if client was created
                if self.client:
                    logger.info("Supabase client initialized successfully")
                else:
                    logger.warning("Supabase client creation returned None")
                    self.has_supabase_credentials = False
                    
            except Exception as e:
                logger.warning(f"Supabase initialization failed: {str(e)}. Database features will be limited.")
                self.client = None
                self.has_supabase_credentials = False
        else:
            logger.warning("Supabase credentials not found - database features will be limited")
            self.client = None
    
    async def create_user_document(self, user_id: str, filename: str, file_type: str, file_size: int, doc_id: str = None) -> Dict[str, Any]:
        """Create a record for an uploaded document"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot create document record - Supabase not configured")
            return {}
            
        try:
            document_data = {
                'user_id': user_id,
                'filename': filename,
                'type': file_type,
                'file_size': file_size,
                'processing_status': 'uploaded'
                # uploaded_at will be set automatically by default
            }
            
            # Add doc_id if provided
            if doc_id:
                document_data['doc_id'] = doc_id
            
            result = self.client.table('uploaded_documents').insert(document_data).execute()
            
            logger.info(f"Document record created - user_id: {user_id}, filename: {filename}")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create document record: {str(e)}")
            raise
    
    async def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot get user documents - Supabase not configured")
            return []
            
        try:
            result = self.client.table('uploaded_documents').select('*').eq('user_id', user_id).execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get user documents: {str(e)}")
            raise
    
    async def create_vector_chunk(self, chunk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a vector chunk record"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot create vector chunk - Supabase not configured")
            return {}
            
        try:
            result = self.client.table('vector_chunks').insert(chunk_data).execute()
            logger.info(f"Vector chunk created - chunk_id: {chunk_data.get('chunk_id')}")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create vector chunk: {str(e)}")
            raise
    
    async def get_document_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a document"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot get document chunks - Supabase not configured")
            return []
            
        try:
            result = self.client.table('vector_chunks').select('*').eq('doc_id', doc_id).execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get document chunks: {str(e)}")
            raise
    
    async def create_filled_form(self, user_id: str, original_form_name: str, filled_form_url: str) -> Dict[str, Any]:
        """Create a record for a filled form"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot create filled form record - Supabase not configured")
            return {}
            
        try:
            result = self.client.table('filled_forms').insert({
                'user_id': user_id,
                'original_form_name': original_form_name,
                'filled_form_url': filled_form_url
                # created_at will be set automatically by default
            }).execute()
            
            logger.info(f"Filled form record created - user_id: {user_id}, form_name: {original_form_name}")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to create filled form record: {str(e)}")
            raise
    
    async def get_user_filled_forms(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all filled forms for a user"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot get user filled forms - Supabase not configured")
            return []
            
        try:
            result = self.client.table('filled_forms').select('*').eq('user_id', user_id).execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get user filled forms: {str(e)}")
            raise

# Global instance
supabase_client = SupabaseClient() 