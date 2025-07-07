import os
import uuid
from typing import Dict, List, Any, Optional
import logging
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

from config import settings
from services.rag_service import rag_service

logger = logging.getLogger(__name__)

class WebFormService:
    def __init__(self):
        self.supported_form_types = {
            'input': ['text', 'email', 'tel', 'url', 'password', 'number', 'date'],
            'textarea': [],
            'select': []
        }
    
    async def analyze_web_form(self, url: str, html_content: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a web form and extract field information"""
        try:
            if not html_content:
                # Fetch the webpage
                response = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                html_content = response.text
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all forms on the page
            forms = soup.find_all('form')
            form_data = []
            
            for form_idx, form in enumerate(forms):
                form_info = {
                    'form_index': form_idx,
                    'action': form.get('action', ''),
                    'method': form.get('method', 'GET').upper(),
                    'fields': []
                }
                
                # Extract form fields
                fields = self._extract_form_fields(form)
                form_info['fields'] = fields
                
                if fields:  # Only include forms with fields
                    form_data.append(form_info)
            
            result = {
                'url': url,
                'forms_count': len(form_data),
                'forms': form_data,
                'metadata': {
                    'title': soup.title.string if soup.title else '',
                    'domain': urlparse(url).netloc
                }
            }
            
            logger.info(f"Web form analyzed - URL: {url}, forms_found: {len(form_data)}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze web form: {str(e)}")
            raise
    
    def _extract_form_fields(self, form) -> List[Dict[str, Any]]:
        """Extract individual form fields from a form element"""
        fields = []
        
        # Input fields
        inputs = form.find_all('input')
        for input_elem in inputs:
            input_type = input_elem.get('type', 'text').lower()
            if input_type in ['hidden', 'submit', 'button', 'reset']:
                continue
                
            field_info = self._create_field_info(input_elem, 'input')
            if field_info:
                fields.append(field_info)
        
        # Textarea fields
        textareas = form.find_all('textarea')
        for textarea in textareas:
            field_info = self._create_field_info(textarea, 'textarea')
            if field_info:
                fields.append(field_info)
        
        # Select fields
        selects = form.find_all('select')
        for select in selects:
            field_info = self._create_field_info(select, 'select')
            if field_info:
                # Add options for select fields
                options = []
                for option in select.find_all('option'):
                    options.append({
                        'value': option.get('value', ''),
                        'text': option.get_text(strip=True)
                    })
                field_info['options'] = options
                fields.append(field_info)
        
        return fields
    
    def _create_field_info(self, element, field_type: str) -> Optional[Dict[str, Any]]:
        """Create field information dictionary from form element"""
        try:
            field_info = {
                'type': field_type,
                'input_type': element.get('type', 'text') if field_type == 'input' else field_type,
                'name': element.get('name', ''),
                'id': element.get('id', ''),
                'placeholder': element.get('placeholder', ''),
                'required': element.has_attr('required'),
                'value': element.get('value', ''),
                'selector': self._generate_selector(element)
            }
            
            # Get label text
            label_text = self._find_label_text(element)
            field_info['label'] = label_text
            
            # Determine field purpose based on various attributes
            field_info['purpose'] = self._determine_field_purpose(field_info)
            
            return field_info
            
        except Exception as e:
            logger.error(f"Failed to create field info: {str(e)}")
            return None
    
    def _generate_selector(self, element) -> str:
        """Generate a CSS selector for the element"""
        selectors = []
        
        # Try ID first (most specific)
        if element.get('id'):
            return f"#{element['id']}"
        
        # Try name attribute
        if element.get('name'):
            selectors.append(f"[name='{element['name']}']")
        
        # Try class if available
        if element.get('class'):
            class_str = '.'.join(element['class'])
            selectors.append(f".{class_str}")
        
        # Fallback to tag + attributes
        tag = element.name
        if element.get('type'):
            selectors.append(f"{tag}[type='{element['type']}']")
        else:
            selectors.append(tag)
        
        return selectors[0] if selectors else tag
    
    def _find_label_text(self, element) -> str:
        """Find associated label text for form element"""
        label_text = ""
        
        # Check for explicit label with for attribute
        if element.get('id'):
            label = element.find_parent().find('label', {'for': element['id']})
            if label:
                label_text = label.get_text(strip=True)
        
        # Check for wrapping label
        if not label_text:
            label = element.find_parent('label')
            if label:
                # Get text excluding the input element itself
                label_copy = label.__copy__()
                if label_copy.find(element.name):
                    label_copy.find(element.name).extract()
                label_text = label_copy.get_text(strip=True)
        
        # Check for nearby text/labels
        if not label_text:
            # Look for previous siblings
            prev_sibling = element.find_previous_sibling(['label', 'span', 'div'])
            if prev_sibling:
                text = prev_sibling.get_text(strip=True)
                if len(text) < 100:  # Reasonable label length
                    label_text = text
        
        return label_text
    
    def _determine_field_purpose(self, field_info: Dict[str, Any]) -> str:
        """Determine the purpose of a form field based on its attributes"""
        name = field_info.get('name', '').lower()
        id_attr = field_info.get('id', '').lower()
        placeholder = field_info.get('placeholder', '').lower()
        label = field_info.get('label', '').lower()
        input_type = field_info.get('input_type', '').lower()
        
        # Combine all text for analysis
        all_text = f"{name} {id_attr} {placeholder} {label}".lower()
        
        # Email patterns
        if input_type == 'email' or any(keyword in all_text for keyword in ['email', 'e-mail', 'mail']):
            return 'email'
        
        # Phone patterns
        if input_type == 'tel' or any(keyword in all_text for keyword in ['phone', 'tel', 'mobile', 'cellular']):
            return 'phone'
        
        # Name patterns
        if any(keyword in all_text for keyword in ['firstname', 'first_name', 'fname']):
            return 'first_name'
        if any(keyword in all_text for keyword in ['lastname', 'last_name', 'lname', 'surname']):
            return 'last_name'
        if any(keyword in all_text for keyword in ['fullname', 'full_name', 'name']) and 'first' not in all_text and 'last' not in all_text:
            return 'full_name'
        
        # Address patterns
        if any(keyword in all_text for keyword in ['address', 'street', 'addr']):
            return 'address'
        if any(keyword in all_text for keyword in ['city', 'town']):
            return 'city'
        if any(keyword in all_text for keyword in ['state', 'province', 'region']):
            return 'state'
        if any(keyword in all_text for keyword in ['zip', 'postal', 'postcode']):
            return 'zip_code'
        
        # Date patterns
        if input_type == 'date' or any(keyword in all_text for keyword in ['date', 'birth', 'dob']):
            return 'date'
        
        # URL patterns
        if input_type == 'url' or any(keyword in all_text for keyword in ['website', 'url', 'link', 'portfolio']):
            return 'url'
        
        # LinkedIn patterns
        if any(keyword in all_text for keyword in ['linkedin', 'linked-in']):
            return 'linkedin'
        
        # Cover letter / message patterns
        if field_info.get('type') == 'textarea' or any(keyword in all_text for keyword in ['cover', 'letter', 'message', 'notes', 'additional']):
            return 'cover_letter'
        
        # Generic text field
        return 'text'
    
    async def generate_autofill_data(self, form_analysis: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Generate autofill data for a web form based on user documents"""
        try:
            autofill_data = {}
            confidence_scores = {}
            missing_fields = []
            field_mapping = {}
            
            # Get user context
            user_context = await self._get_user_context_for_web_form(user_id)
            
            for form in form_analysis['forms']:
                form_autofill = {}
                
                for field in form['fields']:
                    field_purpose = field['purpose']
                    field_selector = field['selector']
                    
                    # Use AI to extract appropriate data
                    field_value, confidence, source = await self._extract_field_value(
                        field_purpose, field, user_context
                    )
                    
                    if field_value and field_value != "MISSING":
                        form_autofill[field_selector] = field_value
                        confidence_scores[field_selector] = confidence
                        field_mapping[field_selector] = source
                    else:
                        missing_fields.append(field['label'] or field['name'] or field_selector)
                
                autofill_data[f"form_{form['form_index']}"] = form_autofill
            
            result = {
                'autofill_data': autofill_data,
                'confidence_scores': confidence_scores,
                'missing_fields': missing_fields,
                'field_mapping': field_mapping,
                'form_analysis': form_analysis
            }
            
            logger.info(f"Autofill data generated - user_id: {user_id}, fields_filled: {len(confidence_scores)}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate autofill data: {str(e)}")
            raise
    
    async def _get_user_context_for_web_form(self, user_id: str) -> str:
        """Get comprehensive user context for web form filling"""
        try:
            search_queries = [
                "name full name first name last name",
                "email address contact",
                "phone number telephone mobile",
                "address street city state zip postal code",
                "linkedin profile portfolio website url",
                "cover letter introduction about me",
                "experience work employment job",
                "education school university degree",
                "skills technical skills programming"
            ]
            
            all_context = []
            for query in search_queries:
                results = await rag_service.search_documents(query, user_id, top_k=3)
                all_context.extend(results)
            
            # Remove duplicates
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
                for item in unique_context[:15]  # More context for web forms
            ])
            
            return context_str
            
        except Exception as e:
            logger.error(f"Failed to get user context: {str(e)}")
            raise
    
    async def _extract_field_value(self, field_purpose: str, field_info: Dict[str, Any], user_context: str) -> tuple[str, float, str]:
        """Extract appropriate value for a specific field"""
        try:
            prompt = f"""You are an AI assistant that extracts specific information for web form autofill.

Field Information:
- Purpose: {field_purpose}
- Label: {field_info.get('label', '')}
- Name: {field_info.get('name', '')}
- Placeholder: {field_info.get('placeholder', '')}
- Type: {field_info.get('input_type', '')}

User Data Context:
{user_context}

Instructions:
1. Extract the most appropriate value for this field from the user context
2. If the field is a select/dropdown and you have options, choose the best match
3. For cover letters or long text fields, provide a professional and relevant response
4. If information is not available, respond with "MISSING"
5. For email fields, extract email addresses
6. For phone fields, extract phone numbers
7. For name fields, extract appropriate name parts
8. For address fields, extract address components

Available options (if select field): {field_info.get('options', [])}

Respond with ONLY the extracted value, nothing else:"""

            response = await rag_service.llm.ainvoke(prompt)
            field_value = response.content.strip()
            
            # Calculate confidence based on field purpose and context match
            confidence = self._calculate_confidence(field_purpose, field_value, user_context)
            
            # Determine source document
            source = "User documents"
            
            return field_value, confidence, source
            
        except Exception as e:
            logger.error(f"Failed to extract field value: {str(e)}")
            return "MISSING", 0.0, "Error"
    
    def _calculate_confidence(self, field_purpose: str, field_value: str, user_context: str) -> float:
        """Calculate confidence score for extracted field value"""
        if field_value == "MISSING":
            return 0.0
        
        # Basic confidence calculation
        if field_purpose in ['email', 'phone'] and '@' in field_value or any(char.isdigit() for char in field_value):
            return 0.9
        elif field_purpose in ['first_name', 'last_name', 'full_name'] and field_value.replace(' ', '').isalpha():
            return 0.85
        elif field_purpose in ['address', 'city', 'state'] and len(field_value) > 2:
            return 0.8
        elif len(field_value) > 0:
            return 0.7
        else:
            return 0.5

# Global instance
web_form_service = WebFormService() 