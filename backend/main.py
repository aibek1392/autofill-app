import os
import uuid
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, StreamingResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
import logging
import json
from config import settings
from services.document_processor import document_processor
from services.transaction_parser import transaction_parser
from services.rag_service import rag_service
from services.form_filler import form_filler
from services.web_form_service import web_form_service
from database.supabase_client import supabase_client
from database.pinecone_client import pinecone_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Remove hardcoded demo user ID - require proper authentication
# DEMO_USER_ID = "550e8400-e29b-41d4-a716-446655440000"  # Only used as fallback when no auth available

# Create FastAPI app
app = FastAPI(
    title="AI Autofill Form App",
    description="Full-stack AI application for document processing and form autofill",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
   CORSMiddleware,
    allow_origins=["*"],  # Or restrict to ["chrome-extension://<your-extension-id>", "https://jobs.ashbyhq.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Create upload directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# In-memory storage for demo mode when Supabase is not available
demo_documents = {}
demo_filled_forms = {}

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error on {request.method} {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body) if hasattr(exc, 'body') else None}
    )

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    user_id: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    context_used: int

class FormFillRequest(BaseModel):
    user_id: str

class FieldUpdateRequest(BaseModel):
    field_name: str
    field_value: str
    user_id: str

class WebFormAnalysisRequest(BaseModel):
    url: str
    html_content: Optional[str] = None

class WebFormAutofillRequest(BaseModel):
    url: str
    html_content: Optional[str] = None
    user_id: Optional[str] = None

class FieldMatchRequest(BaseModel):
    field_label: str
    field_type: str = "text"
    field_context: str = ""
    placeholder: str = ""
    user_id: Optional[str] = None

class FieldMatchResponse(BaseModel):
    matched: bool
    confidence: float
    value: Optional[str] = None
    field_type: Optional[str] = None
    source: Optional[str] = None
    suggestions: List[Dict[str, Any]] = []

class TransactionsResponse(BaseModel):
    doc_id: str
    transactions: List[Dict[str, Any]]

class BulkFieldMatchRequest(BaseModel):
    fields: List[Dict[str, str]]  # List of field info dicts
    user_id: Optional[str] = None

# Dependency to get current user (simplified for demo)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current user from JWT token (simplified for demo)"""
    # In production, you'd validate the JWT token here
    # For now, we'll extract user_id from the token (demo purposes)
    try:
        # This is a simplified approach - in production, decode and validate JWT
        user_id = credentials.credentials  # Assuming token contains user_id
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        return user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Autofill Form App API", "status": "running"}

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check Pinecone connection (with timeout to avoid blocking)
        pinecone_status = "unknown"
        pinecone_stats = None
        try:
            pinecone_stats = await pinecone_client.get_index_stats()
            pinecone_status = "connected"
        except Exception as e:
            logger.warning(f"Pinecone health check failed: {str(e)}")
            pinecone_status = "disconnected"
        
        # Check Supabase connection
        supabase_status = "unknown"
        try:
            if supabase_client.has_supabase_credentials:
                # Simple query to test connection
                supabase_client.admin_client.table('uploaded_documents').select('doc_id').limit(1).execute()
                supabase_status = "connected"
            else:
                supabase_status = "not_configured"
        except Exception as e:
            logger.warning(f"Supabase health check failed: {str(e)}")
            supabase_status = "disconnected"
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": "running",
                "pinecone": pinecone_status,
                "supabase": supabase_status
            },
            "pinecone_stats": pinecone_stats
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

@app.get("/api/ping")
async def ping():
    """Simple ping endpoint for keep-alive services"""
    return {
        "status": "pong",
        "timestamp": datetime.now().isoformat(),
        "message": "Server is alive"
    }

async def process_document_background(file_path: str, filename: str, user_id: str):
    """Background task to process uploaded document"""
    try:
        logger.info(f"Starting background processing - file_path: {file_path}, filename: {filename}, user_id: {user_id}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found for processing: {file_path}")
            # Update document status to indicate processing failed
            if supabase_client.has_supabase_credentials:
                try:
                    # Find the document by filename and user_id
                    docs_result = supabase_client.admin_client.table('uploaded_documents').select('*').eq('filename', filename).eq('user_id', user_id).execute()
                    if docs_result.data:
                        doc_id = docs_result.data[0]['doc_id']
                        # Update status to failed
                        supabase_client.admin_client.table('uploaded_documents').update({'processing_status': 'failed'}).eq('doc_id', doc_id).execute()
                        logger.info(f"Updated document status to 'failed' for missing file - doc_id: {doc_id}")
                except Exception as e:
                    logger.error(f"Failed to update document status: {str(e)}")
            return
        
        # Check file size
        file_size = os.path.getsize(file_path)
        logger.info(f"Processing file - size: {file_size} bytes")
        
        if file_size == 0:
            logger.error(f"File is empty: {file_path}")
            return
        
        # Update document status to processing
        doc_id = None
        if supabase_client.has_supabase_credentials:
            try:
                docs_result = supabase_client.admin_client.table('uploaded_documents').select('*').eq('filename', filename).eq('user_id', user_id).execute()
                if docs_result.data:
                    doc_id = docs_result.data[0]['doc_id']
                    # Update status to processing
                    supabase_client.admin_client.table('uploaded_documents').update({'processing_status': 'processing'}).eq('doc_id', doc_id).execute()
                    logger.info(f"Updated document status to 'processing' - doc_id: {doc_id}")
            except Exception as e:
                logger.error(f"Failed to update document status to processing: {str(e)}")
        
        # Process document
        logger.info(f"Starting document processing - file_path: {file_path}")
        document = await document_processor.process_document(file_path, filename, doc_id)
        logger.info(f"Document processed successfully - doc_id: {document['doc_id']}, text_length: {len(document['text'])}")
        
        # Parse transactions row-by-row for financial statements
        transactions = []
        try:
            transactions = transaction_parser.parse_transactions(document.get('text', ''))
            logger.info(f"Transaction parsing complete - count: {len(transactions)}")
        except Exception as parse_err:
            logger.warning(f"Transaction parsing failed: {str(parse_err)}")

        # Persist transactions (best-effort)
        if transactions and supabase_client.has_supabase_credentials and doc_id:
            try:
                inserted = await supabase_client.create_transactions_bulk(user_id, doc_id, transactions)
                logger.info(f"Transactions saved to DB - inserted: {inserted}")
            except Exception as tx_err:
                logger.warning(f"Failed to save transactions: {str(tx_err)}")

        # Create transaction chunks for embeddings in addition to text chunks
        transaction_chunks = []
        try:
            if transactions:
                transaction_chunks = transaction_parser.create_transaction_chunks(transactions, document['doc_id'], filename)
        except Exception as ch_err:
            logger.warning(f"Failed to create transaction chunks: {str(ch_err)}")

        # Document record is already created in the upload endpoint, so we don't need to create it again
        # Just chunk and process the document
        chunks = document_processor.chunk_document(document)
        if transaction_chunks:
            chunks = chunks + transaction_chunks
        logger.info(f"Document chunked successfully - chunks: {len(chunks)}")
        
        # Process through RAG pipeline with document for field embeddings
        await rag_service.process_document_pipeline(chunks, user_id, document['doc_id'], document)
        logger.info(f"RAG pipeline completed successfully - doc_id: {document['doc_id']}")
        
        # Update document status to completed
        if supabase_client.has_supabase_credentials and doc_id:
            try:
                supabase_client.admin_client.table('uploaded_documents').update({'processing_status': 'completed'}).eq('doc_id', doc_id).execute()
                logger.info(f"Updated document status to 'completed' - doc_id: {doc_id}")
            except Exception as e:
                logger.error(f"Failed to update document status to completed: {str(e)}")
        
        logger.info(f"Document processing completed successfully - user_id: {user_id}, doc_id: {document['doc_id']}, filename: {filename}")
        
    except Exception as e:
        logger.error(f"Background document processing failed: {str(e)}")
        logger.error(f"Error details - file_path: {file_path}, filename: {filename}, user_id: {user_id}")
        
        # Update document status to failed
        if supabase_client.has_supabase_credentials:
            try:
                docs_result = supabase_client.admin_client.table('uploaded_documents').select('*').eq('filename', filename).eq('user_id', user_id).execute()
                if docs_result.data:
                    doc_id = docs_result.data[0]['doc_id']
                    supabase_client.admin_client.table('uploaded_documents').update({'processing_status': 'failed'}).eq('doc_id', doc_id).execute()
                    logger.info(f"Updated document status to 'failed' due to processing error - doc_id: {doc_id}")
            except Exception as status_error:
                logger.error(f"Failed to update document status to failed: {str(status_error)}")
        
        # Re-raise the exception for debugging
        import traceback
        traceback.print_exc()

