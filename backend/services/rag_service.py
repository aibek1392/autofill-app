from typing import List, Dict, Any, Optional
import logging
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import Document
from langchain.callbacks import LangChainTracer
from langsmith import traceable
import asyncio
from config import settings
from database.pinecone_client import pinecone_client
from database.supabase_client import supabase_client
import uuid

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        # Check if OpenAI API key is available
        self.has_openai_key = bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "")
        
        if self.has_openai_key:
            # Initialize OpenAI embeddings
            self.embeddings = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            # Initialize ChatOpenAI
            self.llm = ChatOpenAI(
                model=settings.CHAT_MODEL,
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS,
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            # Initialize LangSmith tracer
            self.tracer = LangChainTracer(
                project_name=settings.LANGCHAIN_PROJECT
            ) if settings.LANGCHAIN_TRACING_V2 else None
        else:
            logger.warning("OpenAI API key not found - AI features will be limited")
            self.embeddings = None
            self.llm = None
            self.tracer = None
    
    @traceable
    async def generate_embeddings(self, chunks: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """Generate embeddings for document chunks"""
        if not self.has_openai_key:
            logger.warning("Cannot generate embeddings - OpenAI API key not configured")
            return []
        
        try:
            # Extract text from chunks
            texts = [chunk['text'] for chunk in chunks]
            
            # Generate embeddings
            embeddings = await self.embeddings.aembed_documents(texts)
            
            # Prepare vectors for Pinecone
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = pinecone_client.generate_vector_id(chunk['doc_id'], chunk['chunk_index'])
                
                vectors.append({
                    'id': vector_id,
                    'embedding': embedding,
                    'metadata': {
                        'user_id': user_id,
                        'doc_id': chunk['doc_id'],
                        'chunk_id': chunk['chunk_id'],
                        'text': chunk['text'],
                        'filename': chunk['metadata']['filename'],
                        'file_type': chunk['metadata']['file_type'],
                        'chunk_index': chunk['chunk_index']
                    }
                })
            
            logger.info(f"Embeddings generated successfully - user_id: {user_id}, chunks: {len(chunks)}, vectors: {len(vectors)}")
            
            return vectors
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise
    
    @traceable
    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a query"""
        try:
            embedding = await self.embeddings.aembed_query(query)
            logger.info(f"Query embedded successfully - query_length: {len(query)}")
            return embedding
        except Exception as e:
            logger.error(f"Failed to embed query: {str(e)}")
            raise
    
    @traceable
    async def search_documents(self, query: str, user_id: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search for relevant documents using vector similarity"""
        try:
            # Generate query embedding
            query_embedding = await self.embed_query(query)
            
            # Search in Pinecone for document chunks
            results = await pinecone_client.search_similar(
                query_embedding=query_embedding,
                user_id=user_id,
                top_k=top_k
            )
            
            # Format document chunk results
            formatted_results = []
            for result in results:
                metadata = result['metadata']
                # Include document chunks (not field vectors) for document search
                if metadata.get('type') != 'field' and 'text' in metadata:
                    print(f"[SIMILARITY CHUNK] Score: {result['score']:.3f} | File: {metadata.get('filename')} | Text: {metadata['text'][:200]}...")
                    formatted_results.append({
                        'text': metadata['text'],
                        'score': result['score'],
                        'filename': metadata['filename'],
                        'doc_id': metadata['doc_id'],
                        'chunk_index': metadata.get('chunk_index', 0)
                    })
            
            # Also search field vectors for personal information queries
            personal_info_keywords = ['email', 'name', 'phone', 'address', 'contact', 'information', 'who are you', 'about me', 'my', 'tell me about', 'skills', 'programming', 'languages', 'experience', 'work', 'job', 'education', 'linkedin', 'what do', 'what are', 'what is']
            is_personal_query = any(keyword in query.lower() for keyword in personal_info_keywords)
            
            if is_personal_query:
                # Extract field type from query for more targeted search
                field_type_hints = {
                    'email': ['email', 'e-mail', 'mail'],
                    'phone': ['phone', 'number', 'tel', 'telephone', 'mobile'],
                    'full_name': ['name'],
                    'address': ['address', 'location'],
                    'skills': ['skills', 'programming', 'languages', 'tech'],
                    'experience': ['experience', 'work', 'job', 'years']
                }
                
                detected_field_type = None
                query_lower = query.lower()
                
                for field_type, keywords in field_type_hints.items():
                    if any(keyword in query_lower for keyword in keywords):
                        detected_field_type = field_type
                        break
                
                # Search field vectors for personal information
                if detected_field_type:
                    # Search specifically for the detected field type
                    field_results = await self.search_field_matches(query, user_id, field_type=detected_field_type, top_k=5)
                else:
                    # General field search
                    field_results = await self.search_field_matches(query, user_id, top_k=5)
                
                # If the query mentions a specific person's name, prioritize their information
                person_names = ['aibek', 'ozhorov', 'aman', 'asangulov']
                mentioned_person = None
                
                for name in person_names:
                    if name in query_lower:
                        mentioned_person = name
                        break
                
                # Filter and reorder field results based on mentioned person
                if mentioned_person:
                    # Separate results by person and prioritize mentioned person
                    prioritized_results = []
                    other_results = []
                    
                    for field_result in field_results:
                        # Check if the result's filename or context mentions the person
                        result_text = (field_result.get('filename', '') + ' ' + 
                                     field_result.get('context', '') + ' ' + 
                                     str(field_result.get('field_value', ''))).lower()
                        
                        if mentioned_person in result_text:
                            prioritized_results.append(field_result)
                        else:
                            other_results.append(field_result)
                    
                    # Use prioritized results first, then others
                    field_results = prioritized_results + other_results[:max(0, 5-len(prioritized_results))]
                
                # Add field results as formatted text entries
                for field_result in field_results:
                    field_text = f"**{field_result['field_type'].title()}**: {field_result['field_value']}"
                    if field_result.get('context'):
                        field_text += f" (Context: {field_result['context'][:100]}...)"
                    
                    formatted_results.append({
                        'text': field_text,
                        'score': field_result['confidence'],
                        'filename': field_result['filename'],
                        'doc_id': field_result['doc_id'],
                        'chunk_index': f"field_{field_result['field_type']}"
                    })
                    print(f"[FIELD MATCH] Score: {field_result['confidence']:.3f} | Type: {field_result['field_type']} | Value: {field_result['field_value']}")
            
            logger.info(f"Document search completed - user_id: {user_id}, query: {query}, results_found: {len(formatted_results)}")
            
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to search documents: {str(e)}")
            raise
    
    @traceable
    async def generate_response(self, query: str, context: List[Dict[str, Any]], user_id: str) -> Dict[str, Any]:
        """Generate response using RAG with LLM"""
        if not self.has_openai_key:
            return {
                'answer': f"I cannot process your query '{query}' because OpenAI API key is not configured. Please add your API keys to enable AI features.",
                'sources': [],
                'context_used': 0,
                'user_id': user_id
            }
        
        try:
            # Prepare context string
            context_str = "\n\n".join([
                f"Source: {doc['filename']} (Relevance: {doc['score']:.2f})\n{doc['text']}"
                for doc in context
            ])
            
            # Prepare prompt
            prompt = f"""You are an AI assistant helping with document analysis and form filling. 
Use the following context from the user's documents to answer their question accurately.

Context from user documents:
{context_str}

User question: {query}

Instructions:
1. Answer based primarily on the provided context
2. If the context doesn't contain enough information, clearly state what's missing
3. Be specific and cite which document the information comes from when possible
4. For form filling requests, extract the exact values needed

Answer:"""

            # Generate response with callbacks
            callbacks = [self.tracer] if self.tracer else None
            response = await self.llm.ainvoke(prompt, config={'callbacks': callbacks} if callbacks else {})
            
            result = {
                'answer': response.content,
                'sources': [{'filename': doc['filename'], 'score': doc['score']} for doc in context],
                'context_used': len(context),
                'user_id': user_id
            }
            
            logger.info(f"Response generated successfully - user_id: {user_id}, context_docs: {len(context)}, response_length: {len(response.content)}")
            
            return result
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            raise
    
    @traceable
    async def extract_form_fields(self, form_text: str, user_documents_context: str) -> Dict[str, Any]:
        """Extract and populate form fields using AI"""
        try:
            prompt = f"""You are an AI assistant specialized in form filling. 
Analyze the following form and extract all fillable fields, then populate them using the provided user data.

Form content:
{form_text}

User data context:
{user_documents_context}

Instructions:
1. Identify all form fields (name, address, phone, email, dates, etc.)
2. For each field, try to find matching information from the user data
3. If information is missing, mark the field as "MISSING" 
4. Return results in JSON format

Expected output format:
{{
    "filled_fields": {{
        "field_name": "extracted_value",
        "another_field": "MISSING"
    }},
    "confidence_scores": {{
        "field_name": 0.95,
        "another_field": 0.0
    }},
    "missing_fields": ["list", "of", "missing", "fields"],
    "field_mapping": {{
        "field_name": "source_document_reference"
    }}
}}

Respond with valid JSON only:"""

            # Generate response
            callbacks = [self.tracer] if self.tracer else None
            response = await self.llm.ainvoke(prompt, config={'callbacks': callbacks} if callbacks else {})
            
            # Parse JSON response
            import json
            try:
                result = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback if AI doesn't return valid JSON
                result = {
                    "filled_fields": {},
                    "confidence_scores": {},
                    "missing_fields": [],
                    "field_mapping": {}
                }
            
            logger.info(f"Form fields extracted successfully - filled_fields: {len(result.get('filled_fields', {}))}, missing_fields: {len(result.get('missing_fields', []))}")
            
            return result
        except Exception as e:
            logger.error(f"Failed to extract form fields: {str(e)}")
            raise
    
    async def process_document_pipeline(self, chunks: List[Dict[str, Any]], user_id: str, doc_id: str, document: Optional[Dict[str, Any]] = None) -> bool:
        """Process document through complete RAG pipeline"""
        try:
            # Generate standard text chunk embeddings
            vectors = await self.generate_embeddings(chunks, user_id)
            
            # Generate field-specific embeddings if document is provided
            field_vectors = []
            if document:
                field_vectors = await self.generate_field_embeddings(document, user_id)
            
            # Combine all vectors
            all_vectors = vectors + field_vectors
            
            # Upsert to Pinecone
            if all_vectors:
                await pinecone_client.upsert_embeddings(all_vectors)
            
            # Store chunk metadata in Supabase (skip if it fails)
            if supabase_client.has_supabase_credentials:
                try:
                    for chunk in chunks:
                        chunk_data = {
                            'chunk_id': chunk['chunk_id'],
                            'doc_id': doc_id,
                            'user_id': user_id,
                            'text': chunk['text'],
                            'chunk_index': chunk['chunk_index'],
                            'metadata': chunk['metadata']
                        }
                        await supabase_client.create_vector_chunk(chunk_data)
                except Exception as e:
                    logger.warning(f"Failed to store chunk metadata in Supabase (continuing anyway): {str(e)}")
            
            logger.info(f"Document pipeline completed - user_id: {user_id}, doc_id: {doc_id}, chunks: {len(chunks)}, field_vectors: {len(field_vectors)}")
            return True
        except Exception as e:
            logger.error(f"Failed to process document pipeline: {str(e)}")
            raise
    
    @traceable
    async def generate_field_embeddings(self, document: Dict[str, Any], user_id: str) -> List[Dict[str, Any]]:
        """Generate embeddings for extracted fields from a document"""
        if not self.has_openai_key:
            logger.warning("Cannot generate field embeddings - OpenAI API key not configured")
            return []
        
        try:
            field_vectors = []
            structured_fields = document.get('structured_fields', {})
            
            for field_type, field_matches in structured_fields.items():
                for i, field_match in enumerate(field_matches):
                    # Create embedding text that includes field type, value, and context
                    embedding_text = f"{field_type}: {field_match['value']} | Context: {field_match['context']}"
                    
                    # Generate embedding
                    embedding = await self.embeddings.aembed_query(embedding_text)
                    
                    # Create vector ID for field
                    vector_id = f"{document['doc_id']}_field_{field_type}_{i}_{uuid.uuid4().hex[:8]}"
                    
                    field_vectors.append({
                        'id': vector_id,
                        'embedding': embedding,
                        'metadata': {
                            'user_id': user_id,
                            'doc_id': document['doc_id'],
                            'type': 'field',
                            'field_type': field_type,
                            'field_value': field_match['value'],
                            'field_context': field_match['context'],
                            'confidence': field_match['confidence'],
                            'filename': document['filename'],
                            'file_type': document['file_type']
                        }
                    })
            
            logger.info(f"Field embeddings generated - user_id: {user_id}, doc_id: {document['doc_id']}, field_vectors: {len(field_vectors)}")
            return field_vectors
            
        except Exception as e:
            logger.error(f"Failed to generate field embeddings: {str(e)}")
            raise
    
    @traceable
    async def search_field_matches(self, field_query: str, user_id: str, field_type: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for field matches using semantic similarity"""
        try:
            # Generate query embedding
            query_embedding = await self.embed_query(field_query)
            
            # Build filter for field-specific search
            search_filter = {'user_id': user_id, 'type': 'field'}
            
            # Map common field types to stored field types for better matching
            field_type_mappings = {
                'tel': ['phone'],
                'phone': ['phone'],
                'email': ['email'],
                'text': ['name', 'first_name', 'last_name', 'full_name', 'experience'],
                'textarea': ['skills', 'experience', 'cover_letter'],
                'url': ['linkedin', 'github', 'website'],
                'date': ['date'],
                'address': ['address'],
                'education': ['education'],
                'name': ['full_name', 'name', 'first_name', 'last_name']
            }
            
            # Try multiple field type variations if field_type is provided
            search_attempts = []
            if field_type and field_type in field_type_mappings:
                # Try mapped field types
                for mapped_type in field_type_mappings[field_type]:
                    search_attempts.append(mapped_type)
            else:
                # Try the original field type
                if field_type:
                    search_attempts.append(field_type)
                else:
                    # No field type filter - search all fields
                    search_attempts.append(None)
            
            all_results = []
            for attempt_type in search_attempts:
                attempt_filter = search_filter.copy()
                if attempt_type:
                    attempt_filter['field_type'] = attempt_type
            
                # Search in Pinecone for field matches
                results = await pinecone_client.search_similar_with_filter(
                    query_embedding=query_embedding,
                    filter=attempt_filter,
                    top_k=top_k
                )
                
                # Add results to combined list
                all_results.extend(results)
            
            # Remove duplicates and sort by score
            seen_ids = set()
            unique_results = []
            for result in sorted(all_results, key=lambda x: x['score'], reverse=True):
                if result['id'] not in seen_ids:
                    seen_ids.add(result['id'])
                    unique_results.append(result)
                    if len(unique_results) >= top_k:
                        break
            
            # Format field results
            formatted_results = []
            for result in unique_results:
                metadata = result['metadata']
                formatted_results.append({
                    'field_type': metadata['field_type'],
                    'field_value': metadata['field_value'],
                    'confidence': result['score'] * metadata['confidence'],  # Combined confidence
                    'context': metadata['field_context'],
                    'filename': metadata['filename'],
                    'doc_id': metadata['doc_id'],
                    'similarity_score': result['score'],
                    'extraction_confidence': metadata['confidence']
                })
            
            logger.info(f"Field search completed - user_id: {user_id}, query: {field_query}, results_found: {len(formatted_results)}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search field matches: {str(e)}")
            raise
    
    @traceable
    async def match_form_field(self, field_label: str, field_type: str, field_context: str, user_id: str) -> Dict[str, Any]:
        """Match a specific form field to user data using AI and semantic search"""
        try:
            # Create comprehensive search query
            search_queries = [
                field_label,
                f"{field_type} {field_label}",
                f"{field_label} {field_context}",
                field_type
            ]
            
            best_match = None
            best_confidence = 0.0
            
            # Try multiple search strategies
            for query in search_queries:
                # Search for field matches
                field_matches = await self.search_field_matches(query, user_id, field_type, top_k=3)
                
                for match in field_matches:
                    # Calculate combined confidence score
                    label_similarity = self._calculate_label_similarity(field_label, match['field_type'])
                    combined_confidence = (match['confidence'] * 0.7) + (label_similarity * 0.3)
                    
                    if combined_confidence > best_confidence:
                        best_confidence = combined_confidence
                        best_match = {
                            'value': match['field_value'],
                            'confidence': combined_confidence,
                            'field_type': match['field_type'],
                            'source': match['filename'],
                            'context': match['context'],
                            'similarity_score': match['similarity_score'],
                            'extraction_confidence': match['extraction_confidence']
                        }
            
            # If no good match found, try general document search
            if not best_match or best_confidence < 0.3:
                doc_results = await self.search_documents(f"{field_label} {field_type}", user_id, top_k=3)
                
                if doc_results and self.has_openai_key:
                    # Use AI to extract relevant value from document context
                    context_text = "\n".join([doc['text'] for doc in doc_results[:2]])
                    ai_extracted = await self._ai_extract_field_value(field_label, field_type, context_text)
                    
                    if ai_extracted and ai_extracted['confidence'] > best_confidence:
                        best_match = ai_extracted
                        best_confidence = ai_extracted['confidence']
            
            result = {
                'matched': best_match is not None,
                'confidence': best_confidence,
                'match': best_match,
                'field_label': field_label,
                'field_type': field_type
            }
            
            logger.info(f"Form field matched - user_id: {user_id}, field: {field_label}, matched: {result['matched']}, confidence: {best_confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to match form field: {str(e)}")
            return {
                'matched': False,
                'confidence': 0.0,
                'match': None,
                'field_label': field_label,
                'field_type': field_type,
                'error': str(e)
            }
    
    def _calculate_label_similarity(self, field_label: str, field_type: str) -> float:
        """Calculate similarity between field label and extracted field type"""
        try:
            label_lower = field_label.lower()
            type_lower = field_type.lower()
            
            # Direct match
            if type_lower in label_lower or label_lower in type_lower:
                return 1.0
            
            # Common mappings
            mappings = {
                'email': ['email', 'e-mail', 'mail', 'electronic mail'],
                'phone': ['phone', 'tel', 'telephone', 'mobile', 'cell'],
                'name': ['name', 'full name', 'fullname'],
                'address': ['address', 'street', 'location'],
                'linkedin': ['linkedin', 'linked-in'],
                'website': ['website', 'url', 'site', 'portfolio'],
                'github': ['github', 'git'],
                'experience': ['experience', 'work', 'employment', 'job'],
                'education': ['education', 'school', 'university', 'degree'],
                'skills': ['skills', 'abilities', 'technologies']
            }
            
            if field_type in mappings:
                for keyword in mappings[field_type]:
                    if keyword in label_lower:
                        return 0.8
            
            return 0.0
            
        except Exception:
            return 0.0
    
    @traceable
    async def _ai_extract_field_value(self, field_label: str, field_type: str, context: str) -> Optional[Dict[str, Any]]:
        """Use AI to extract field value from document context"""
        if not self.has_openai_key:
            return None
            
        try:
            prompt = f"""Extract the value for the form field "{field_label}" (type: {field_type}) from the following text.

Context:
{context}

Instructions:
1. Look for information that would be appropriate for a form field labeled "{field_label}"
2. Return the exact value that should be filled in the form
3. If you cannot find relevant information, respond with "NOT_FOUND"
4. Be precise and return only the value, not explanations

Field value:"""

            response = await self.llm.ainvoke(prompt)
            extracted_value = response.content.strip()
            
            if extracted_value and extracted_value != "NOT_FOUND" and len(extracted_value) > 0:
                return {
                    'value': extracted_value,
                    'confidence': 0.6,  # AI extraction confidence
                    'field_type': field_type,
                    'source': 'AI extraction from documents',
                    'context': context[:200] + '...' if len(context) > 200 else context
                }
            
            return None
            
        except Exception as e:
            logger.error(f"AI field extraction failed: {str(e)}")
            return None

# Create global instance
rag_service = RAGService() 