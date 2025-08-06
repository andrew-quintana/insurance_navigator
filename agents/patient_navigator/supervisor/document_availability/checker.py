"""
Document Availability Checker for Patient Navigator Supervisor Workflow.

This module provides deterministic document availability checking for workflow orchestration.
It integrates with Supabase for document presence verification and supports mock mode for testing.
"""

import logging
import os
from typing import List, Optional
from supabase import create_client, Client

from ..models import WorkflowType, DocumentAvailabilityResult


class DocumentAvailabilityChecker:
    """
    Deterministic document availability checker for LangGraph nodes.
    
    This is not an agent-based component but a deterministic checker
    that integrates with Supabase for document presence verification.
    """
    
    def __init__(self, use_mock: bool = False, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """
        Initialize the document availability checker.
        
        Args:
            use_mock: If True, use mock responses for testing
            supabase_url: Supabase URL (if not provided, will try to get from environment)
            supabase_key: Supabase service role key (if not provided, will try to get from environment)
        """
        self.use_mock = use_mock
        self.logger = logging.getLogger("document_availability_checker")
        
        # Document requirements for MVP workflows
        self.document_requirements = {
            WorkflowType.INFORMATION_RETRIEVAL: ["insurance_policy", "benefits_summary"],
            WorkflowType.STRATEGY: ["insurance_policy", "benefits_summary"]
        }
        
        # Initialize Supabase client if not in mock mode
        self.supabase_client: Optional[Client] = None
        if not use_mock:
            try:
                # Use project's environment variable patterns
                supabase_url = supabase_url or os.getenv("SUPABASE_URL") or os.getenv("SUPABASE_DB_URL")
                supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
                
                if not supabase_url or not supabase_key:
                    self.logger.warning("Supabase credentials not provided, falling back to mock mode")
                    self.use_mock = True
                else:
                    # Create Supabase client with proper configuration
                    self.supabase_client = create_client(supabase_url, supabase_key)
                    
                    # Test connection
                    try:
                        # Simple test query to verify connection
                        test_response = self.supabase_client.table("documents").select("count").limit(1).execute()
                        self.logger.info("Successfully connected to Supabase for document availability checking")
                    except Exception as test_error:
                        self.logger.warning(f"Supabase connection test failed: {test_error}, falling back to mock mode")
                        self.use_mock = True
                        
            except Exception as e:
                self.logger.error(f"Failed to initialize Supabase client: {e}")
                self.use_mock = True
    
    async def check_availability(self, workflows: List[WorkflowType], user_id: str) -> DocumentAvailabilityResult:
        """
        Check document availability for prescribed workflows.
        
        Args:
            workflows: List of workflows that require documents
            user_id: User identifier for document access
            
        Returns:
            DocumentAvailabilityResult with availability status
        """
        try:
            self.logger.info(f"Checking document availability for user {user_id}")
            
            if self.use_mock:
                return self._mock_check_availability(workflows, user_id)
            
            # Determine required documents for prescribed workflows
            required_docs = self._get_required_documents(workflows)
            
            # Check document availability in Supabase
            available_docs = await self._check_documents_in_supabase(required_docs, user_id)
            missing_docs = [doc for doc in required_docs if doc not in available_docs]
            
            # Create document status mapping
            document_status = {doc: doc in available_docs for doc in required_docs}
            
            # Determine overall readiness
            is_ready = len(missing_docs) == 0
            
            self.logger.info(f"Document availability check completed for user {user_id}: {len(available_docs)} available, {len(missing_docs)} missing")
            
            return DocumentAvailabilityResult(
                is_ready=is_ready,
                available_documents=available_docs,
                missing_documents=missing_docs,
                document_status=document_status
            )
            
        except Exception as e:
            self.logger.error(f"Error checking document availability: {e}")
            # Return not ready on error
            return DocumentAvailabilityResult(
                is_ready=False,
                available_documents=[],
                missing_documents=required_docs if 'required_docs' in locals() else [],
                document_status={}
            )
    
    def _get_required_documents(self, workflows: List[WorkflowType]) -> List[str]:
        """
        Get required documents for prescribed workflows.
        
        Args:
            workflows: List of prescribed workflows
            
        Returns:
            List of required document types
        """
        required_docs = set()
        for workflow in workflows:
            if workflow in self.document_requirements:
                required_docs.update(self.document_requirements[workflow])
        
        return list(required_docs)
    
    async def _check_documents_in_supabase(self, required_docs: List[str], user_id: str) -> List[str]:
        """
        Check document availability in Supabase documents table.
        
        Args:
            required_docs: List of required document types
            user_id: User identifier
            
        Returns:
            List of available document types
        """
        if not self.supabase_client:
            self.logger.warning("No Supabase client available, using mock response")
            return self._mock_document_check(required_docs, user_id)
        
        try:
            self.logger.info(f"Checking documents in Supabase for user {user_id}")
            
            # Query documents table for user's documents with proper filtering
            response = self.supabase_client.table("documents").select(
                "document_type, status, created_at"
            ).eq("user_id", user_id).in_("document_type", required_docs).execute()
            
            if not response.data:
                self.logger.info(f"No documents found for user {user_id}")
                return []
            
            # Filter for available documents with valid status
            available_docs = []
            for doc in response.data:
                doc_type = doc.get("document_type")
                status = doc.get("status", "unknown")
                
                # Consider document available if it's in required list and has valid status
                if doc_type in required_docs and status in ["processed", "available", "active", "completed"]:
                    available_docs.append(doc_type)
                    self.logger.debug(f"Found available document: {doc_type} with status: {status}")
            
            self.logger.info(f"Found {len(available_docs)} available documents for user {user_id}")
            return available_docs
            
        except Exception as e:
            self.logger.error(f"Error checking documents in Supabase: {e}")
            # Fallback to mock response on error
            return self._mock_document_check(required_docs, user_id)
    
    def _mock_document_check(self, required_docs: List[str], user_id: str) -> List[str]:
        """
        Mock document availability checking for testing.
        
        Args:
            required_docs: List of required document types
            user_id: User identifier
            
        Returns:
            List of available document types
        """
        # Enhanced mock logic for Phase 4 testing
        available_docs = []
        
        # Mock logic: assume some documents are available based on user_id
        for doc in required_docs:
            # For testing: assume information_retrieval docs are available for most users
            if "policy" in doc or "benefits" in doc:
                # Make some users have documents, others don't
                if user_id.endswith("123") or user_id.endswith("456"):
                    available_docs.append(doc)
        
        return available_docs
    
    def _mock_check_availability(self, workflows: List[WorkflowType], user_id: str) -> DocumentAvailabilityResult:
        """
        Mock document availability checking for testing.
        
        Args:
            workflows: List of prescribed workflows
            user_id: User identifier
            
        Returns:
            Mock DocumentAvailabilityResult
        """
        required_docs = self._get_required_documents(workflows)
        
        # Enhanced mock logic for Phase 4 testing
        available_docs = []
        missing_docs = []
        
        for doc in required_docs:
            # Mock logic: vary availability based on user_id and workflow type
            if WorkflowType.INFORMATION_RETRIEVAL in workflows:
                # Information retrieval users typically have basic documents
                if doc in ["insurance_policy", "benefits_summary"]:
                    if user_id.endswith("123") or user_id.endswith("456"):
                        available_docs.append(doc)
                    else:
                        missing_docs.append(doc)
                else:
                    missing_docs.append(doc)
            else:
                # Strategy users need more documents
                if user_id.endswith("789"):
                    available_docs.append(doc)
                else:
                    missing_docs.append(doc)
        
        document_status = {doc: doc in available_docs for doc in required_docs}
        is_ready = len(missing_docs) == 0
        
        return DocumentAvailabilityResult(
            is_ready=is_ready,
            available_documents=available_docs,
            missing_documents=missing_docs,
            document_status=document_status
        ) 