@app.post("/api/upload")
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None)
):
    """Upload and process documents"""
    try:
        logger.info(f"Upload request received - user_id: {user_id}, files_count: {len(files) if files else 0}")
        
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Use demo user if no user_id provided
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not provided")
        
        uploaded_files = []
        
        for file in files:
            logger.info(f"Processing file: {file.filename}, size: {file.size}, content_type: {file.content_type}")
            
            # Validate file type
            if not file.filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file.filename}"
                )
            
            # Validate file size
            if file.size and file.size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large: {file.filename}. Max size: {settings.MAX_FILE_SIZE} bytes"
                )
            
            # Additional validation for file content
            if file.size == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"File is empty: {file.filename}"
                )
            
            # Create uploads directory if it doesn't exist
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            
            # Save file
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.filename)[1]
            safe_filename = f"{file_id}{file_extension}"
            file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
            
            try:
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # Verify file was written correctly
                actual_size = os.path.getsize(file_path)
                logger.info(f"File saved locally: {safe_filename}, expected size: {file.size}, actual size: {actual_size}")
                
                # Upload to Supabase Storage if available
                if supabase_client.has_supabase_credentials:
                    try:
                        # Read the file content for upload
                        with open(file_path, "rb") as f:
                            file_content = f.read()
                        
                        # Upload to Supabase Storage
                        upload_response = supabase_client.admin_client.storage.from_('documents').upload(
                            file=file_content,
                            path=safe_filename,
                            file_options={"content-type": file.content_type or "application/octet-stream"}
                        )
                        logger.info(f"File uploaded to Supabase Storage: {safe_filename}")
                        
                    except Exception as storage_error:
                        logger.warning(f"Failed to upload to Supabase Storage: {str(storage_error)}")
                        # Continue with local storage only
                else:
                    logger.info("Supabase Storage not available, using local storage only")
                
            except Exception as e:
                logger.error(f"Failed to save file {file.filename}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to save file: {file.filename}")
            
            # Always create document record in database (regardless of AI processing)
            doc_record_created = False
            try:
                if supabase_client.has_supabase_credentials:
                    # Extract JWT token from Authorization header
                    access_token = None
                    if authorization and authorization.startswith("Bearer "):
                        access_token = authorization[7:]  # Remove "Bearer " prefix
                    
                    # Try JWT authentication first, fallback to service role
                    if access_token:
                        try:
                            doc_record = await supabase_client.create_user_document_with_auth(
                                user_id=user_id,
                                filename=file.filename,
                                file_type=file.content_type or "application/octet-stream",
                                file_size=actual_size,
                                access_token=access_token,
                                doc_id=file_id
                            )
                            logger.info(f"Document record created in Supabase with JWT - user_id: {user_id}, filename: {file.filename}")
                            doc_record_created = True
                        except Exception as jwt_error:
                            logger.warning(f"JWT authentication failed, trying service role: {str(jwt_error)}")
                            # Fallback to service role
                            doc_record = await supabase_client.create_user_document(
                                user_id=user_id,
                                filename=file.filename,
                                file_type=file.content_type or "application/octet-stream",
                                file_size=actual_size,
                                doc_id=file_id
                            )
                            logger.info(f"Document record created in Supabase with service role - user_id: {user_id}, filename: {file.filename}")
                            doc_record_created = True
                    else:
                        # No JWT token, use service role
                        doc_record = await supabase_client.create_user_document(
                            user_id=user_id,
                            filename=file.filename,
                            file_type=file.content_type or "application/octet-stream",
                            file_size=actual_size,
                            doc_id=file_id
                        )
                        logger.info(f"Document record created in Supabase with service role - user_id: {user_id}, filename: {file.filename}")
                        doc_record_created = True
                else:
                    logger.warning("Supabase not available, will use demo storage")
            except Exception as e:
                logger.warning(f"Failed to create document record in Supabase: {str(e)}")
                # Continue to demo storage fallback
            
            # Only use demo storage as fallback if Supabase failed
            if not doc_record_created:
                if user_id not in demo_documents:
                    demo_documents[user_id] = []
                
                demo_documents[user_id].append({
                    "doc_id": file_id,
                    "filename": file.filename,
                    "type": file.content_type or "application/octet-stream",
                    "file_size": actual_size,
                    "uploaded_at": datetime.now().isoformat(),
                    "processing_status": "uploaded"
                })
                logger.info(f"Document stored in demo storage (fallback) - user_id: {user_id}, filename: {file.filename}")
            else:
                logger.info(f"Document successfully stored in Supabase - user_id: {user_id}, filename: {file.filename}")
            
            # Add background task for processing (only if we have required services)
            if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
                background_tasks.add_task(
                    process_document_background,
                    file_path,
                    file.filename,
                    user_id
                )
                status = "processing"
            else:
                status = "uploaded"  # No AI processing without OpenAI key
            
            uploaded_files.append({
                "filename": file.filename,
                "file_id": file_id,
                "status": status,
                "size": file.size,
                "type": file.content_type
            })
        
        logger.info(f"Files uploaded successfully - user_id: {user_id}, file_count: {len(files)}")
        
        return {
            "message": "Files uploaded successfully",
            "files": uploaded_files,
            "total": len(uploaded_files)
        }
    
    except HTTPException:
        # Re-raise HTTPExceptions (like 400 Bad Request) without modification
        raise
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def get_user_documents(user_id: Optional[str] = Header(None, alias="X-User-ID")):
    """Get all documents for the current user"""
    try:
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not provided")
        
        documents = []
        
        # Try to get documents from Supabase first
        if supabase_client.has_supabase_credentials:
            try:
                documents = await supabase_client.get_user_documents(user_id)
                logger.info(f"Retrieved {len(documents)} documents from Supabase for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to get documents from Supabase: {str(e)}")
                # Fall back to demo storage
                documents = demo_documents.get(user_id, [])
                logger.info(f"Retrieved {len(documents)} documents from demo storage (fallback) for user {user_id}")
        else:
            # Use demo storage when Supabase is not available
            documents = demo_documents.get(user_id, [])
            logger.info(f"Retrieved {len(documents)} documents from demo storage for user {user_id}")
            
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Failed to get user documents: {str(e)}")
        # Return demo storage as final fallback
        return {"documents": demo_documents.get(user_id, [])}

