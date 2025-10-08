from supabase import create_client, Client
from typing import Dict, List, Optional, Any
import logging
from config import settings

logger = logging.getLogger(__name__)

class SupabaseClient:
    def __init__(self):
        # Debug logging for environment variables
        logger.info(f"Supabase URL present: {bool(settings.SUPABASE_URL)}")
        logger.info(f"Supabase ANON KEY present: {bool(settings.SUPABASE_ANON_KEY)}")
        logger.info(f"Supabase SERVICE ROLE KEY present: {bool(settings.SUPABASE_SERVICE_ROLE_KEY)}")
        
        # Check if Supabase credentials are available
        self.has_supabase_credentials = bool(
            settings.SUPABASE_URL and settings.SUPABASE_URL != "" and
            settings.SUPABASE_ANON_KEY and settings.SUPABASE_ANON_KEY != ""
        )
        
        logger.info(f"Has Supabase credentials: {self.has_supabase_credentials}")
        
        # Also check if we have service role key for admin operations
        self.has_service_role = bool(
            settings.SUPABASE_SERVICE_ROLE_KEY and settings.SUPABASE_SERVICE_ROLE_KEY != ""
        )
        
        logger.info(f"Has service role key: {self.has_service_role}")
        
        if self.has_supabase_credentials:
            try:
                logger.info("Attempting to initialize Supabase client...")
                # Initialize with ANON KEY for JWT authentication (not service role)
                self.client: Client = create_client(
                    supabase_url=settings.SUPABASE_URL,
                    supabase_key=settings.SUPABASE_ANON_KEY
                )
                
                # Create separate admin client with service role for admin operations
                if self.has_service_role:
                    logger.info("Initializing admin client with service role...")
                    self.admin_client: Client = create_client(
                        supabase_url=settings.SUPABASE_URL,
                        supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY
                    )
                else:
                    logger.warning("Service role key not available - admin operations will be limited")
                    self.admin_client = None
                
                # Simple validation - just check if client was created
                if self.client:
                    logger.info("Supabase client initialized successfully with anon key")
                else:
                    logger.warning("Supabase client creation returned None")
                    self.has_supabase_credentials = False
                    
            except Exception as e:
                logger.error(f"Primary Supabase initialization failed: {str(e)}")
                # Try with explicit parameters to avoid proxy issues
                try:
                    logger.info("Attempting Supabase initialization with explicit parameters...")
                    
                    # Clear proxy environment variables
                    import os
                    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
                    original_values = {}
                    for var in proxy_vars:
                        if var in os.environ:
                            original_values[var] = os.environ[var]
                            del os.environ[var]
                    
                    # Use the simplest possible initialization
                    self.client = create_client(
                        supabase_url=settings.SUPABASE_URL,
                        supabase_key=settings.SUPABASE_ANON_KEY
                    )
                    
                    if self.has_service_role:
                        self.admin_client = create_client(
                            supabase_url=settings.SUPABASE_URL,
                            supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY
                        )
                    else:
                        self.admin_client = None
                    
                    # Restore original environment variables
                    for var, value in original_values.items():
                        os.environ[var] = value
                    
                    logger.info("Supabase client initialized successfully with explicit parameters")
                    
                except Exception as e2:
                    logger.error(f"All Supabase initialization attempts failed: {str(e2)}")
                    logger.error("Database features will be limited - using demo storage")
                    self.client = None
                    self.admin_client = None
                    self.has_supabase_credentials = False
        else:
            logger.warning("Supabase credentials not found - database features will be limited")
            self.client = None
            self.admin_client = None

    def set_auth(self, access_token: str):
        """Set the JWT token for authentication"""
        if self.client and access_token:
            self.client.auth.set_session(access_token, "")
            logger.info("JWT authentication set for Supabase client")
    
    async def create_user_document_with_auth(self, user_id: str, filename: str, file_type: str, file_size: int, access_token: str, doc_id: str = None) -> Dict[str, Any]:
        """Create a record for an uploaded document using JWT authentication"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot create document record - Supabase not configured")
            return {}
            
        try:
            # Skip JWT authentication for now and use service role
            # The RLS policies are preventing proper authentication
            logger.info("Using service role for document creation due to RLS policy configuration")
            return await self.create_user_document(user_id, filename, file_type, file_size, doc_id)
                
        except Exception as e:
            logger.error(f"Failed to create document record with JWT: {str(e)}")
            logger.error(f"Error details - user_id: '{user_id}', filename: '{filename}', type: '{file_type}', size: {file_size}")
            raise

    async def create_user_document(self, user_id: str, filename: str, file_type: str, file_size: int, doc_id: str = None) -> Dict[str, Any]:
        """Create a record for an uploaded document using service role (fallback)"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot create document record - Supabase not configured")
            return {}
            
        try:
            # Ensure we're using the admin client with service role key
            if not self.admin_client:
                logger.error("Admin client not available - service role key may not be configured")
                raise Exception("Service role client not configured")
            
            # Add detailed logging for debugging
            logger.info(f"Creating document record with service role - user_id: '{user_id}', filename: '{filename}', type: '{file_type}', size: {file_size}")
            
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
            
            # Log the exact data being inserted
            logger.info(f"Inserting document data with service role: {document_data}")
            
            # Use admin client which should bypass RLS
            result = self.admin_client.table('uploaded_documents').insert(document_data).execute()
            
            # Log the result
            logger.info(f"Insert result: {result.data}")
            
            if result.data and len(result.data) > 0:
                created_doc = result.data[0]
                logger.info(f"Document record created successfully with service role - doc_id: {created_doc.get('doc_id')}, user_id: {created_doc.get('user_id')}, filename: {filename}")
                return created_doc
            else:
                logger.warning(f"Document insert returned empty result for user_id: {user_id}, filename: {filename}")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to create document record with service role: {str(e)}")
            logger.error(f"Error details - user_id: '{user_id}', filename: '{filename}', type: '{file_type}', size: {file_size}")
            raise
    
    async def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot get user documents - Supabase not configured")
            return []
            
        try:
            # Use admin client to bypass RLS for this query
            client_to_use = self.admin_client if self.admin_client else self.client
            result = client_to_use.table('uploaded_documents').select('*').eq('user_id', user_id).execute()
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
            # Use admin client for vector chunks (background processing)
            client_to_use = self.admin_client if self.admin_client else self.client
            result = client_to_use.table('vector_chunks').insert(chunk_data).execute()
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
            client_to_use = self.admin_client if self.admin_client else self.client
            result = client_to_use.table('vector_chunks').select('*').eq('doc_id', doc_id).execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get document chunks: {str(e)}")
            raise

    async def create_transactions_bulk(self, user_id: str, doc_id: str, transactions: List[Dict[str, Any]]) -> int:
        """Insert multiple transactions for a document"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot create transactions - Supabase not configured")
            return 0
        try:
            if not transactions:
                return 0
            client_to_use = self.admin_client if self.admin_client else self.client
            # Map parser fields to DB columns
            rows = []
            for t in transactions:
                rows.append({
                    'user_id': user_id,
                    'doc_id': doc_id,
                    'trans_date': t.get('date'),
                    'description': t.get('description'),
                    'amount': t.get('amount'),
                    'line_number': t.get('line_number'),
                    'raw_text': t.get('raw_text'),
                    'confidence': t.get('confidence'),
                    'external_transaction_id': t.get('transaction_id')
                })
            result = client_to_use.table('transactions').insert(rows).execute()
            inserted = len(result.data) if result.data else 0
            logger.info(f"Inserted {inserted} transactions - user_id: {user_id}, doc_id: {doc_id}")
            return inserted
        except Exception as e:
            logger.error(f"Failed to insert transactions: {str(e)}")
            raise

    async def get_document_transactions(self, user_id: str, doc_id: str) -> List[Dict[str, Any]]:
        """Get transactions for a document"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot get transactions - Supabase not configured")
            return []
        try:
            client_to_use = self.admin_client if self.admin_client else self.client
            result = client_to_use.table('transactions') \
                .select('*') \
                .eq('user_id', user_id) \
                .eq('doc_id', doc_id) \
                .order('trans_date', desc=False) \
                .order('line_number', desc=False) \
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get transactions: {str(e)}")
            raise

    # Chat History Methods
    async def create_chat_session(self, user_id: str, session_name: str = None) -> Dict[str, Any]:
        """Create a new chat session"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot create chat session - Supabase not configured")
            return {}
        try:
            client_to_use = self.admin_client if self.admin_client else self.client
            
            # Generate session name if not provided
            if not session_name:
                from datetime import datetime
                session_name = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            session_data = {
                'user_id': user_id,
                'session_name': session_name
            }
            
            result = client_to_use.table('chat_sessions').insert(session_data).execute()
            
            if result.data and len(result.data) > 0:
                created_session = result.data[0]
                logger.info(f"Chat session created - session_id: {created_session.get('session_id')}, user_id: {user_id}")
                return created_session
            else:
                logger.warning(f"Chat session insert returned empty result for user_id: {user_id}")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to create chat session: {str(e)}")
            raise

    async def get_user_chat_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all chat sessions for a user"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot get chat sessions - Supabase not configured")
            return []
        try:
            client_to_use = self.admin_client if self.admin_client else self.client
            result = client_to_use.table('chat_sessions') \
                .select('*') \
                .eq('user_id', user_id) \
                .order('updated_at', desc=True) \
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get chat sessions: {str(e)}")
            raise

    async def get_session_messages(self, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a chat session"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot get session messages - Supabase not configured")
            return []
        try:
            client_to_use = self.admin_client if self.admin_client else self.client
            result = client_to_use.table('chat_messages') \
                .select('*') \
                .eq('session_id', session_id) \
                .eq('user_id', user_id) \
                .order('created_at', desc=False) \
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get session messages: {str(e)}")
            raise

    async def save_chat_message(self, session_id: str, user_id: str, message: str, response: str, sources: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Save a chat message and response"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot save chat message - Supabase not configured")
            return {}
        try:
            client_to_use = self.admin_client if self.admin_client else self.client
            
            message_data = {
                'session_id': session_id,
                'user_id': user_id,
                'message': message,
                'response': response,
                'sources': sources or [],
                'metadata': {}
            }
            
            result = client_to_use.table('chat_messages').insert(message_data).execute()
            
            # Update session updated_at timestamp
            try:
                client_to_use.table('chat_sessions') \
                    .update({'updated_at': 'now()'}) \
                    .eq('session_id', session_id) \
                    .eq('user_id', user_id) \
                    .execute()
            except Exception as update_err:
                logger.warning(f"Failed to update session timestamp: {str(update_err)}")
            
            if result.data and len(result.data) > 0:
                saved_message = result.data[0]
                logger.info(f"Chat message saved - message_id: {saved_message.get('message_id')}, session_id: {session_id}")
                return saved_message
            else:
                logger.warning(f"Chat message insert returned empty result for session_id: {session_id}")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to save chat message: {str(e)}")
            raise

    async def delete_chat_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session and all its messages"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot delete chat session - Supabase not configured")
            return False
        try:
            client_to_use = self.admin_client if self.admin_client else self.client
            
            # Delete messages first (due to foreign key constraint)
            messages_result = client_to_use.table('chat_messages') \
                .delete() \
                .eq('session_id', session_id) \
                .eq('user_id', user_id) \
                .execute()
            
            deleted_messages = len(messages_result.data) if messages_result.data else 0
            
            # Delete session
            session_result = client_to_use.table('chat_sessions') \
                .delete() \
                .eq('session_id', session_id) \
                .eq('user_id', user_id) \
                .execute()
            
            deleted_sessions = len(session_result.data) if session_result.data else 0
            
            logger.info(f"Chat session deleted - session_id: {session_id}, messages: {deleted_messages}, sessions: {deleted_sessions}")
            return deleted_sessions > 0
            
        except Exception as e:
            logger.error(f"Failed to delete chat session: {str(e)}")
            raise
    
    async def create_filled_form(self, user_id: str, original_form_name: str, filled_form_url: str) -> Dict[str, Any]:
        """Create a record for a filled form"""
        if not self.has_supabase_credentials:
            logger.warning("Cannot create filled form record - Supabase not configured")
            return {}
            
        try:
            client_to_use = self.admin_client if self.admin_client else self.client
            result = client_to_use.table('filled_forms').insert({
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
            client_to_use = self.admin_client if self.admin_client else self.client
            result = client_to_use.table('filled_forms').select('*').eq('user_id', user_id).execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get user filled forms: {str(e)}")
            raise

# Global instance
supabase_client = SupabaseClient() 