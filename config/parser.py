"""
LlamaParse integration for document parsing.
"""
from typing import List, Optional
import os
from pathlib import Path
from dotenv import load_dotenv
from llama_parse import LlamaParse
from langchain_core.documents import Document

# Load environment variables
load_dotenv()

class DocumentParser:
    def __init__(self):
        self.api_key = os.getenv("LLAMA_CLOUD_API_KEY")
        if not self.api_key:
            raise ValueError("LLAMA_CLOUD_API_KEY environment variable not set")
        self.parser = LlamaParse(api_key=self.api_key, result_type="text")
        
    def parse_document(self, file_path: str) -> List[Document]:
        """
        Parse a document using LlamaParse.
        
        Args:
            file_path: Path to the document to parse
            
        Returns:
            List of Document objects
            
        Raises:
            Exception: If file doesn't exist or parsing fails
        """
        # Check if file exists
        if not Path(file_path).exists():
            raise Exception(f"File not found: {file_path}")
            
        try:
            # Parse the document using LlamaParse's load_data method
            extra_info = {"file_name": file_path}
            with open(file_path, "rb") as f:
                parsed_docs = self.parser.load_data(f, extra_info=extra_info)
            
            # Handle empty results
            if not parsed_docs:
                return [Document(
                    page_content="",
                    metadata={
                        "page_number": 1,
                        "source": file_path,
                        "error": "No content parsed"
                    }
                )]
            
            # Convert to LangChain documents if needed
            documents = []
            for doc in parsed_docs:
                # Handle both Document objects and raw parsed results
                if isinstance(doc, Document):
                    documents.append(doc)
                else:
                    documents.append(Document(
                        page_content=doc.text if hasattr(doc, "text") else str(doc),
                        metadata={
                            "page_number": doc.page_number if hasattr(doc, "page_number") else 1,
                            "source": file_path
                        }
                    ))
            return documents
            
        except Exception as e:
            raise Exception(f"Error parsing document: {str(e)}")
            
    def parse_documents(self, file_paths: List[str]) -> List[Document]:
        """
        Parse multiple documents using LlamaParse.
        
        Args:
            file_paths: List of paths to documents to parse
            
        Returns:
            List of Document objects
            
        Raises:
            Exception: If any file doesn't exist or parsing fails
        """
        all_documents = []
        for file_path in file_paths:
            documents = self.parse_document(file_path)
            all_documents.extend(documents)
        return all_documents 