@app.delete("/api/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None)
):
    """Delete a document completely from all storage locations"""
    try:
        logger.info(f"Delete request received - doc_id: {doc_id}, user_id: {user_id}")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not provided")
        
        if not supabase_client.has_supabase_credentials:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Get document info first to verify ownership and get details
        try:
            client = supabase_client.admin_client if supabase_client.admin_client else supabase_client.client
            doc_result = client.table('uploaded_documents').select('*').eq('doc_id', doc_id).eq('user_id', user_id).execute()
            
            if not doc_result.data:
                raise HTTPException(status_code=404, detail="Document not found or access denied")
            
            document = doc_result.data[0]
            logger.info(f"Found document to delete: {document['filename']} - doc_id: {doc_id}")
            
        except Exception as e:
            logger.error(f"Failed to get document info: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve document information")
        
        # Step 1: Delete from Pinecone (vectors) - Comprehensive deletion
        try:
            logger.info(f"Deleting vectors from Pinecone for doc_id: {doc_id}")
            
            # Use comprehensive deletion method
            deletion_success = await pinecone_client.delete_document_vectors_comprehensive(
                doc_id=doc_id,
                user_id=user_id,
                filename=document['filename']
            )
            
            if deletion_success:
                logger.info(f"Successfully completed vector deletion for doc_id: {doc_id}")
            else:
                logger.warning(f"Vector deletion may be incomplete for doc_id: {doc_id}")
                
        except Exception as e:
            logger.warning(f"Failed to delete vectors from Pinecone: {str(e)}")
            # Continue with other deletions even if Pinecone fails
        
        # Step 2: Delete from Supabase vector_chunks table
        try:
            logger.info(f"Deleting chunks from Supabase for doc_id: {doc_id}")
            chunks_result = client.table('vector_chunks').delete().eq('doc_id', doc_id).eq('user_id', user_id).execute()
            deleted_chunks = len(chunks_result.data) if chunks_result.data else 0
            logger.info(f"Deleted {deleted_chunks} chunks from Supabase vector_chunks table")
            
        except Exception as e:
            logger.error(f"Failed to delete chunks from Supabase: {str(e)}")
            # Continue with other deletions

        # Step 2.5: Delete transactions from Supabase transactions table
        try:
            logger.info(f"Deleting transactions from Supabase for doc_id: {doc_id}")
            txns_result = client.table('transactions').delete().eq('doc_id', doc_id).eq('user_id', user_id).execute()
            deleted_txns = len(txns_result.data) if txns_result.data else 0
            logger.info(f"Deleted {deleted_txns} transactions from Supabase transactions table")
            
        except Exception as e:
            logger.error(f"Failed to delete transactions from Supabase: {str(e)}")
            # Continue with other deletions
        
        # Step 3: Delete physical file from disk
        try:
            # Try to find and delete the physical file
            # Files are stored with UUID names, so we need to search for files with the doc_id
            import glob
            
            # Search for files that might match this doc_id
            possible_files = glob.glob(os.path.join(settings.UPLOAD_DIR, f"{doc_id}*"))
            
            deleted_files = 0
            for file_path in possible_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        deleted_files += 1
                        logger.info(f"Deleted physical file: {file_path}")
                except Exception as file_error:
                    logger.warning(f"Failed to delete file {file_path}: {str(file_error)}")
            
            if deleted_files == 0:
                logger.warning(f"No physical files found to delete for doc_id: {doc_id}")
            
        except Exception as e:
            logger.warning(f"Failed to delete physical files: {str(e)}")
            # Continue with database deletion
        
        # Step 4: Delete from Supabase uploaded_documents table (this should be last)
        try:
            logger.info(f"Deleting document record from Supabase for doc_id: {doc_id}")
            doc_delete_result = client.table('uploaded_documents').delete().eq('doc_id', doc_id).eq('user_id', user_id).execute()
            
            if doc_delete_result.data:
                logger.info(f"Successfully deleted document record from Supabase")
            else:
                logger.warning("No document record was deleted from Supabase")
            
        except Exception as e:
            logger.error(f"Failed to delete document record from Supabase: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete document record")
        
        logger.info(f"Document deletion completed successfully - doc_id: {doc_id}, filename: {document['filename']}")
        
        # Step 3.5: Delete from Supabase Storage bucket
        try:
            if supabase_client.has_supabase_credentials:
                filename = document['filename']
                file_extension = os.path.splitext(filename)[1]
                safe_filename = f"{doc_id}{file_extension}"
                logger.info(f"Deleting file from Supabase Storage: {safe_filename}")
                delete_result = supabase_client.admin_client.storage.from_('documents').remove(safe_filename)
                logger.info(f"Deleted file from Supabase Storage: {safe_filename}")
        except Exception as e:
            logger.warning(f"Failed to delete file from Supabase Storage: {str(e)}")
            # Continue with other deletions
        
        return {
            "message": "Document deleted successfully",
            "doc_id": doc_id,
            "filename": document['filename'],
            "deleted_from": [
                "uploaded_documents",
                "vector_chunks", 
                "pinecone_vectors",
                "physical_files"
            ]
        }
        
    except HTTPException:
        # Re-raise HTTPExceptions without modification
        raise
    except Exception as e:
        logger.error(f"Document deletion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_documents(request: ChatRequest):
    """Chat with user's documents using RAG"""
    try:
        # Search relevant documents
        search_results = await rag_service.search_documents(
            query=request.message,
            user_id=request.user_id,
            top_k=5
        )
        
        if not search_results:
            return ChatResponse(
                answer="I couldn't find any relevant information in your documents to answer this question.",
                sources=[],
                context_used=0
            )
        
        # Generate response
        response = await rag_service.generate_response(
            query=request.message,
            context=search_results,
            user_id=request.user_id
        )
        
        return ChatResponse(
            answer=response['answer'],
            sources=response['sources'],
            context_used=response['context_used']
        )
    
    except Exception as e:
        logger.error(f"Chat request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def chat_with_documents_stream(request: ChatRequest):
    """Chat with user's documents using RAG with streaming response"""
    async def generate_stream():
        try:
            # Search relevant documents
            search_results = await rag_service.search_documents(
                query=request.message,
                user_id=request.user_id,
                top_k=5
            )
            
            if not search_results:
                yield f"data: {json.dumps({'type': 'error', 'content': 'I could not find any relevant information in your documents to answer this question.', 'sources': [], 'context_used': 0})}\n\n"
                return
            
            # Generate streaming response
            async for chunk in rag_service.generate_streaming_response(
                query=request.message,
                context=search_results,
                user_id=request.user_id
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming chat request failed: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'content': f'I encountered an error while processing your question: {str(e)}', 'sources': [], 'context_used': 0})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8"
        }
    )

