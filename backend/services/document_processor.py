import os
import uuid
from typing import List, Dict, Any, Optional
import logging
from PIL import Image
import pytesseract
import PyPDF2
# from pdf2image import convert_from_path  # Not installed in current setup
# import magic  # Not installed in current setup
from io import BytesIO
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import settings
import re
# from .simple_ai_extractor import simple_ai_extractor

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
        )
        
        # Field extraction patterns for common form fields
        self.field_patterns = {
            'email': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                r'email[:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
                r'e-mail[:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
            ],
            'phone': [
                r'\(?([0-9]{3})\)?\s*[-.\s\n]*([0-9]{3})[-.\s\n]*([0-9]{4})',
                r'\b\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
                r'phone[:\s]*([0-9\-\.\s\(\)\+\n]{10,})',
                r'tel[:\s]*([0-9\-\.\s\(\)\+\n]{10,})',
                r'mobile[:\s]*([0-9\-\.\s\(\)\+\n]{10,})'
            ],
            'name': [
                r'name[:\s]*([A-Za-z\s]{2,50})',
                r'full name[:\s]*([A-Za-z\s]{2,50})',
                r'first name[:\s]*([A-Za-z]{2,30})',
                r'last name[:\s]*([A-Za-z]{2,30})',
                r'firstname[:\s]*([A-Za-z]{2,30})',
                r'lastname[:\s]*([A-Za-z]{2,30})'
            ],
            'full_name': [
                # Traditional patterns first (more reliable)
                r'name[:\s]*([A-Za-z\s]{2,50})',
                r'full name[:\s]*([A-Za-z\s]{2,50})',
                # Pattern to capture names at the very top of documents (like resumes)
                r'^\s*([A-Z][A-Za-z]{2,15})\s*\n\s*([A-Z][A-Za-z]{2,15})\s*\n\s*(?:FULL|SOFTWARE|DEVELOPER|ENGINEER|MANAGER)',
                r'^\s*([A-Z][A-Za-z]{2,15}\s+[A-Z][A-Za-z]{2,15})\s*\n\s*(?:FULL|SOFTWARE|DEVELOPER|ENGINEER|MANAGER)'
            ],
            'address': [
                r'address[:\s]*([A-Za-z0-9\s,.-]{10,100})',
                r'street[:\s]*([A-Za-z0-9\s,.-]{10,100})',
                r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)',
                r'city[:\s]*([A-Za-z\s]{2,50})',
                r'state[:\s]*([A-Za-z\s]{2,30})',
                r'zip[:\s]*([0-9]{5}(?:-[0-9]{4})?)',
                r'postal[:\s]*([A-Za-z0-9\s]{5,10})'
            ],
            'linkedin': [
                r'linkedin\.com/in/([A-Za-z0-9\-]+)',
                r'linkedin[:\s]*(?:https?://)?(?:www\.)?linkedin\.com/in/([A-Za-z0-9\-]+)',
                r'linkedin profile[:\s]*([^\s\n]+)'
            ],
            'website': [
                r'website[:\s]*(https?://[^\s]+)',
                r'portfolio[:\s]*(https?://[^\s]+)',
                r'personal website[:\s]*(https?://[^\s]+)',
                r'(https?://(?:www\.)?[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s]*)?)'
            ],
            'github': [
                r'github\.com/([A-Za-z0-9\-]+)',
                r'github[:\s]*(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9\-]+)',
                r'github profile[:\s]*([^\s\n]+)'
            ],
            'skills': [
                r'skills[:\s]*([A-Za-z0-9\s,.-]{10,200})',
                r'technical skills[:\s]*([A-Za-z0-9\s,.-]{10,200})',
                r'programming languages?[:\s]*([A-Za-z0-9\s,.-]{10,200})',
                r'technologies[:\s]*([A-Za-z0-9\s,.-]{10,200})'
            ],
            'education': [
                r'education[:\s]*([A-Za-z0-9\s,.-]{10,200})',
                r'university[:\s]*([A-Za-z\s]{2,100})',
                r'college[:\s]*([A-Za-z\s]{2,100})',
                r'degree[:\s]*([A-Za-z\s]{2,100})',
                r'bachelor[:\s]*([A-Za-z\s]{2,100})',
                r'master[:\s]*([A-Za-z\s]{2,100})',
                r'phd[:\s]*([A-Za-z\s]{2,100})'
            ],
            'experience': [
                r'experience[:\s]*([A-Za-z0-9\s,.-]{10,500})',
                r'work experience[:\s]*([A-Za-z0-9\s,.-]{10,500})',
                r'employment[:\s]*([A-Za-z0-9\s,.-]{10,500})',
                r'job[:\s]*([A-Za-z0-9\s,.-]{10,200})',
                r'position[:\s]*([A-Za-z0-9\s,.-]{10,200})',
                r'company[:\s]*([A-Za-z0-9\s,.-]{2,100})'
            ],
            'date': [
                r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
                r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',
                r'date of birth[:\s]*([0-9/\-]{8,12})',
                r'dob[:\s]*([0-9/\-]{8,12})',
                r'birth date[:\s]*([0-9/\-]{8,12})'
            ]
        }
    
    def detect_file_type(self, file_path: str) -> str:
        """Detect file type using file extension"""
        try:
            return self._get_type_from_extension(file_path)
        except Exception as e:
            logger.error(f"Failed to detect file type: {str(e)}")
            return 'application/octet-stream'
    
    def _get_type_from_extension(self, file_path: str) -> str:
        """Get file type from extension"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return 'application/pdf'
        elif ext in ['.jpg', '.jpeg']:
            return 'image/jpeg'
        elif ext == '.png':
            return 'image/png'
        else:
            return 'application/octet-stream'
    
    async def extract_text_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF using PyPDF2 and OCR fallback"""
        try:
            extracted_data = {
                'text': '',
                'pages': [],
                'metadata': {}
            }
            
            # Try text extraction first
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                extracted_data['metadata'] = {
                    'page_count': len(pdf_reader.pages),
                    'title': pdf_reader.metadata.get('/Title', '') if pdf_reader.metadata else '',
                    'author': pdf_reader.metadata.get('/Author', '') if pdf_reader.metadata else ''
                }
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    extracted_data['pages'].append({
                        'page_number': page_num + 1,
                        'text': page_text,
                        'extraction_method': 'text'
                    })
                    extracted_data['text'] += page_text + '\n'
            
            # If no text extracted, use OCR
            if not extracted_data['text'].strip():
                logger.info(f"No text extracted, falling back to OCR - file: {file_path}")
                extracted_data = await self._ocr_pdf(file_path)
            
            logger.info("PDF text extraction completed", 
                       extra={"file_path_info": file_path, 
                              "pages": len(extracted_data['pages']),
                              "text_length": len(extracted_data['text'])})
            
            return extracted_data
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {str(e)}")
            raise
    
    async def _ocr_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF using OCR (simplified version without pdf2image)"""
        try:
            # Simplified fallback - return empty result for now
            logger.warning("PDF OCR not available without pdf2image package")
            extracted_data = {
                'text': '',
                'pages': [],
                'metadata': {'page_count': 0}
            }
            return extracted_data
        except Exception as e:
            logger.error(f"Failed to OCR PDF: {str(e)}")
            raise
    
    async def extract_text_from_image(self, file_path: str) -> Dict[str, Any]:
        """Extract text from image using OCR"""
        try:
            # Open and process image
            image = Image.open(file_path)
            
            # Perform OCR
            text = pytesseract.image_to_string(image, config='--oem 3 --psm 6')
            
            extracted_data = {
                'text': text,
                'pages': [{
                    'page_number': 1,
                    'text': text,
                    'extraction_method': 'ocr'
                }],
                'metadata': {
                    'page_count': 1,
                    'image_size': image.size,
                    'image_format': image.format
                }
            }
            
            logger.info("Image text extraction completed", 
                       extra={"file_path_info": file_path,
                              "text_length": len(text)})
            
            return extracted_data
        except Exception as e:
            logger.error(f"Failed to extract text from image: {str(e)}")
            raise
    
    async def process_document(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process document and extract text"""
        try:
            file_type = self.detect_file_type(file_path)
            doc_id = str(uuid.uuid4())
            
            if file_type == 'application/pdf':
                extracted_data = await self.extract_text_from_pdf(file_path)
            elif file_type.startswith('image/'):
                extracted_data = await self.extract_text_from_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Extract structured fields from the text using AI
            structured_fields = await self.extract_structured_fields_ai(extracted_data['text'], filename)
            
            # Create document object
            document = {
                'doc_id': doc_id,
                'filename': filename,
                'file_type': file_type,
                'text': extracted_data['text'],
                'pages': extracted_data['pages'],
                'metadata': extracted_data['metadata'],
                'structured_fields': structured_fields,
                'processed_at': 'now()'
            }
            
            logger.info("Document processed successfully", 
                       extra={"doc_id": doc_id,
                              "file_name": filename,
                              "file_type": file_type,
                              "extracted_fields": len(structured_fields)})
            
            return document
        except Exception as e:
            logger.error(f"Failed to process document: {str(e)}")
            raise
    
    def chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk document text for embedding"""
        try:
            text = document['text']
            chunks = self.text_splitter.split_text(text)
            
            chunked_documents = []
            for i, chunk in enumerate(chunks):
                chunk_data = {
                    'chunk_id': f"{document['doc_id']}_chunk_{i}",
                    'doc_id': document['doc_id'],
                    'text': chunk,
                    'chunk_index': i,
                    'metadata': {
                        'filename': document['filename'],
                        'file_type': document['file_type'],
                        'doc_id': document['doc_id'],
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }
                }
                chunked_documents.append(chunk_data)
            
            logger.info("Document chunked successfully", 
                       extra={"doc_id": document['doc_id'],
                              "chunks_created": len(chunks)})
            
            return chunked_documents
        except Exception as e:
            logger.error(f"Failed to chunk document: {str(e)}")
            raise
    
    async def extract_structured_fields_ai(self, text: str, filename: str = "") -> Dict[str, List[Dict[str, Any]]]:
        """Extract structured field data from text using AI"""
        try:
            # Use simple AI extractor for intelligent field extraction
            # extracted_fields = await simple_ai_extractor.extract_structured_fields(text, filename)
            
            # Temporarily use regex extraction until AI extractor is fixed
            logger.info("Using regex extraction temporarily - AI extractor disabled")
            extracted_fields = self.extract_structured_fields_regex(text)
            
            logger.info(f"Structured fields extracted - filename: {filename}, field_types: {len(extracted_fields)}")
            return extracted_fields
            
        except Exception as e:
            logger.error(f"Failed to extract structured fields: {str(e)}")
            # Fallback to regex extraction if AI fails
            logger.info("Falling back to regex extraction...")
            return self.extract_structured_fields_regex(text)
    
    def extract_structured_fields_regex(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract structured field data from text using regex patterns (fallback)"""
        try:
            extracted_fields = {}
            
            for field_type, patterns in self.field_patterns.items():
                matches = []
                
                for pattern in patterns:
                    found_matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                    for match in found_matches:
                        # Special handling for different field types
                        if field_type == 'phone' and match.groups() and len(match.groups()) >= 3:
                            # Format phone number from groups
                            area, prefix, number = match.groups()[:3]
                            value = f"({area}) {prefix}-{number}"
                        elif field_type == 'full_name' and match.groups() and len(match.groups()) >= 2:
                            # Combine first and last name
                            if match.groups()[1]:  # Two separate groups
                                value = f"{match.group(1)} {match.group(2)}"
                            else:  # Single group with full name
                                value = match.group(1)
                        else:
                            # Get the matched value (either full match or first group)
                            value = match.group(1) if match.groups() else match.group(0)
                        
                        value = value.strip()
                        
                        if len(value) > 1:  # Exclude single characters
                            # Get context around the match
                            start_pos = max(0, match.start() - 50)
                            end_pos = min(len(text), match.end() + 50)
                            context = text[start_pos:end_pos].strip()
                            
                            matches.append({
                                'value': value,
                                'context': context,
                                'confidence': self._calculate_field_confidence(field_type, value, context),
                                'position': match.start()
                            })
                
                # Remove duplicates and sort by confidence
                unique_matches = []
                seen_values = set()
                for match in matches:
                    if match['value'].lower() not in seen_values:
                        seen_values.add(match['value'].lower())
                        unique_matches.append(match)
                
                unique_matches.sort(key=lambda x: x['confidence'], reverse=True)
                extracted_fields[field_type] = unique_matches[:3]  # Keep top 3 matches
            
            logger.info(f"Regex structured fields extracted - field_types: {len(extracted_fields)}")
            return extracted_fields
            
        except Exception as e:
            logger.error(f"Failed to extract structured fields with regex: {str(e)}")
            return {}
    
    def _calculate_field_confidence(self, field_type: str, value: str, context: str) -> float:
        """Calculate confidence score for extracted field value"""
        try:
            confidence = 0.5  # Base confidence
            
            # Field-specific validation
            if field_type == 'email':
                if '@' in value and '.' in value.split('@')[-1]:
                    confidence = 0.9
            elif field_type == 'phone':
                # Remove non-digits and check length
                digits = re.sub(r'[^\d]', '', value)
                if 10 <= len(digits) <= 11:
                    confidence = 0.8
            elif field_type == 'name' or field_type == 'full_name':
                # Check if it looks like a real name
                words = value.split()
                if len(words) >= 2 and value.replace(' ', '').isalpha():
                    confidence = 0.8
                    # Boost confidence if it's at the beginning of document
                    if context.startswith(value) or value in context[:200]:
                        confidence = 0.95
                    # Penalize common non-name phrases
                    lower_value = value.lower()
                    if any(phrase in lower_value for phrase in ['full stack', 'developer', 'engineer', 'manager', 'director']):
                        confidence = 0.2
                elif len(words) == 1 and value.isalpha() and len(value) > 2:
                    confidence = 0.6  # Single name
            elif field_type == 'linkedin':
                if 'linkedin.com' in value:
                    confidence = 0.9
            elif field_type == 'website':
                if value.startswith('http') and '.' in value:
                    confidence = 0.8
            
            # Context-based confidence adjustment
            context_lower = context.lower()
            if field_type in context_lower:
                confidence += 0.1
            
            # Penalize very short values
            if len(value) < 3:
                confidence *= 0.5
            
            return min(1.0, confidence)
            
        except Exception:
            return 0.5

# Global instance
document_processor = DocumentProcessor() 