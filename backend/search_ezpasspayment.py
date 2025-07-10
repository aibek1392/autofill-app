#!/usr/bin/env python3
"""
Search specifically for the missing E-ZPASSPAYMENT transaction
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.rag_service import RAGService

async def search_ezpasspayment():
    print("🔍 Searching for missing E-ZPASSPAYMENT transaction")
    print("=" * 60)
    
    user_id = "18e3f9bf-3a9b-4994-90cd-8cc9b08dcedf"
    rag_service = RAGService()
    
    # Test specific queries for the missing transaction
    test_queries = [
        "E-ZPASSPAYMENT",
        "12/12/22 E-ZPASSPAYMENT", 
        "ID:5229569",
        "E-ZPASS PAYMENT",
        "E-ZPASS ID:5229569",
        "12/12/22 E-ZPASS",
        "E-ZPASS -240.00",
        "E-ZPASS 240.00",
        "E-ZPASS PAYMENT 240",
        "E-ZPASS PAYMENT -240"
    ]
    
    for query in test_queries:
        print(f"\n🔎 Testing: '{query}'")
        print("-" * 50)
        
        try:
            results = await rag_service.search_documents(query, user_id)
            print(f"📊 Found {len(results)} results")
            
            for i, result in enumerate(results):
                text = result['text']
                print(f"   Result {i+1}:")
                print(f"   Score: {result['score']:.3f}")
                print(f"   Text: {text}")
                
                # Look for E-ZPASS related content
                if "E-ZPASS" in text.upper():
                    print(f"   ✅ Contains E-ZPASS")
                if "5229569" in text:
                    print(f"   ✅ Contains ID:5229569")
                if "240" in text:
                    print(f"   ✅ Contains 240")
                print()
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(search_ezpasspayment()) 