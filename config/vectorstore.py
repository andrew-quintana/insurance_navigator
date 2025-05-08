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
        self.connection_string = os.getenv("SUPABASE_DB_URL")
        self.embeddings = embeddings
        self.collection_name = "insurance_documents"
        
    def init_store(self) -> PGVector:
        """Initialize the vector store."""
        return PGVector(
            connection_string=self.connection_string,
            embedding_function=self.embeddings,
            collection_name=self.collection_name
        )
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store."""
        store = self.init_store()
        store.add_documents(documents)
        
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Perform similarity search on the vector store."""
        store = self.init_store()
        return store.similarity_search(query, k=k) 