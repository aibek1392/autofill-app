#!/usr/bin/env python3

"""
AI-based field extraction service using LangChain
Replaces regex-based extraction with intelligent AI parsing
"""

import json
import logging
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from config import settings

logger = logging.getLogger(__name__)

class AIFieldExtractor:
    def __init__(self):
        self.has_openai_key = bool(settings.OPENAI_API_KEY)
        if self.has_openai_key:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0,
                api_key=settings.OPENAI_API_KEY
            )
        else:
            self.llm = None
            logger.warning("OpenAI API key not configured. AI extraction will be disabled.")
    
    async def extract_structured_fields(self, text: str, filename: str = "") -> Dict[str, List[Dict[str, Any]]]:
        """Extract structured fields from document text using AI"""
        if not self.has_openai_key:
            logger.warning("Cannot extract fields - OpenAI API key not configured")
            return {}
        
        try:
            # Create extraction prompt
            extraction_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert at extracting structured information from documents, especially resumes and professional documents.

Your task is to extract specific field types from the document text and return them in a structured JSON format.

IMPORTANT GUIDELINES:
1. For names: Extract the PERSON'S name, not company names or job titles
2. For phone numbers: Extract complete phone numbers with proper formatting
3. For emails: Extract email addresses
4. For addresses: Extract physical addresses
5. For experience: Extract work experience descriptions, not company names alone
6. For skills: Extract technical skills, programming languages, technologies
7. For education: Extract educational background
8. For dates: Extract relevant dates
9. For LinkedIn/GitHub/Website: Extract social media and portfolio URLs

Return ONLY valid JSON in this exact format:
{
  "full_name": [{"value": "John Doe", "confidence": 0.95, "context": "surrounding text"}],
  "email": [{"value": "john@example.com", "confidence": 0.9, "context": "contact info"}],
  "phone": [{"value": "(555) 123-4567", "confidence": 0.8, "context": "phone section"}],
  "address": [{"value": "123 Main St, City, State", "confidence": 0.7, "context": "address section"}],
  "linkedin": [{"value": "linkedin.com/in/johndoe", "confidence": 0.8, "context": "social links"}],
  "github": [{"value": "github.com/johndoe", "confidence": 0.8, "context": "portfolio links"}],
  "website": [{"value": "johndoe.com", "confidence": 0.8, "context": "portfolio"}],
  "skills": [{"value": "Python, JavaScript, React", "confidence": 0.9, "context": "skills section"}],
  "experience": [{"value": "5 years as Software Developer", "confidence": 0.8, "context": "work history"}],
  "education": [{"value": "BS Computer Science", "confidence": 0.9, "context": "education section"}]
}

Confidence scores should be between 0.0 and 1.0 based on how certain you are about the extraction.
Context should be 2-3 words describing where you found the information."""),
                ("human", "Document filename: {filename}\n\nDocument text:\n{text}\n\nExtract structured fields:")
            ])
            
            # Generate response
            response = await self.llm.ainvoke(
                extraction_prompt.format(filename=filename, text=text[:4000])  # Limit text length
            )
            
                         # Parse JSON response
            try:
                # Clean the response content to handle potential formatting issues
                content = response.content.strip()
                
                # Try to extract JSON if it's wrapped in markdown code blocks
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                elif content.startswith('```'):
                    content = content.replace('```', '').strip()
                
                extracted_fields = json.loads(content)
                
                # Validate and clean the response
                cleaned_fields = {}
                for field_type, field_list in extracted_fields.items():
                    if isinstance(field_list, list) and field_list:
                        cleaned_list = []
                        for field_item in field_list:
                            if isinstance(field_item, dict) and 'value' in field_item:
                                # Ensure required fields exist
                                cleaned_item = {
                                    'value': str(field_item['value']).strip(),
                                    'confidence': float(field_item.get('confidence', 0.5)),
                                    'context': str(field_item.get('context', ''))[:200]  # Limit context length
                                }
                                
                                # Skip empty values
                                if cleaned_item['value'] and len(cleaned_item['value']) > 1:
                                    cleaned_list.append(cleaned_item)
                        
                        if cleaned_list:
                            cleaned_fields[field_type] = cleaned_list
                
                logger.info(f"AI field extraction completed - filename: {filename}, fields_extracted: {len(cleaned_fields)}")
                return cleaned_fields
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI extraction response as JSON: {e}")
                logger.debug(f"Raw response: {response.content[:500]}...")
                
                # Try a simpler approach - use AI to extract just the name and phone
                return await self._extract_basic_fields_fallback(text)
            except Exception as e:
                logger.error(f"Unexpected error in AI extraction: {e}")
                return {}
                
        except Exception as e:
            logger.error(f"AI field extraction failed: {str(e)}")
            return {}
    
    async def extract_specific_field(self, text: str, field_type: str, field_context: str = "") -> Optional[Dict[str, Any]]:
        """Extract a specific field type from text using AI"""
        if not self.has_openai_key:
            return None
            
        try:
            # Create field-specific prompt
            field_prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are an expert at extracting specific information from documents.

Extract ONLY the {field_type} from the provided text. 

FIELD TYPE DEFINITIONS:
- full_name: The person's actual name (first and last name), NOT company names or job titles
- email: Email address
- phone: Complete phone number with proper formatting like (555) 123-4567
- address: Physical mailing address
- linkedin: LinkedIn profile URL
- github: GitHub profile URL  
- website: Personal website or portfolio URL
- skills: Technical skills, programming languages, technologies
- experience: Work experience description or years of experience
- education: Educational background, degrees, schools

Return ONLY a JSON object in this format:
{{"value": "extracted_value", "confidence": 0.95, "context": "where_found"}}

If you cannot find the {field_type}, return: {{"value": null, "confidence": 0.0, "context": "not_found"}}"""),
                ("human", f"Context: {field_context}\n\nText to search:\n{text[:2000]}\n\nExtract {field_type}:")
            ])
            
            response = await self.llm.ainvoke(field_prompt.format())
            
            try:
                result = json.loads(response.content)
                if result.get('value'):
                    return {
                        'value': str(result['value']).strip(),
                        'confidence': float(result.get('confidence', 0.5)),
                        'context': str(result.get('context', ''))[:200]
                    }
            except json.JSONDecodeError:
                pass
                
            return None
            
        except Exception as e:
            logger.error(f"Specific field extraction failed for {field_type}: {str(e)}")
            return None
    
    async def _extract_basic_fields_fallback(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Fallback method to extract basic fields when JSON parsing fails"""
        try:
            basic_fields = {}
            
            # Extract name using a simple prompt
            name_result = await self.extract_specific_field(text, "full_name", "person's name at top of document")
            if name_result:
                basic_fields['full_name'] = [name_result]
            
            # Extract phone
            phone_result = await self.extract_specific_field(text, "phone", "phone number")
            if phone_result:
                basic_fields['phone'] = [phone_result]
            
            # Extract email
            email_result = await self.extract_specific_field(text, "email", "email address")
            if email_result:
                basic_fields['email'] = [email_result]
            
            logger.info(f"Basic field extraction fallback completed - fields: {len(basic_fields)}")
            return basic_fields
            
        except Exception as e:
            logger.error(f"Basic field extraction fallback failed: {e}")
            return {}

# Global instance
ai_extractor = AIFieldExtractor() 