@app.post("/api/upload-form")
async def upload_form(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """Upload a form to be filled"""
    try:
        # Validate file type (only PDF forms)
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF forms are supported"
            )
        
        # Save form file
        form_id = str(uuid.uuid4())
        form_filename = f"form_{form_id}.pdf"
        form_path = os.path.join(settings.UPLOAD_DIR, form_filename)
        
        with open(form_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process form filling
        form_result = await form_filler.process_form_filling(form_path, user_id)
        
        # Save filled form record to Supabase
        await supabase_client.create_filled_form(
            user_id=user_id,
            original_form_name=file.filename,
            filled_form_url=form_result['filled_form_url']
        )
        
        logger.info(f"Form processed successfully - user_id: {user_id}, form_name: {file.filename}")
        
        return form_result
    
    except Exception as e:
        logger.error(f"Form upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{filename}")
async def download_file(filename: str, user_id: str = Depends(get_current_user)):
    """Download a filled form or uploaded document"""
    try:
        # Check in filled forms directory first
        filled_form_path = os.path.join(settings.UPLOAD_DIR, 'filled_forms', filename)
        if os.path.exists(filled_form_path):
            return FileResponse(
                filled_form_path,
                media_type='application/pdf',
                filename=filename
            )
        
        # Check in regular uploads
        upload_path = os.path.join(settings.UPLOAD_DIR, filename)
        if os.path.exists(upload_path):
            return FileResponse(upload_path, filename=filename)
        
        raise HTTPException(status_code=404, detail="File not found")
    
    except Exception as e:
        logger.error(f"File download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{doc_id}/download")
async def download_document_by_id(
    doc_id: str,
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None)
):
    """Download a document by its doc_id"""
    try:
        logger.info(f"Download request for doc_id: {doc_id}, user_id: {user_id}")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not provided")
        
        # First verify the document exists and belongs to the user
        if supabase_client.has_supabase_credentials:
            try:
                client = supabase_client.admin_client if supabase_client.admin_client else supabase_client.client
                doc_result = client.table('uploaded_documents').select('*').eq('doc_id', doc_id).eq('user_id', user_id).execute()
                
                if not doc_result.data:
                    raise HTTPException(status_code=404, detail="Document not found or access denied")
                
                document = doc_result.data[0]
                logger.info(f"Found document: {document['filename']} for download")
                
            except Exception as e:
                logger.error(f"Failed to verify document ownership: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to verify document access")
        else:
            # Fallback to demo storage
            user_docs = demo_documents.get(user_id, [])
            document = None
            for doc in user_docs:
                if doc['doc_id'] == doc_id:
                    document = doc
                    break
            
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
        
        # Look for the physical file
        import glob
        
        # Try Supabase Storage first
        if supabase_client.has_supabase_credentials:
            try:
                # Get the file from Supabase Storage
                # Search for files that match this doc_id (they're stored with UUID names)
                possible_files = glob.glob(os.path.join(settings.UPLOAD_DIR, f"{doc_id}*"))
                
                if possible_files:
                    # Get the original filename from the local file to determine extension
                    local_file_path = possible_files[0]
                    file_extension = os.path.splitext(local_file_path)[1]
                    safe_filename = f"{doc_id}{file_extension}"
                    
                    # Download from Supabase Storage
                    file_content = supabase_client.admin_client.storage.from_('documents').download(safe_filename)
                    
                    if file_content:
                        logger.info(f"Public file retrieved from Supabase Storage: {safe_filename}")
                        
                        # Determine the appropriate media type
                        media_type = 'application/octet-stream'  # Default
                        if file_extension == '.pdf':
                            media_type = 'application/pdf'
                        elif file_extension in ['.jpg', '.jpeg']:
                            media_type = 'image/jpeg'
                        elif file_extension == '.png':
                            media_type = 'image/png'
                        
                        # Add CORS headers for SimplePDF
                        headers = {
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Methods": "GET, OPTIONS",
                            "Access-Control-Allow-Headers": "*",
                            "Access-Control-Expose-Headers": "Content-Length, Content-Type",
                            "Cross-Origin-Resource-Policy": "cross-origin",
                            "Cross-Origin-Embedder-Policy": "unsafe-none"
                        }
                        
                        # Return the file content as a response
                        return Response(
                            content=file_content,
                            media_type=media_type,
                            headers=headers
                        )
                    else:
                        logger.warning(f"Public file not found in Supabase Storage: {safe_filename}")
                        
                else:
                    logger.warning(f"No local file found to determine extension for doc_id: {doc_id}")
                    
            except Exception as storage_error:
                logger.warning(f"Failed to retrieve public file from Supabase Storage: {str(storage_error)}")
                # Fall back to local storage
        
        # Fallback to local storage
        # Search for files that match this doc_id (they're stored with UUID names)
        possible_files = glob.glob(os.path.join(settings.UPLOAD_DIR, f"{doc_id}*"))
        
        if not possible_files:
            logger.error(f"No physical file found for doc_id: {doc_id}")
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # Use the first matching file
        file_path = possible_files[0]
        
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # Determine the appropriate media type
        file_extension = os.path.splitext(file_path)[1].lower()
        media_type = 'application/octet-stream'  # Default
        
        if file_extension == '.pdf':
            media_type = 'application/pdf'
        elif file_extension in ['.jpg', '.jpeg']:
            media_type = 'image/jpeg'
        elif file_extension == '.png':
            media_type = 'image/png'
        
        logger.info(f"Serving public file: {file_path} as {media_type}")
        
        # Add CORS headers for SimplePDF
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Expose-Headers": "Content-Length, Content-Type",
            "Cross-Origin-Resource-Policy": "cross-origin",
            "Cross-Origin-Embedder-Policy": "unsafe-none"
        }
        
        return FileResponse(
            file_path,
            media_type=media_type,
            headers=headers
        )
    
    except HTTPException:
        # Re-raise HTTPExceptions without modification
        raise
    except Exception as e:
        logger.error(f"Document download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")

@app.get("/api/documents/{doc_id}/transactions", response_model=TransactionsResponse)
async def get_document_transactions(doc_id: str, user_id: Optional[str] = Header(None, alias="X-User-ID")):
    """Fetch parsed transactions for a given document"""
    try:
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not provided")

        if not supabase_client.has_supabase_credentials:
            # If DB not configured, return empty list
            return TransactionsResponse(doc_id=doc_id, transactions=[])

        txns = await supabase_client.get_document_transactions(user_id, doc_id)
        return TransactionsResponse(doc_id=doc_id, transactions=txns)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get transactions for doc_id {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load transactions")

@app.get("/api/public/documents/{doc_id}")
async def get_public_document(
    doc_id: str,
    token: Optional[str] = None
):
    """Public endpoint for document access with temporary token"""
    try:
        logger.info(f"Public document request for doc_id: {doc_id}")
        
        # For now, we'll make this a simple public endpoint
        # In production, you'd want to implement token-based access
        
        # Try Supabase Storage first
        if supabase_client.has_supabase_credentials:
            try:
                # First, try to get document info from database to get the filename
                client = supabase_client.admin_client
                doc_result = client.table('uploaded_documents').select('filename').eq('doc_id', doc_id).execute()
                
                if doc_result.data:
                    document = doc_result.data[0]
                    filename = document['filename']
                    file_extension = os.path.splitext(filename)[1]
                    safe_filename = f"{doc_id}{file_extension}"
                    
                    logger.info(f"Found document in database: {filename}, trying Supabase Storage: {safe_filename}")
                    
                    # Download from Supabase Storage
                    file_content = supabase_client.admin_client.storage.from_('documents').download(safe_filename)
                    
                    if file_content:
                        logger.info(f"Public file retrieved from Supabase Storage: {safe_filename}")
                        
                        # Determine the appropriate media type
                        media_type = 'application/octet-stream'  # Default
                        if file_extension == '.pdf':
                            media_type = 'application/pdf'
                        elif file_extension in ['.jpg', '.jpeg']:
                            media_type = 'image/jpeg'
                        elif file_extension == '.png':
                            media_type = 'image/png'
                        
                        # Add CORS headers for SimplePDF
                        headers = {
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Methods": "GET, OPTIONS",
                            "Access-Control-Allow-Headers": "*",
                            "Access-Control-Expose-Headers": "Content-Length, Content-Type",
                            "Cross-Origin-Resource-Policy": "cross-origin",
                            "Cross-Origin-Embedder-Policy": "unsafe-none"
                        }
                        
                        # Return the file content as a response
                        return Response(
                            content=file_content,
                            media_type=media_type,
                            headers=headers
                        )
                    else:
                        logger.warning(f"Public file not found in Supabase Storage: {safe_filename}")
                        
                else:
                    logger.warning(f"Document not found in database for doc_id: {doc_id}")
                    
            except Exception as storage_error:
                logger.warning(f"Failed to retrieve public file from Supabase Storage: {str(storage_error)}")
                # Fall back to local storage
        
        # Fallback to local storage
        import glob
        
        # Search for files that match this doc_id (they're stored with UUID names)
        possible_files = glob.glob(os.path.join(settings.UPLOAD_DIR, f"{doc_id}*"))
        
        if not possible_files:
            logger.error(f"No physical file found for doc_id: {doc_id}")
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # Use the first matching file
        file_path = possible_files[0]
        
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # Determine the appropriate media type
        file_extension = os.path.splitext(file_path)[1].lower()
        media_type = 'application/octet-stream'  # Default
        
        if file_extension == '.pdf':
            media_type = 'application/pdf'
        elif file_extension in ['.jpg', '.jpeg']:
            media_type = 'image/jpeg'
        elif file_extension == '.png':
            media_type = 'image/png'
        
        logger.info(f"Serving public file from local storage: {file_path} as {media_type}")
        
        # Add CORS headers for SimplePDF
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Expose-Headers": "Content-Length, Content-Type",
            "Cross-Origin-Resource-Policy": "cross-origin",
            "Cross-Origin-Embedder-Policy": "unsafe-none"
        }
        
        return FileResponse(
            file_path,
            media_type=media_type,
            headers=headers
        )
    
    except HTTPException:
        # Re-raise HTTPExceptions without modification
        raise
    except Exception as e:
        logger.error(f"Public document access failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to access document: {str(e)}")

