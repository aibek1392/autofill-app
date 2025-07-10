#!/usr/bin/env python3
"""
Extract raw text from PDF and search for missing E-ZPASSPAYMENT transaction
"""

import asyncio
import sys
import os
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.document_processor import DocumentProcessor

async def extract_raw_text():
    print("🔍 Extracting raw text from BofA statements.pdf")
    print("=" * 60)
    
    # Path to the PDF file (using the UUID filename)
    pdf_path = "uploads/be5e5108-620f-4c23-beea-d43319ceefe3.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    print(f"📄 Processing: {pdf_path}")
    
    try:
        # Extract text using the document processor
        processor = DocumentProcessor()
        result = await processor.extract_text_from_pdf(pdf_path)
        if isinstance(result, dict):
            print(f"Returned keys: {list(result.keys())}")
            raw_text = result.get('text', '')
        else:
            raw_text = result
        print(f"📊 Extracted {len(raw_text)} characters of text")
        print("\n" + "="*60)
        print("🔍 SEARCHING FOR E-ZPASS TRANSACTIONS")
        print("="*60)
        
        # Search for E-ZPASS related content
        search_patterns = [
            r"E-ZPASSPAYMENT.*?ID:5229569",
            r"E-ZPASS.*?PAYMENT.*?5229569",
            r"12/12/22.*?E-ZPASS",
            r"E-ZPASSPAYMENT.*?DES:EZPASS",
            r"ID:5229569",
            r"E-ZPASS.*?240\.00",
            r"E-ZPASS.*?-240\.00",
            r"WEB-240\.00",
            r"12/12/22.*?WEB-240",
            r"E-ZPASS.*?REBILL.*?ID:9863076",
            r"E-ZPASS.*?REBILL.*?ID:9482226", 
            r"E-ZPASS.*?REBILL.*?ID:9691475"
        ]
        
        found_matches = []
        
        for pattern in search_patterns:
            matches = re.finditer(pattern, raw_text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                start = max(0, match.start() - 100)
                end = min(len(raw_text), match.end() + 100)
                context = raw_text[start:end]
                found_matches.append({
                    'pattern': pattern,
                    'match': match.group(),
                    'context': context,
                    'position': match.start()
                })
        
        if found_matches:
            print(f"✅ Found {len(found_matches)} matches:")
            for i, match_info in enumerate(found_matches):
                print(f"\n--- Match {i+1} ---")
                print(f"Pattern: {match_info['pattern']}")
                print(f"Match: {match_info['match']}")
                print(f"Context: ...{match_info['context']}...")
                print(f"Position: {match_info['position']}")
        else:
            print("❌ No E-ZPASS transactions found in raw text")
        
        print("\n" + "="*60)
        print("🔍 SEARCHING FOR SPECIFIC DATES AND AMOUNTS")
        print("="*60)
        
        # Search for specific dates and amounts
        date_amount_patterns = [
            r"12/12/22.*?240\.00",
            r"12/12/22.*?-240\.00", 
            r"WEB-240\.00",
            r"12/12/22.*?WEB-240",
            r"01/03/23.*?E-ZPASS",
            r"01/03/23.*?WEB-13\.75",
            r"01/03/23.*?WEB-2\.59",
            r"01/03/23.*?WEB-1\.25"
        ]
        
        for pattern in date_amount_patterns:
            matches = re.finditer(pattern, raw_text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                start = max(0, match.start() - 50)
                end = min(len(raw_text), match.end() + 50)
                context = raw_text[start:end]
                print(f"\nPattern: {pattern}")
                print(f"Match: {match.group()}")
                print(f"Context: ...{context}...")
        
        print("\n" + "="*60)
        print("📄 FIRST 2000 CHARACTERS OF RAW TEXT")
        print("="*60)
        print(raw_text[:2000])
        
        print("\n" + "="*60)
        print("📄 LAST 2000 CHARACTERS OF RAW TEXT")
        print("="*60)
        print(raw_text[-2000:])
        
    except Exception as e:
        print(f"❌ Error extracting text: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(extract_raw_text()) 