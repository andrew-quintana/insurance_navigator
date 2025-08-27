"""
Upload Pipeline RAG Configuration

This module provides RAG configuration for agents to query upload_pipeline vectors directly.
It extends the existing RAG system to work with the upload pipeline schema.
"""

from typing import Optional
from .core import RetrievalConfig


class UploadPipelineRAGConfig(RetrievalConfig):
    """
    RAG configuration for querying upload_pipeline vectors directly.
    
    This configuration allows agents to perform semantic search on the upload_pipeline
    document_chunks table without needing a bridge schema.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize upload pipeline RAG configuration.
        
        Args:
            **kwargs: Additional configuration parameters
        """
        super().__init__(**kwargs)
        
        # Upload pipeline specific configuration
        self.schema_name = "upload_pipeline"
        self.chunks_table = "document_chunks"
        self.chunks_id_column = "chunk_id"
        self.embedding_column = "embedding_vector"
        self.content_column = "chunk_text"
        self.metadata_column = "chunk_metadata"
        self.user_id_column = "user_id"
        self.document_id_column = "document_id"
        self.chunk_index_column = "chunk_index"
        
        # RAG query configuration
        self.similarity_threshold = kwargs.get('similarity_threshold', 0.7)
        self.max_chunks = kwargs.get('max_chunks', 10)
        self.token_budget = kwargs.get('token_budget', 4000)
        
        # Vector search configuration
        self.vector_dimensions = 1536  # OpenAI text-embedding-3-small
        self.distance_metric = "cosine"  # pgvector cosine distance
        
        # Performance tuning
        self.use_prepared_statements = True
        self.enable_query_caching = False  # Disabled for initial implementation
        
    def get_similarity_query(self) -> str:
        """
        Get the SQL query for similarity search on upload_pipeline vectors.
        
        Returns:
            SQL query string for vector similarity search
        """
        return f"""
            SELECT 
                {self.chunks_id_column},
                {self.document_id_column},
                {self.user_id_column},
                {self.content_column},
                {self.metadata_column},
                {self.chunk_index_column},
                1 - ({self.embedding_column} <=> $1) AS similarity
            FROM {self.schema_name}.{self.chunks_table}
            WHERE {self.user_id_column} = $2
              AND {self.embedding_column} IS NOT NULL
              AND 1 - ({self.embedding_column} <=> $1) > $3
            ORDER BY {self.embedding_column} <=> $1
            LIMIT $4
        """
    
    def get_document_availability_query(self) -> str:
        """
        Get the SQL query for checking document availability by type.
        
        Returns:
            SQL query string for document availability check
        """
        return f"""
            SELECT DISTINCT d.document_type, COUNT(*) as doc_count
            FROM {self.schema_name}.documents d
            WHERE d.{self.user_id_column} = $1 
              AND d.document_id IN (
                SELECT document_id FROM {self.schema_name}.upload_jobs 
                WHERE status = 'complete'
              )
            GROUP BY d.document_type
        """
    
    def get_rag_ready_documents_query(self) -> str:
        """
        Get the SQL query for finding RAG-ready documents.
        
        Returns:
            SQL query string for RAG-ready documents
        """
        return f"""
            SELECT 
                d.document_id,
                d.filename,
                d.document_type,
                COUNT(dc.{self.chunks_id_column}) as chunk_count,
                AVG(vector_norm(dc.{self.embedding_column})) as avg_vector_norm
            FROM {self.schema_name}.documents d
            JOIN {self.schema_name}.upload_jobs uj ON d.document_id = uj.document_id
            LEFT JOIN {self.schema_name}.{self.chunks_table} dc ON d.document_id = dc.{self.document_id_column}
            WHERE uj.status = 'complete' AND d.{self.user_id_column} = $1
            GROUP BY d.document_id, d.filename, d.document_type
            HAVING COUNT(dc.{self.chunks_id_column}) > 0
        """
    
    def validate_config(self) -> bool:
        """
        Validate the upload pipeline RAG configuration.
        
        Returns:
            True if configuration is valid
        """
        try:
            # Check required fields
            required_fields = [
                'schema_name', 'chunks_table', 'embedding_column', 
                'content_column', 'user_id_column'
            ]
            
            for field in required_fields:
                if not hasattr(self, field) or not getattr(self, field):
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate similarity threshold
            if not 0.0 < self.similarity_threshold <= 1.0:
                raise ValueError("similarity_threshold must be in (0, 1]")
            
            # Validate max chunks
            if self.max_chunks <= 0:
                raise ValueError("max_chunks must be positive")
            
            # Validate token budget
            if self.token_budget <= 0:
                raise ValueError("token_budget must be positive")
            
            return True
            
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False
    
    def get_connection_string(self, db_config: dict) -> str:
        """
        Generate database connection string for upload_pipeline access.
        
        Args:
            db_config: Database configuration dictionary
            
        Returns:
            Database connection string
        """
        host = db_config.get('host', '127.0.0.1')
        port = db_config.get('port', 5432)
        user = db_config.get('user', 'postgres')
        password = db_config.get('password', 'postgres')
        database = db_config.get('database', 'accessa_dev')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def get_schema_search_path(self) -> str:
        """
        Get the PostgreSQL search path for upload_pipeline schema.
        
        Returns:
            Search path string
        """
        return f"{self.schema_name}, public"
    
    def __repr__(self) -> str:
        """String representation of the configuration."""
        return (
            f"UploadPipelineRAGConfig("
            f"schema={self.schema_name}, "
            f"table={self.chunks_table}, "
            f"similarity_threshold={self.similarity_threshold}, "
            f"max_chunks={self.max_chunks}, "
            f"token_budget={self.token_budget}"
            f")"
        )


# Default configuration instance
default_upload_pipeline_config = UploadPipelineRAGConfig()


def get_default_upload_pipeline_config() -> UploadPipelineRAGConfig:
    """Get the default upload pipeline RAG configuration."""
    return default_upload_pipeline_config


def create_upload_pipeline_config(**kwargs) -> UploadPipelineRAGConfig:
    """
    Create a custom upload pipeline RAG configuration.
    
    Args:
        **kwargs: Configuration parameters
        
    Returns:
        UploadPipelineRAGConfig instance
    """
    return UploadPipelineRAGConfig(**kwargs)