@app.options("/api/public/documents/{doc_id}")
async def options_public_document(doc_id: str):
    """Handle CORS preflight requests for public documents"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
        }
    )

@app.get("/api/filled-forms")
async def get_filled_forms(user_id: Optional[str] = Header(None, alias="X-User-ID")):
    """Get all filled forms for the current user"""
    try:
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not provided")
            
        filled_forms = []
        
        # Try to get filled forms from Supabase first
        if supabase_client.has_supabase_credentials:
            try:
                filled_forms = await supabase_client.get_user_filled_forms(user_id)
                logger.info(f"Retrieved {len(filled_forms)} filled forms from Supabase for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to get filled forms from Supabase: {str(e)}")
                # Fall back to demo storage
                filled_forms = demo_filled_forms.get(user_id, [])
                logger.info(f"Retrieved {len(filled_forms)} filled forms from demo storage (fallback) for user {user_id}")
        else:
            # Use demo storage when Supabase is not available
            filled_forms = demo_filled_forms.get(user_id, [])
            logger.info(f"Retrieved {len(filled_forms)} filled forms from demo storage for user {user_id}")
            
        return {"filled_forms": filled_forms}
    except Exception as e:
        logger.error(f"Failed to get filled forms: {str(e)}")
        # Return demo storage as final fallback
        return {"filled_forms": demo_filled_forms.get(user_id, [])}

@app.post("/api/missing-field-suggestions")
async def get_missing_field_suggestions(
    missing_fields: List[str],
    user_id: str = Depends(get_current_user)
):
    """Get AI suggestions for missing form fields"""
    try:
        suggestions = await form_filler.get_missing_field_suggestions(missing_fields, user_id)
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Failed to get field suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_user_stats(user_id: Optional[str] = Header(None, alias="X-User-ID")):
    """Get user statistics"""
    try:
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not provided")
        
        documents = []
        filled_forms = []
        
        # Get documents and forms for stats
        if supabase_client.has_supabase_credentials:
            try:
                documents = await supabase_client.get_user_documents(user_id)
                filled_forms = await supabase_client.get_user_filled_forms(user_id)
                logger.info(f"Retrieved stats from Supabase - {len(documents)} docs, {len(filled_forms)} forms")
            except Exception as e:
                logger.warning(f"Failed to get stats from Supabase: {str(e)}")
                # Fallback to demo storage
                documents = demo_documents.get(user_id, [])
                filled_forms = demo_filled_forms.get(user_id, [])
                logger.info(f"Retrieved stats from demo storage (fallback) - {len(documents)} docs, {len(filled_forms)} forms")
        else:
            # Fallback for demo mode when database is not configured
            documents = demo_documents.get(user_id, [])
            filled_forms = demo_filled_forms.get(user_id, [])
            logger.info(f"Retrieved stats from demo storage - {len(documents)} docs, {len(filled_forms)} forms")
        
        return {
            "total_documents": len(documents),
            "total_filled_forms": len(filled_forms),
            "recent_documents": documents[:5] if documents else [],
            "recent_filled_forms": filled_forms[:5] if filled_forms else []
        }
    except Exception as e:
        logger.error(f"Failed to get user stats: {str(e)}")
        # Return default stats for demo mode
        return {
            "total_documents": 0,
            "total_filled_forms": 0,
            "recent_documents": [],
            "recent_filled_forms": []
        }

@app.post("/api/analyze-web-form")
async def analyze_web_form(request: WebFormAnalysisRequest):
    """Analyze a web form and extract field information"""
    try:
        form_analysis = await web_form_service.analyze_web_form(
            url=request.url,
            html_content=request.html_content
        )
        
        logger.info(f"Web form analyzed - URL: {request.url}, forms_found: {form_analysis['forms_count']}")
        return form_analysis
    
    except Exception as e:
        logger.error(f"Web form analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-web-autofill")
async def generate_web_autofill(
    request: WebFormAutofillRequest,
    user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """Generate autofill data for web form"""
    try:
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not provided")
        
        # Analyze the form first
        form_analysis = await web_form_service.analyze_web_form(request.url, request.html_content)
        
        # Generate autofill data
        autofill_data = await web_form_service.generate_autofill_data(form_analysis, user_id)
        
        logger.info(f"Web autofill generated - user_id: {user_id}, URL: {request.url}")
        
        return {
            "form_analysis": form_analysis,
            "autofill_data": autofill_data,
            "url": request.url
        }
        
    except Exception as e:
        logger.error(f"Failed to generate web autofill: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/match-field", response_model=FieldMatchResponse)
async def match_form_field(
    request: FieldMatchRequest,
    user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """Match a single form field to user data using semantic search"""
    try:
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not provided")
        
        # Create comprehensive field context
        field_context = f"{request.field_context} {request.placeholder}".strip()
        
        # Use RAG service to match the field
        match_result = await rag_service.match_form_field(
            field_label=request.field_label,
            field_type=request.field_type,
            field_context=field_context,
            user_id=user_id
        )
        
        # Get additional suggestions
        suggestions = []
        if match_result['matched']:
            # Get other potential matches
            field_matches = await rag_service.search_field_matches(
                request.field_label, user_id, request.field_type, top_k=3
            )
            
            suggestions = [
                {
                    'value': match['field_value'],
                    'confidence': match['confidence'],
                    'source': match['filename']
                }
                for match in field_matches[:3]
            ]
        
        response = FieldMatchResponse(
            matched=match_result['matched'],
            confidence=match_result['confidence'],
            value=match_result['match']['value'] if match_result['match'] else None,
            field_type=match_result['match']['field_type'] if match_result['match'] else None,
            source=match_result['match']['source'] if match_result['match'] else None,
            suggestions=suggestions
        )
        
        logger.info(f"Field matched - user_id: {user_id}, field: {request.field_label}, matched: {response.matched}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to match field: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/match-fields-bulk")
async def match_fields_bulk(
    request: BulkFieldMatchRequest,
    user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """Match multiple form fields at once for better performance"""
    try:
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not provided")
        
        matched_fields = {}
        
        for field_info in request.fields:
            field_label = field_info.get('label', '')
            field_type = field_info.get('type', 'text')
            field_context = field_info.get('context', '')
            field_name = field_info.get('name', field_label)
            
            if field_label:
                # Match the field
                match_result = await rag_service.match_form_field(
                    field_label=field_label,
                    field_type=field_type,
                    field_context=field_context,
                    user_id=user_id
                )
                
                matched_fields[field_name] = {
                    'matched': match_result['matched'],
                    'confidence': match_result['confidence'],
                    'value': match_result['match']['value'] if match_result['match'] else None,
                    'field_type': match_result['match']['field_type'] if match_result['match'] else None,
                    'source': match_result['match']['source'] if match_result['match'] else None
                }
        
        logger.info(f"Bulk field matching completed - user_id: {user_id}, fields: {len(request.fields)}, matched: {sum(1 for f in matched_fields.values() if f['matched'])}")
        
        return {
            "matched_fields": matched_fields,
            "total_fields": len(request.fields),
            "matched_count": sum(1 for f in matched_fields.values() if f['matched'])
        }
        
    except Exception as e:
        logger.error(f"Failed to match fields bulk: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bookmarklet")
async def bookmarklet_page():
    """Display the bookmarklet in a user-friendly HTML page"""
    try:
        user_id = "demo-user"
        
        # Generate the smart bookmarklet (complete JavaScript)
        smart_bookmarklet = f"""javascript:(function(){{
const API_BASE='http://localhost:8000';const USER_ID='{user_id}';
function detectFieldType(e){{const t=((e.name||'')+(e.id||'')+(e.placeholder||'')+(e.labels?.[0]?.textContent||'')).toLowerCase();return e.type==='email'||t.includes('email')?'email':e.type==='tel'||t.includes('phone')||t.includes('tel')?'phone':t.includes('first')&&t.includes('name')?'first_name':t.includes('last')&&t.includes('name')?'last_name':t.includes('name')&&!t.includes('user')&&!t.includes('company')?'full_name':t.includes('address')||t.includes('street')?'address':t.includes('city')?'city':t.includes('state')||t.includes('province')?'state':t.includes('zip')||t.includes('postal')?'zip_code':t.includes('linkedin')?'linkedin':t.includes('github')?'github':t.includes('website')||t.includes('portfolio')?'website':e.tagName==='TEXTAREA'||t.includes('cover')||t.includes('letter')?'cover_letter':t.includes('skill')?'skills':t.includes('experience')?'experience':'text'}}
function getFieldLabel(e){{if(e.labels&&e.labels[0])return e.labels[0].textContent.trim();const c=e.closest('label');if(c)return c.textContent.replace(e.value||'','').trim();const p=e.previousElementSibling;if(p&&['LABEL','SPAN','DIV','P'].includes(p.tagName)){{const t=p.textContent.trim();if(t.length<100)return t}}return e.placeholder||e.name||'Field'}}
async function fillFormWithAI(){{try{{const s=document.createElement('div');s.id='ai-autofill-status';s.style.cssText='position:fixed;top:20px;right:20px;z-index:10000;background:linear-gradient(135deg,#007cba,#0056b3);color:white;padding:15px 20px;border-radius:8px;font-family:-apple-system,BlinkMacSystemFont,sans-serif;font-size:14px;font-weight:500;box-shadow:0 4px 20px rgba(0,0,0,0.3);max-width:300px;min-width:200px;';s.textContent='🤖 Scanning form fields...';document.body.appendChild(s);
const fields=Array.from(document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="file"]),textarea,select')).filter(e=>e.offsetParent!==null).map(e=>({{element:e,name:e.name||e.id||'field_'+Date.now(),label:getFieldLabel(e),type:detectFieldType(e),context:e.placeholder||''}}));
if(fields.length===0){{s.textContent='❌ No form fields found';setTimeout(()=>s.remove(),3000);return}}
s.textContent='🔍 Found '+fields.length+' fields. Getting your data...';
const apiFields=fields.map(f=>({{name:f.name,label:f.label,type:f.type,context:f.context}}));
const response=await fetch(API_BASE+'/api/match-fields-bulk',{{method:'POST',headers:{{'Content-Type':'application/json','X-User-ID':USER_ID}},body:JSON.stringify({{fields:apiFields,user_id:USER_ID}})}});
if(!response.ok)throw new Error('API error: '+response.status);
const result=await response.json();const matches=result.matched_fields;let filled=0;
for(const field of fields){{const match=matches[field.name];if(match&&match.matched&&match.confidence>0.3){{try{{if(field.element.tagName==='SELECT'){{const option=Array.from(field.element.options).find(opt=>opt.text.toLowerCase().includes(match.value.toLowerCase())||opt.value.toLowerCase().includes(match.value.toLowerCase()));if(option){{field.element.value=option.value;filled++}}}}else{{field.element.value=match.value;field.element.dispatchEvent(new Event('input',{{bubbles:true}}));field.element.dispatchEvent(new Event('change',{{bubbles:true}}));filled++}}}}catch(err){{console.warn('Error filling field:',field.label,err)}}}}}}
s.innerHTML='<div style="font-weight:600;margin-bottom:8px;">✅ Autofill Complete!</div><div style="font-size:12px;opacity:0.9;">Filled '+filled+' of '+fields.length+' fields with your PDF data</div><div style="font-size:11px;margin-top:8px;opacity:0.8;">Using AI-extracted data from your resume</div>';
setTimeout(()=>{{s.style.transform='translateX(100%)';setTimeout(()=>s.remove(),300)}},4000)}}catch(error){{console.error('Autofill error:',error);const s=document.getElementById('ai-autofill-status')||document.createElement('div');s.style.cssText='position:fixed;top:20px;right:20px;z-index:10000;background:#dc2626;color:white;padding:15px 20px;border-radius:8px;font-family:-apple-system,BlinkMacSystemFont,sans-serif;font-size:14px;';s.textContent='❌ Error: Could not connect to AI service';if(!document.getElementById('ai-autofill-status'))document.body.appendChild(s);setTimeout(()=>s.remove(),4000)}}}}
fillFormWithAI()}})();"""
        
        # Create a compact fallback bookmarklet
        simple_bookmarklet = """javascript:(function(){
const d={email:'ozhorov@gmail.com',name:'AIBEK OZHOROV',phone:'(347) 466-0699',address:'Brooklyn, NY'};
function f(){let c=0;document.querySelectorAll('input,textarea').forEach(e=>{try{const t=(e.name+e.id+e.placeholder).toLowerCase();let k='';if(t.includes('email'))k='email';else if(t.includes('name')&&!t.includes('user'))k='name';else if(t.includes('phone')||t.includes('tel'))k='phone';else if(t.includes('address')||t.includes('location'))k='address';if(k&&d[k]){e.value=d[k];c++;}}catch(err){}});return c;}
alert(f()>0?'🤖 Filled '+f()+' fields!':'🤖 No fields found');
})();"""
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Autofill Bookmarklet</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
            background: #f9f9f9;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #007cba;
            margin-bottom: 10px;
        }}
        .bookmarklet-option {{
            margin: 30px 0;
            padding: 20px;
            border-radius: 8px;
            border: 2px solid #e5e7eb;
        }}
        .ai-powered {{
            border-color: #007cba;
            background: #f0f9ff;
        }}
        .simple-fallback {{
            background: #f8f9fa;
            border-color: #6b7280;
        }}
        .option-header {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }}
        .badge {{
            background: #007cba;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 15px;
        }}
        .badge.recommended {{
            background: #10b981;
        }}
        .badge.fallback {{
            background: #6b7280;
        }}
        .bookmarklet-button {{
            display: inline-block;
            background: linear-gradient(135deg, #007cba, #0056b3);
            color: white;
            padding: 15px 25px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
            font-size: 16px;
            margin: 20px 0;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,124,186,0.3);
            cursor: grab;
        }}
        .bookmarklet-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,124,186,0.4);
        }}
        .bookmarklet-button.simple {{
            background: linear-gradient(135deg, #6b7280, #4b5563);
            box-shadow: 0 4px 15px rgba(107,114,128,0.3);
        }}
        .bookmarklet-button.simple:hover {{
            box-shadow: 0 6px 20px rgba(107,114,128,0.4);
        }}
        .drag-instruction {{
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background: #e7f3ff;
            border-radius: 8px;
            border: 2px dashed #007cba;
        }}
        .features {{
            background: #f0f9ff;
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
        }}
        .features ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .features li {{
            margin: 5px 0;
            color: #374151;
        }}
        .personal-data {{
            background: #e8f5e8;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #28a745;
        }}
        .code-box {{
            background: #f1f3f4;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 11px;
            margin: 15px 0;
            border: 1px solid #ddd;
            word-break: break-all;
            max-height: 150px;
            overflow-y: auto;
        }}
        .copy-btn {{
            background: #28a745;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            margin-left: 10px;
            font-size: 12px;
        }}
        .copy-btn:hover {{
            background: #218838;
        }}
        .vs-text {{
            text-align: center;
            margin: 20px 0;
            font-size: 18px;
            font-weight: 600;
            color: #6b7280;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Autofill Bookmarklet</h1>
        <p>Choose your preferred bookmarklet for automatically filling web forms with your data</p>
        
        <div class="personal-data">
            <h3>✅ Your Data Ready</h3>
            <p><strong>Source:</strong> AI-extracted from your uploaded PDF resume</p>
            <p><strong>Email:</strong> ozhorov@gmail.com</p>
            <p><strong>Name:</strong> AIBEK OZHOROV</p>
            <p><strong>Phone:</strong> (347) 466-0699</p>
            <p><strong>Address:</strong> Brooklyn, NY</p>
            <p><strong>+ Skills, Experience, and more extracted from your resume</strong></p>
        </div>
        
        <!-- AI-Powered Option -->
        <div class="bookmarklet-option ai-powered">
            <div class="option-header">
                <h3 style="margin: 0;">🧠 AI-Powered Bookmarklet</h3>
                <span class="badge recommended">RECOMMENDED</span>
            </div>
            
            <p><strong>Uses real data extracted from your uploaded PDFs via AI field matching API</strong></p>
            
            <div class="features">
                <h4 style="margin: 0 0 10px 0;">Features:</h4>
                <ul>
                    <li>🎯 <strong>Real Data:</strong> Uses AI-extracted fields from your actual resume</li>
                    <li>🧠 <strong>Smart Matching:</strong> Intelligently matches form fields to your data</li>
                    <li>📊 <strong>Confidence Scoring:</strong> Only fills fields with high confidence matches</li>
                    <li>🔄 <strong>Live Updates:</strong> Always uses your latest document data</li>
                    <li>📝 <strong>Comprehensive:</strong> Handles name, email, phone, skills, experience, cover letters</li>
                    <li>✨ <strong>Visual Feedback:</strong> Shows real-time status and results</li>
                </ul>
            </div>
            
            <div class="drag-instruction">
                <div style="margin-bottom: 10px;">👆 <strong>Drag this AI-powered button to your bookmarks bar</strong> 👆</div>
                <a id="smart-bookmarklet-link" class="bookmarklet-button" draggable="true">
                    🧠 AI Autofill (Smart)
                </a>
                <div style="margin-top: 10px; font-size: 14px; color: #666;">
                    <strong>This connects to your AI service to get real data from your PDFs</strong>
                </div>
            </div>
        </div>
        
        <div class="vs-text">OR</div>
        
        <!-- Simple Fallback Option -->
        <div class="bookmarklet-option simple-fallback">
            <div class="option-header">
                <h3 style="margin: 0;">⚡ Simple Bookmarklet</h3>
                <span class="badge fallback">FALLBACK</span>
            </div>
            
            <p><strong>Uses hardcoded data - works offline and on sites that block API calls</strong></p>
            
            <div class="features">
                <h4 style="margin: 0 0 10px 0;">Features:</h4>
                <ul>
                    <li>🏃‍♂️ <strong>Fast:</strong> Instant autofill without API calls</li>
                    <li>🌐 <strong>Universal:</strong> Works on any website, even with strict CSP</li>
                    <li>📱 <strong>Offline:</strong> No internet connection required</li>
                    <li>🛡️ <strong>Secure:</strong> No external requests or data transmission</li>
                    <li>⚙️ <strong>Simple:</strong> Basic field detection for common form types</li>
                </ul>
            </div>
            
            <div class="drag-instruction">
                <div style="margin-bottom: 10px;">👆 <strong>Drag this simple button to your bookmarks bar</strong> 👆</div>
                <a id="simple-bookmarklet-link" class="bookmarklet-button simple" draggable="true">
                    ⚡ AI Autofill (Simple)
                </a>
                <div style="margin-top: 10px; font-size: 14px; color: #666;">
                    <strong>Uses your basic info - works everywhere</strong>
                </div>
            </div>
        </div>
        
        <div style="margin-top: 30px; padding: 20px; background: #fef3c7; border-radius: 8px; border-left: 4px solid #f59e0b;">
            <h4 style="margin: 0 0 10px 0;">💡 How to Use</h4>
            <ol style="margin: 0; padding-left: 20px;">
                <li>Drag your preferred bookmarklet button to your browser's bookmarks bar</li>
                <li>Go to any job application or form website (like Ashby, Greenhouse, Lever, etc.)</li>
                <li>Click the bookmarklet in your bookmarks bar</li>
                <li>Watch the form get filled with your information! ✨</li>
            </ol>
        </div>
        
        <details style="margin-top: 30px;">
            <summary style="cursor: pointer; font-weight: bold; padding: 10px 0;">
                🔧 Manual Setup (if dragging doesn't work)
            </summary>
            <div style="margin: 20px 0;">
                <h4>AI-Powered Bookmarklet Code:</h4>
                <div class="code-box" id="smart-code">{smart_bookmarklet}</div>
                <button class="copy-btn" onclick="copyCode('smart')">Copy AI Code</button>
            </div>
            <div style="margin: 20px 0;">
                <h4>Simple Bookmarklet Code:</h4>
                <div class="code-box" id="simple-code">{simple_bookmarklet}</div>
                <button class="copy-btn" onclick="copyCode('simple')">Copy Simple Code</button>
            </div>
            <p style="margin-top: 15px;"><strong>Manual Setup:</strong></p>
            <ol>
                <li>Right-click your bookmarks bar → "Add bookmark"</li>
                <li>Name: <strong>AI Autofill</strong></li>
                <li>Copy one of the codes above and paste as the URL</li>
            </ol>
        </details>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666;">
            <p>🎯 <strong>Test on job sites:</strong> 
                <a href="https://jobs.ashbyhq.com/wander/121c24e0-eeff-49a8-ac56-793d2dbc9fcd/application" target="_blank" style="color: #007cba; text-decoration: none; font-weight: bold;">Ashby</a> | 
                <a href="https://jobs.lever.co/" target="_blank" style="color: #007cba; text-decoration: none; font-weight: bold;">Lever</a> | 
                <a href="https://boards.greenhouse.io/" target="_blank" style="color: #007cba; text-decoration: none; font-weight: bold;">Greenhouse</a>
            </p>
        </div>
    </div>
    
    <script>
        // Set the bookmarklet hrefs
        document.getElementById('smart-bookmarklet-link').href = `{smart_bookmarklet}`;
        document.getElementById('simple-bookmarklet-link').href = `{simple_bookmarklet}`;
        
        function copyCode(type) {{
            const code = document.getElementById(type + '-code').textContent;
            navigator.clipboard.writeText(code).then(() => {{
                const btn = event.target;
                btn.textContent = 'Copied!';
                setTimeout(() => btn.textContent = type === 'smart' ? 'Copy AI Code' : 'Copy Simple Code', 2000);
            }}).catch(() => {{
                alert('Please manually copy the code above');
            }});
        }}
        
        // Drag feedback for both buttons
        ['smart-bookmarklet-link', 'simple-bookmarklet-link'].forEach(id => {{
            const btn = document.getElementById(id);
            btn.addEventListener('dragstart', function() {{
                this.style.opacity = '0.7';
            }});
            btn.addEventListener('dragend', function() {{
                this.style.opacity = '1';
            }});
        }});
    </script>
</body>
</html>"""
        
        return HTMLResponse(content=html_content, media_type="text/html")
    
    except Exception as e:
        logger.error(f"Failed to generate bookmarklet page: {str(e)}")
        return HTMLResponse(
            content=f"<html><body><h1>Error</h1><p>Failed to generate page: {str(e)}</p></body></html>",
            status_code=500,
            media_type="text/html"
        )

