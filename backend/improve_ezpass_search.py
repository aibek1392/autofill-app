#!/usr/bin/env python3
"""
Script to improve E-ZPASS search by adding specific patterns
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from services.rag_service import RAGService

async def test_improved_search():
    """Test improved search queries for E-ZPASS"""
    print("🔍 Testing Improved E-ZPASS Search")
    print("=" * 60)
    
    test_user_id = "test-user-123"
    rag_service = RAGService()
    
    # More specific and comprehensive queries
    improved_queries = [
        "E-ZPASS REBILL transactions from January 3rd 2023",
        "E-ZPASS REBILL ID:9863076 ID:9482226 ID:9691475",
        "01/03/23 E-ZPASS REBILL charges by Aibek Ozhorov",
        "E-ZPASS REBILL transactions on January 3rd 2023",
        "Aibek Ozhorov E-ZPASS REBILL charges from January 3rd",
        "E-ZPASS REBILL ID:9863076 $26.87",
        "E-ZPASS REBILL ID:9482226 $13.75", 
        "E-ZPASS REBILL ID:9691475 $2.59",
        "E-ZPASS REBILL charges on 01/03/23",
        "E-ZPASS REBILL transactions January 3rd 2023"
    ]
    
    for query in improved_queries:
        print(f"\n🔎 Query: '{query}'")
        print("-" * 50)
        
        try:
            results = await rag_service.search_documents(query, test_user_id)
            print(f"📊 Found {len(results)} results")
            
            if results:
                for i, result in enumerate(results):
                    print(f"   Result {i+1}: Score {result['score']:.3f} | {result['filename']}")
                    
                    # Check if this result contains the specific transactions
                    text = result['text'].lower()
                    if "01/03/23" in text and "ezpass" in text:
                        print(f"      ✅ Contains 01/03/23 E-ZPASS content!")
                        
                        # Look for specific IDs
                        if "9863076" in text:
                            print(f"      ✅ Contains ID:9863076")
                        if "9482226" in text:
                            print(f"      ✅ Contains ID:9482226")
                        if "9691475" in text:
                            print(f"      ✅ Contains ID:9691475")
                    
                    print(f"      Text: {result['text'][:200]}...")
                    print()
            else:
                print("   ❌ No results found")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Improved search test completed!")

if __name__ == "__main__":
    asyncio.run(test_improved_search()) 