"""
Document service module for managing document operations with HIPAA compliance.
"""
from typing import Optional, Dict, Any, List, BinaryIO
from pathlib import Path
from fastapi import Depends, HTTPException, status
from supabase import Client as SupabaseClient
import logging
import os
from datetime import datetime
from cryptography.fernet import Fernet
from config.database import get_supabase_client as get_base_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentService:
    """Service for managing document operations with HIPAA compliance."""

    def __init__(self, supabase_client: SupabaseClient):
        """Initialize the document service."""
        self.supabase = supabase_client
        self.table = "documents"
        self.audit_table = "audit_logs"
        self.encryption_key = os.getenv("DOCUMENT_ENCRYPTION_KEY")
        if not self.encryption_key:
            raise ValueError("Document encryption key not configured")
        self.fernet = Fernet(self.encryption_key.encode())

    async def get_document(self, document_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get document with access logging."""
        try:
            logger.info(f"Fetching document {document_id} for user {user_id}")
            
            # Get document with RLS policy check
            response = await self.supabase.table(self.table).select("*").eq("id", document_id).eq("user_id", user_id).single().execute()
            
            if response.error:
                logger.error(f"Error fetching document: {response.error}")
                return None
                
            if not response.data:
                return None
                
            # Update access log
            access_log = response.data.get("access_log", [])
            access_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "action": "document_accessed",
                "user_id": user_id
            })
            
            # Update document metadata
            await self.supabase.table(self.table).update({
                "last_accessed": datetime.utcnow().isoformat(),
                "access_log": access_log
            }).eq("id", document_id).execute()
            
            # Create audit log entry
            await self.supabase.table(self.audit_table).insert({
                "user_id": user_id,
                "action": "document_accessed",
                "details": {
                    "document_id": document_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "success": True
            }).execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            return None

    async def create_document(self, user_id: str, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new document record with HIPAA compliance."""
        try:
            logger.info(f"Creating document for user: {user_id}")
            
            # Add HIPAA-required metadata
            metadata.update({
                "created_at": datetime.utcnow().isoformat(),
                "last_accessed": datetime.utcnow().isoformat(),
                "encryption_enabled": True,
                "hipaa_compliant": True
            })
            
            data = {
                "user_id": user_id,
                "metadata": metadata,
                "status": "pending",
                "encryption_key_id": self.encryption_key[:8],  # Store reference to key version
                "access_log": []
            }
            
            response = await self.supabase.table(self.table).insert(data).execute()
            
            if response.error:
                logger.error(f"Error creating document: {response.error}")
                return None
            
            # Create audit log entry
            await self.supabase.table(self.audit_table).insert({
                "user_id": user_id,
                "action": "document_created",
                "details": {
                    "document_id": response.data[0]["id"],
                    "timestamp": datetime.utcnow().isoformat()
                },
                "success": True
            }).execute()
                
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            return None

    async def update_document_status(self, document_id: str, status: str, message: Optional[str] = None) -> bool:
        """Update document status."""
        try:
            logger.info(f"Updating document {document_id} status to: {status}")
            data = {"status": status}
            if message:
                data["status_message"] = message
                
            response = await self.supabase.table(self.table).update(data).eq("id", document_id).execute()
            
            if response.error:
                logger.error(f"Error updating document status: {response.error}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error updating document status: {str(e)}")
            return False

    async def upload_document(self, file_path: Path, user_id: str, content_type: str) -> Optional[str]:
        """
        Upload a document with encryption and create its record.
        
        Args:
            file_path: Path to the file to upload
            user_id: ID of the user uploading the document
            content_type: MIME type of the document
            
        Returns:
            Document ID if successful, None otherwise
        """
        try:
            logger.info(f"Uploading document {file_path} for user {user_id}")
            
            # Read and encrypt file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
                encrypted_content = self.fernet.encrypt(file_content)

            # Upload encrypted content to storage
            storage_path = f"documents/{user_id}/{file_path.name}"
            response = await self.supabase.storage.from_('documents').upload(
                storage_path,
                encrypted_content,
                file_options={
                    'content-type': content_type,
                    'x-upsert': 'true',
                    'x-encrypted': 'true'
                }
            )

            if response.error:
                logger.error(f"Error uploading file: {response.error}")
                return None

            # Create document record with HIPAA metadata
            doc_data = {
                "user_id": user_id,
                "filename": file_path.name,
                "content_type": content_type,
                "status": "uploaded",
                "storage_path": storage_path,
                "encryption_enabled": True,
                "encryption_key_id": self.encryption_key[:8],
                "created_at": datetime.utcnow().isoformat(),
                "last_accessed": datetime.utcnow().isoformat(),
                "access_log": [],
                "hipaa_compliant": True
            }
            
            doc_response = await self.supabase.table(self.table).insert(doc_data).execute()

            if doc_response.error:
                logger.error(f"Error creating document record: {doc_response.error}")
                # Clean up uploaded file
                await self.supabase.storage.from_('documents').remove([storage_path])
                return None

            # Create audit log entry
            await self.supabase.table(self.audit_table).insert({
                "user_id": user_id,
                "action": "document_uploaded",
                "details": {
                    "document_id": doc_response.data[0]["id"],
                    "filename": file_path.name,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "success": True
            }).execute()

            return doc_response.data[0]["id"]

        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            return None

    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get document chunks."""
        try:
            logger.info(f"Fetching chunks for document: {document_id}")
            response = await self.supabase.table("document_chunks").select("*").eq("document_id", document_id).execute()
            
            if response.error:
                logger.error(f"Error getting document chunks: {response.error}")
                return []
                
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting document chunks: {str(e)}")
            return []

    async def get_document_vectors(self, document_id: str) -> List[Dict[str, Any]]:
        """Get document vectors."""
        try:
            logger.info(f"Fetching vectors for document: {document_id}")
            response = await self.supabase.table("document_vectors").select("*").eq("document_id", document_id).execute()
            
            if response.error:
                logger.error(f"Error getting document vectors: {response.error}")
                return []
                
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting document vectors: {str(e)}")
            return []

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and its associated data."""
        try:
            logger.info(f"Deleting document: {document_id}")
            
            # Get document info
            doc = await self.get_document(document_id, "")
            if not doc:
                return False

            # Delete from storage
            storage_response = await self.supabase.storage.from_('documents').remove([doc["storage_path"]])
            
            if storage_response.error:
                logger.error(f"Error deleting document from storage: {storage_response.error}")
                return False

            # Delete document record (this will cascade to chunks and vectors)
            delete_response = await self.supabase.table(self.table).delete().eq("id", document_id).execute()
            
            if delete_response.error:
                logger.error(f"Error deleting document record: {delete_response.error}")
                return False

            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False

async def get_document_service() -> DocumentService:
    """Get configured document service instance."""
    try:
        client = get_base_client()
        return DocumentService(client)
    except Exception as e:
        logger.error(f"Error creating document service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 