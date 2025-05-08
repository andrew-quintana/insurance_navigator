"""
Vector store configuration using PGVector.
"""
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from langchain_community.vectorstores import PGVector
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document

# Load environment variables
load_dotenv()

class VectorStore:
    def __init__(self, embeddings: Embeddings):
        self.connection_string = os.getenv("DATABASE_URL")
        if not self.connection_string:
            raise ValueError("DATABASE_URL environment variable not set")
        self.embeddings = embeddings
        self.collection_name = "insurance_documents"
        self._store = None
        
    def init_store(self) -> PGVector:
        """Initialize the vector store."""
        try:
            if not self._store:
                self._store = PGVector(
                    connection_string=self.connection_string,
                    embedding_function=self.embeddings,
                    collection_name=self.collection_name
                )
            return self._store
        except Exception as e:
            raise Exception(f"Error initializing vector store: {str(e)}")
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store."""
        try:
            store = self.init_store()
            store.add_documents(documents)
        except Exception as e:
            raise Exception(f"Error adding documents to vector store: {str(e)}")
        
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Perform similarity search on the vector store."""
        try:
            store = self.init_store()
            return store.similarity_search(query, k=k)
        except Exception as e:
            raise Exception(f"Error performing similarity search: {str(e)}")
            
    def delete_collection(self) -> None:
        """Delete the collection from the vector store."""
        try:
            store = self.init_store()
            store.delete_collection()
            self._store = None
        except Exception as e:
            raise Exception(f"Error deleting collection: {str(e)}")
            
    def __del__(self):
        """Clean up resources."""
        if hasattr(self, '_store') and self._store and hasattr(self._store, '_bind'):
            try:
                self._store._bind.dispose()
            except Exception:
                pass  # Ignore cleanup errors 