@app.get("/api/generate-bookmarklet")
async def generate_bookmarklet():
    """Generate a bookmarklet for web form autofill"""
    try:
        # Create a compact, working bookmarklet
        bookmarklet_js = """javascript:(function(){
const d={email:'ozhorov@gmail.com',name:'AIBEK OZHOROV',phone:'(347) 466-0699',address:'Brooklyn, NY'};
function f(){let c=0;document.querySelectorAll('input,textarea').forEach(e=>{try{const t=(e.name+e.id+e.placeholder).toLowerCase();let k='';if(t.includes('email'))k='email';else if(t.includes('name')&&!t.includes('user'))k='name';else if(t.includes('phone')||t.includes('tel'))k='phone';else if(t.includes('address')||t.includes('location'))k='address';if(k&&d[k]){e.value=d[k];c++;}}catch(err){}});return c;}
alert(f()>0?'🤖 Filled '+f()+' fields!':'🤖 No fields found');
})();"""
        
        return JSONResponse(content={
            "bookmarklet": bookmarklet_js,
            "instructions": "Drag this bookmarklet to your bookmarks bar, then click it on any form page to auto-fill your data.",
            "personal_data": {
                "email": "ozhorov@gmail.com",
                "name": "AIBEK OZHOROV", 
                "phone": "(347) 466-0699",
                "address": "Brooklyn, NY"
            }
        })
    except Exception as e:
        logger.error(f"Bookmarklet generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/generate-smart-bookmarklet")
