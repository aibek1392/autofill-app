#!/usr/bin/env python3
"""
Script to find specific 01/03/23 E-ZPASS transactions
"""

import asyncio
import sys
import os
import glob

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from services.rag_service import RAGService
from services.document_processor import DocumentProcessor

async def find_specific_ezpass():
    """Find the specific 01/03/23 E-ZPASS transactions"""
    print("🔍 Searching for Specific 01/03/23 E-ZPASS Transactions")
    print("=" * 70)
    
    # Test user ID
    test_user_id = "test-user-123"
    
    # First, let's search for the specific date and amounts
    specific_queries = [
        "01/03/23 E-ZPASS REBILL ID:9863076",
        "01/03/23 E-ZPASS REBILL ID:9482226", 
        "01/03/23 E-ZPASS REBILL ID:9691475",
        "01/03/23 E-ZPASS $26.87",
        "01/03/23 E-ZPASS $13.75",
        "01/03/23 E-ZPASS $2.59",
        "01/03/23 E-ZPASS REBILL",
        "01/03/23 E-ZPASS"
    ]
    
    rag_service = RAGService()
    
    print("🔎 Testing specific queries:")
    print("-" * 40)
    
    for query in specific_queries:
        print(f"\nQuery: '{query}'")
        try:
            results = await rag_service.search_documents(query, test_user_id)
            print(f"   Found {len(results)} results")
            
            if results:
                for i, result in enumerate(results[:3]):  # Show first 3
                    print(f"   Result {i+1}: Score {result['score']:.3f} | {result['filename']}")
                    print(f"      Text: {result['text'][:150]}...")
            else:
                print("   ❌ No results found")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 70)
    print("🔍 Now searching all documents for 01/03/23 content...")
    print("-" * 40)
    
    # Let's also search all documents for any 01/03/23 content
    uploads_dir = settings.UPLOAD_DIR
    pdf_files = glob.glob(os.path.join(uploads_dir, "*.pdf"))
    
    doc_processor = DocumentProcessor()
    
    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        print(f"\n📄 Checking: {filename}")
        
        try:
            # Extract text from PDF
            doc_data = await doc_processor.process_document(pdf_file, filename)
            text = doc_data['text']
            
            # Look for 01/03/23 content
            if "01/03/23" in text:
                print(f"   ✅ Found 01/03/23 content!")
                
                # Look for E-ZPASS in the same document
                if "E-ZPASS" in text:
                    print(f"   ✅ Found E-ZPASS content!")
                    
                    # Extract lines containing both 01/03/23 and E-ZPASS
                    lines = text.split('\n')
                    ezpass_lines = []
                    
                    for i, line in enumerate(lines):
                        if "01/03/23" in line and "E-ZPASS" in line:
                            ezpass_lines.append(f"Line {i+1}: {line.strip()}")
                    
                    if ezpass_lines:
                        print(f"   📋 Found {len(ezpass_lines)} E-ZPASS lines from 01/03/23:")
                        for line in ezpass_lines:
                            print(f"      {line}")
                    else:
                        print(f"   ⚠️  No specific E-ZPASS lines found for 01/03/23")
                        
                        # Show context around 01/03/23
                        for i, line in enumerate(lines):
                            if "01/03/23" in line:
                                print(f"   📍 Line {i+1}: {line.strip()}")
                                # Show next few lines for context
                                for j in range(1, 4):
                                    if i+j < len(lines):
                                        print(f"      +{j}: {lines[i+j].strip()}")
                                break
                else:
                    print(f"   ❌ No E-ZPASS content found")
            else:
                print(f"   ❌ No 01/03/23 content found")
                
        except Exception as e:
            print(f"   ❌ Error processing {filename}: {str(e)}")
    
    print("\n" + "=" * 70)
    print("✅ Search completed!")

if __name__ == "__main__":
    asyncio.run(find_specific_ezpass()) 