import os
import uuid
from typing import Dict, List, Any, Optional
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter
import io
from config import settings
from services.rag_service import rag_service
from services.document_processor import document_processor

logger = logging.getLogger(__name__)

class FormFiller:
    def __init__(self):
        self.output_dir = os.path.join(settings.UPLOAD_DIR, 'filled_forms')
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def extract_form_fields(self, form_path: str) -> Dict[str, Any]:
        """Extract form fields from a PDF"""
        try:
            # Process the form PDF to extract text
            form_document = await document_processor.process_document(form_path, os.path.basename(form_path))
            
            # Use AI to identify form fields
            prompt = f"""Analyze this form and identify all fillable fields. 
            
Form content:
{form_document['text']}

Please identify and list all form fields that need to be filled, such as:
- Name fields (first name, last name, full name)
- Address fields (street, city, state, zip)
- Contact fields (phone, email)
- Date fields
- ID numbers
- Checkboxes and radio buttons
- Any other fillable fields

Return the field names and their likely purposes."""

            # Generate field analysis
            field_analysis = await rag_service.llm.ainvoke(prompt)
            
            result = {
                'form_text': form_document['text'],
                'field_analysis': field_analysis.content,
                'pages': form_document['pages'],
                'metadata': form_document['metadata']
            }
            
            logger.info("Form fields extracted", form_path=form_path)
            return result
        except Exception as e:
            logger.error(f"Failed to extract form fields: {str(e)}")
            raise
    
    async def get_user_data_context(self, user_id: str, form_fields: str) -> str:
        """Get relevant user data for form filling"""
        try:
            # Search user documents for relevant information
            search_queries = [
                "name full name first name last name",
                "address street city state zip postal",
                "phone number telephone contact",
                "email address",
                "date of birth birth date",
                "social security number SSN",
                "driver license number",
                "identification ID number"
            ]
            
            all_context = []
            for query in search_queries:
                results = await rag_service.search_documents(query, user_id, top_k=3)
                all_context.extend(results)
            
            # Remove duplicates and combine context
            seen_chunks = set()
            unique_context = []
            for item in all_context:
                chunk_id = f"{item['doc_id']}_{item['chunk_index']}"
                if chunk_id not in seen_chunks:
                    seen_chunks.add(chunk_id)
                    unique_context.append(item)
            
            # Format context
            context_str = "\n\n".join([
                f"From {item['filename']}:\n{item['text']}"
                for item in unique_context[:10]  # Limit to top 10 most relevant
            ])
            
            logger.info("User data context retrieved", 
                       user_id=user_id,
                       context_items=len(unique_context))
            
            return context_str
        except Exception as e:
            logger.error(f"Failed to get user data context: {str(e)}")
            raise
    
    async def fill_form_with_ai(self, form_data: Dict[str, Any], user_context: str) -> Dict[str, Any]:
        """Use AI to fill form fields based on user data"""
        try:
            form_text = form_data['form_text']
            
            # Use RAG service to extract and fill form fields
            filled_form_data = await rag_service.extract_form_fields(form_text, user_context)
            
            logger.info("Form filled with AI", 
                       filled_fields=len(filled_form_data.get('filled_fields', {})),
                       missing_fields=len(filled_form_data.get('missing_fields', [])))
            
            return filled_form_data
        except Exception as e:
            logger.error(f"Failed to fill form with AI: {str(e)}")
            raise
    
    def create_filled_pdf(self, original_form_path: str, filled_data: Dict[str, Any], output_filename: str) -> str:
        """Create a filled PDF with the extracted data"""
        try:
            # Read the original PDF
            with open(original_form_path, 'rb') as file:
                reader = PdfReader(file)
                writer = PdfWriter()
                
                # For now, we'll create a simple overlay with filled data
                # In a production environment, you'd want to use a more sophisticated PDF form filling library
                
                # Create overlay with filled data
                overlay_buffer = io.BytesIO()
                overlay_canvas = canvas.Canvas(overlay_buffer, pagesize=letter)
                
                # Add filled data as text overlay (simplified approach)
                y_position = 750
                overlay_canvas.setFont("Helvetica", 10)
                
                filled_fields = filled_data.get('filled_fields', {})
                for field_name, field_value in filled_fields.items():
                    if field_value != "MISSING":
                        text = f"{field_name}: {field_value}"
                        overlay_canvas.drawString(50, y_position, text)
                        y_position -= 20
                
                overlay_canvas.save()
                overlay_buffer.seek(0)
                
                # Merge overlay with original
                overlay_reader = PdfReader(overlay_buffer)
                
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    if page_num < len(overlay_reader.pages):
                        page.merge_page(overlay_reader.pages[page_num])
                    writer.add_page(page)
                
                # Save filled PDF
                output_path = os.path.join(self.output_dir, output_filename)
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
                
                logger.info("Filled PDF created", output_path=output_path)
                return output_path
        except Exception as e:
            logger.error(f"Failed to create filled PDF: {str(e)}")
            raise
    
    async def process_form_filling(self, form_path: str, user_id: str) -> Dict[str, Any]:
        """Complete form filling pipeline"""
        try:
            # Step 1: Extract form fields
            logger.info(f"Starting form filling process - form_path: {form_path}, user_id: {user_id}")
            form_data = await self.extract_form_fields(form_path)
            
            # Step 2: Get user data context
            user_context = await self.get_user_data_context(user_id, form_data['field_analysis'])
            
            # Step 3: Fill form with AI
            filled_data = await self.fill_form_with_ai(form_data, user_context)
            
            # Step 4: Create output filename
            original_filename = os.path.basename(form_path)
            name, ext = os.path.splitext(original_filename)
            output_filename = f"{name}_filled_{uuid.uuid4().hex[:8]}{ext}"
            
            # Step 5: Create filled PDF
            filled_pdf_path = self.create_filled_pdf(form_path, filled_data, output_filename)
            
            # Step 6: Prepare result
            result = {
                'filled_form_path': filled_pdf_path,
                'filled_form_url': f"/api/download/{output_filename}",
                'original_form_name': original_filename,
                'filled_fields': filled_data.get('filled_fields', {}),
                'missing_fields': filled_data.get('missing_fields', []),
                'confidence_scores': filled_data.get('confidence_scores', {}),
                'field_mapping': filled_data.get('field_mapping', {}),
                'user_id': user_id,
                'processing_status': 'completed'
            }
            
            logger.info("Form filling completed successfully", 
                       user_id=user_id,
                       filled_fields=len(result['filled_fields']),
                       missing_fields=len(result['missing_fields']))
            
            return result
        except Exception as e:
            logger.error(f"Failed to process form filling: {str(e)}")
            raise
    
    async def get_missing_field_suggestions(self, missing_fields: List[str], user_id: str) -> Dict[str, str]:
        """Get suggestions for missing fields based on user data"""
        try:
            suggestions = {}
            
            for field in missing_fields:
                # Search for similar information in user documents
                search_results = await rag_service.search_documents(field, user_id, top_k=3)
                
                if search_results:
                    # Use AI to suggest possible values
                    context = "\n".join([result['text'] for result in search_results[:2]])
                    prompt = f"""Based on this context from user documents, suggest a possible value for the form field '{field}':

Context: {context}

Provide a concise suggestion for the field value, or respond with 'No suggestion available' if the context doesn't contain relevant information."""
                    
                    response = await rag_service.llm.ainvoke(prompt)
                    suggestions[field] = response.content.strip()
                else:
                    suggestions[field] = "No suggestion available"
            
            logger.info("Missing field suggestions generated", 
                       user_id=user_id,
                       suggestions_count=len(suggestions))
            
            return suggestions
        except Exception as e:
            logger.error(f"Failed to get missing field suggestions: {str(e)}")
            raise

# Global instance
form_filler = FormFiller() 