async def generate_smart_bookmarklet(user_id: Optional[str] = Header(None, alias="X-User-ID")):
    """Generate a smart bookmarklet that uses AI-extracted data from user documents"""
    try:
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not provided")
        
        # Create an intelligent bookmarklet that calls the field matching API
        smart_bookmarklet = f"""javascript:(function(){{
const API_BASE = 'http://localhost:8000';
const USER_ID = '{user_id}';

// Enhanced field detection and mapping
function detectFieldType(element) {{
    const text = ((element.name || '') + (element.id || '') + (element.placeholder || '') + 
                 (element.labels?.[0]?.textContent || '')).toLowerCase();
    
    if (element.type === 'email' || text.includes('email')) return 'email';
    if (element.type === 'tel' || text.includes('phone') || text.includes('tel')) return 'phone';
    if (text.includes('first') && text.includes('name')) return 'first_name';
    if (text.includes('last') && text.includes('name')) return 'last_name';
    if (text.includes('name') && !text.includes('user') && !text.includes('company')) return 'full_name';
    if (text.includes('address') || text.includes('street')) return 'address';
    if (text.includes('city')) return 'city';
    if (text.includes('state') || text.includes('province')) return 'state';
    if (text.includes('zip') || text.includes('postal')) return 'zip_code';
    if (text.includes('linkedin')) return 'linkedin';
    if (text.includes('github')) return 'github';
    if (text.includes('website') || text.includes('portfolio')) return 'website';
    if (element.tagName === 'TEXTAREA' || text.includes('cover') || text.includes('letter')) return 'cover_letter';
    if (text.includes('skill')) return 'skills';
    if (text.includes('experience')) return 'experience';
    if (text.includes('education')) return 'education';
    return 'text';
}}

function getFieldLabel(element) {{
    // Try multiple ways to get field label
    if (element.labels && element.labels[0]) return element.labels[0].textContent.trim();
    
    const closest = element.closest('label');
    if (closest) return closest.textContent.replace(element.value || '', '').trim();
    
    const prev = element.previousElementSibling;
    if (prev && ['LABEL', 'SPAN', 'DIV', 'P'].includes(prev.tagName)) {{
        const text = prev.textContent.trim();
        if (text.length < 100) return text;
    }}
    
    return element.placeholder || element.name || 'Field';
}}

async function fillFormWithAI() {{
    try {{
        // Show status
        const statusDiv = document.createElement('div');
        statusDiv.id = 'ai-autofill-status';
        statusDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 10000; background: linear-gradient(135deg, #007cba, #0056b3); color: white; padding: 15px 20px; border-radius: 8px; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; font-weight: 500; box-shadow: 0 4px 20px rgba(0,0,0,0.3); max-width: 300px; min-width: 200px;';
        statusDiv.textContent = '🤖 Scanning form fields...';
        document.body.appendChild(statusDiv);
        
        // Find form fields
        const fields = Array.from(document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="file"]), textarea, select'))
            .filter(el => el.offsetParent !== null) // Only visible elements
            .map(el => ({{
                element: el,
                name: el.name || el.id || 'field_' + Date.now(),
                label: getFieldLabel(el),
                type: detectFieldType(el),
                context: el.placeholder || '',
                selector: el.name || '#' + el.id || el.tagName.toLowerCase()
            }}));
        
        if (fields.length === 0) {{
            statusDiv.textContent = '❌ No form fields found';
            setTimeout(() => statusDiv.remove(), 3000);
            return;
        }}
        
        statusDiv.textContent = '🔍 Found ' + fields.length + ' fields. Getting your data...';
        
        // Prepare fields for API
        const apiFields = fields.map(f => ({{
            name: f.name,
            label: f.label,
            type: f.type,
            context: f.context
        }}));
        
        // Call field matching API
        const response = await fetch(API_BASE + '/api/match-fields-bulk', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
                'X-User-ID': USER_ID
            }},
            body: JSON.stringify({{
                fields: apiFields,
                user_id: USER_ID
            }})
        }});
        
        if (!response.ok) {{
            throw new Error('API error: ' + response.status);
        }}
        
        const result = await response.json();
        const matches = result.matched_fields;
        
        // Fill form fields
        let filled = 0;
        for (const field of fields) {{
            const match = matches[field.name];
            if (match && match.matched && match.confidence > 0.3) {{
                try {{
                    if (field.element.tagName === 'SELECT') {{
                        // Handle select dropdowns
                        const option = Array.from(field.element.options).find(opt => 
                            opt.text.toLowerCase().includes(match.value.toLowerCase()) ||
                            opt.value.toLowerCase().includes(match.value.toLowerCase())
                        );
                        if (option) {{
                            field.element.value = option.value;
                            filled++;
                        }}
                    }} else {{
                        // Handle input and textarea
                        field.element.value = match.value;
                        field.element.dispatchEvent(new Event('input', {{bubbles: true}}));
                        field.element.dispatchEvent(new Event('change', {{bubbles: true}}));
                        filled++;
                    }}
                }} catch (err) {{
                    console.warn('Error filling field:', field.label, err);
                }}
            }}
        }}
        
        // Show results
        statusDiv.innerHTML = '<div style="font-weight: 600; margin-bottom: 8px;">✅ Autofill Complete!</div><div style="font-size: 12px; opacity: 0.9;">Filled ' + filled + ' of ' + fields.length + ' fields with your PDF data</div><div style="font-size: 11px; margin-top: 8px; opacity: 0.8;">Using AI-extracted data from your resume</div>';
        
        // Auto-remove status after delay
        setTimeout(() => {{
            statusDiv.style.transform = 'translateX(100%)';
            setTimeout(() => statusDiv.remove(), 300);
        }}, 4000);
        
    }} catch (error) {{
        console.error('Autofill error:', error);
        const statusDiv = document.getElementById('ai-autofill-status') || document.createElement('div');
        statusDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 10000; background: #dc2626; color: white; padding: 15px 20px; border-radius: 8px; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px;';
        statusDiv.textContent = '❌ Error: Could not connect to AI service';
        if (!document.getElementById('ai-autofill-status')) document.body.appendChild(statusDiv);
        setTimeout(() => statusDiv.remove(), 4000);
    }}
}}

fillFormWithAI();
}})();"""
        
        return JSONResponse(content={
            "bookmarklet": smart_bookmarklet,
            "description": "Smart AI bookmarklet that uses your uploaded document data",
            "features": [
                "Uses AI-extracted data from your PDFs",
                "Intelligent field type detection",
                "Real-time API integration", 
                "Confidence-based matching",
                "Works on any website"
            ],
            "user_id": user_id
        })
    except Exception as e:
        logger.error(f"Smart bookmarklet generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable (for Render) or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG
    ) 