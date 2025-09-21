#!/usr/bin/env python3
"""
Test RAG system with the newly uploaded document from the worker logs.
This tests if the document was properly processed and stored in the database.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from agents.tooling.rag.core import RAGTool, RetrievalConfig
from agents.patient_navigator.information_retrieval.agent import InformationRetrievalAgent
from agents.patient_navigator.information_retrieval.models import InformationRetrievalInput

async def test_uploaded_document_rag():
    """Test RAG system with the document that was just uploaded and processed."""
    
    print("🔍 Testing RAG System with Newly Uploaded Document")
    print("=" * 60)
    
    # Set production database URL
    os.environ["DATABASE_URL"] = "${DATABASE_URL}/{total_queries}")
        print(f"  Success rate: {successful_queries/total_queries*100:.1f}%")
        
        if successful_queries > 0:
            print("✅ RAG system is working with the uploaded document!")
        else:
            print("❌ RAG system is not finding relevant chunks")
        
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(test_uploaded_document_rag())
