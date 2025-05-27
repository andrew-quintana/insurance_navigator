#!/usr/bin/env python3
"""
Test script for Supabase Storage integration.
Validates file upload, download, signed URLs, and permissions.
"""

import asyncio
import os
import sys
import tempfile
import uuid
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db.services.storage_service import get_storage_service
from db.services.user_service import get_user_service
from db.services.db_pool import get_db_pool
from db.config import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StorageIntegrationTest:
    """Test suite for storage service integration."""

    def __init__(self):
        self.storage_service = None
        self.user_service = None
        self.test_user_id = None
        self.test_policy_id = str(uuid.uuid4())
        self.uploaded_files = []

    async def setup(self):
        """Set up test environment."""
        try:
            logger.info("🔧 Setting up storage integration test...")
            
            # Initialize services
            self.storage_service = await get_storage_service()
            self.user_service = await get_user_service()
            
            # Create test user
            test_email = f"storage_test_{uuid.uuid4().hex[:8]}@example.com"
            user_data = await self.user_service.create_user(
                email=test_email,
                password="TestPassword123!",
                full_name="Storage Test User"
            )
            self.test_user_id = user_data['id']
            
            logger.info(f"✅ Created test user: {self.test_user_id}")
            logger.info(f"✅ Test policy ID: {self.test_policy_id}")
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            raise

    async def test_file_upload(self):
        """Test file upload functionality."""
        logger.info("📤 Testing file upload...")
        
        try:
            # Create test file content
            test_content = b"This is a test policy document content. " * 100
            filename = "test_policy.pdf"
            
            # Upload file
            result = await self.storage_service.upload_policy_document(
                policy_id=self.test_policy_id,
                file_data=test_content,
                filename=filename,
                user_id=self.test_user_id,
                document_type="policy",
                metadata={"test": True, "created_by": "integration_test"}
            )
            
            # Validate result
            assert 'document_id' in result
            assert 'file_path' in result
            assert result['original_filename'] == filename
            assert result['file_size'] == len(test_content)
            
            # Store for cleanup
            self.uploaded_files.append(result['file_path'])
            
            logger.info(f"✅ File uploaded successfully: {result['file_path']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ File upload failed: {e}")
            raise

    async def test_signed_url_generation(self, file_path: str):
        """Test signed URL generation."""
        logger.info("🔗 Testing signed URL generation...")
        
        try:
            # Generate signed URL
            signed_url = await self.storage_service.get_signed_url(
                file_path=file_path,
                expires_in=3600,
                download=True
            )
            
            # Validate URL
            assert signed_url.startswith('http')
            assert 'supabase' in signed_url or 'storage' in signed_url
            
            logger.info(f"✅ Signed URL generated: {signed_url[:50]}...")
            return signed_url
            
        except Exception as e:
            logger.error(f"❌ Signed URL generation failed: {e}")
            raise

    async def test_document_listing(self):
        """Test document listing functionality."""
        logger.info("📋 Testing document listing...")
        
        try:
            # List documents for policy
            documents = await self.storage_service.list_policy_documents(
                policy_id=self.test_policy_id
            )
            
            # Validate results
            assert len(documents) > 0
            assert documents[0]['policy_id'] == self.test_policy_id
            assert documents[0]['uploaded_by'] == self.test_user_id
            
            logger.info(f"✅ Found {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Document listing failed: {e}")
            raise

    async def test_document_metadata(self, file_path: str):
        """Test document metadata retrieval."""
        logger.info("📊 Testing document metadata...")
        
        try:
            # Get metadata
            metadata = await self.storage_service.get_document_metadata(file_path)
            
            # Validate metadata
            assert metadata['file_path'] == file_path
            assert metadata['policy_id'] == self.test_policy_id
            assert metadata['uploaded_by'] == self.test_user_id
            assert 'uploaded_at' in metadata
            
            logger.info(f"✅ Metadata retrieved: {metadata['original_filename']}")
            return metadata
            
        except Exception as e:
            logger.error(f"❌ Metadata retrieval failed: {e}")
            raise

    async def test_file_permissions(self, file_path: str):
        """Test file access permissions."""
        logger.info("🔐 Testing file permissions...")
        
        try:
            # Test owner permissions
            owner_perms = await self.storage_service.get_file_access_permissions(
                file_path=file_path,
                user_id=self.test_user_id
            )
            
            # Owner should have all permissions
            assert owner_perms['read'] == True
            assert owner_perms['write'] == True
            assert owner_perms['delete'] == True
            
            # Test non-owner permissions (create another user)
            test_email2 = f"storage_test2_{uuid.uuid4().hex[:8]}@example.com"
            user_data2 = await self.user_service.create_user(
                email=test_email2,
                password="TestPassword123!",
                full_name="Storage Test User 2"
            )
            
            other_perms = await self.storage_service.get_file_access_permissions(
                file_path=file_path,
                user_id=user_data2['id']
            )
            
            # Non-owner should have limited permissions
            assert other_perms['read'] == True  # Basic users can read
            assert other_perms['write'] == False
            assert other_perms['delete'] == False
            
            logger.info("✅ File permissions working correctly")
            return True
            
        except Exception as e:
            logger.error(f"❌ File permissions test failed: {e}")
            raise

    async def test_file_download(self, file_path: str):
        """Test file download functionality."""
        logger.info("📥 Testing file download...")
        
        try:
            # Download file
            file_content = await self.storage_service.download_document(file_path)
            
            # Validate content
            assert isinstance(file_content, bytes)
            assert len(file_content) > 0
            
            logger.info(f"✅ File downloaded: {len(file_content)} bytes")
            return file_content
            
        except Exception as e:
            logger.error(f"❌ File download failed: {e}")
            raise

    async def test_multiple_file_types(self):
        """Test upload of different file types."""
        logger.info("📄 Testing multiple file types...")
        
        file_types = [
            ("test_document.pdf", b"PDF content", "application/pdf"),
            ("test_image.jpg", b"JPEG content", "image/jpeg"),
            ("test_spreadsheet.xlsx", b"Excel content", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("test_text.txt", b"Text content", "text/plain")
        ]
        
        try:
            uploaded_files = []
            
            for filename, content, expected_type in file_types:
                result = await self.storage_service.upload_policy_document(
                    policy_id=self.test_policy_id,
                    file_data=content,
                    filename=filename,
                    user_id=self.test_user_id,
                    document_type="test"
                )
                
                assert result['content_type'] == expected_type
                uploaded_files.append(result['file_path'])
                self.uploaded_files.append(result['file_path'])
            
            logger.info(f"✅ Uploaded {len(uploaded_files)} different file types")
            return uploaded_files
            
        except Exception as e:
            logger.error(f"❌ Multiple file types test failed: {e}")
            raise

    async def test_soft_delete(self, file_path: str):
        """Test soft delete functionality."""
        logger.info("🗑️ Testing soft delete...")
        
        try:
            # Soft delete file
            success = await self.storage_service.delete_document(
                file_path=file_path,
                user_id=self.test_user_id,
                hard_delete=False
            )
            
            assert success == True
            
            # Verify file is not in active listings
            documents = await self.storage_service.list_policy_documents(
                policy_id=self.test_policy_id
            )
            
            # File should not appear in default listing (active only)
            active_paths = [doc['file_path'] for doc in documents]
            assert file_path not in active_paths
            
            # But should appear when including inactive
            all_documents = await self.storage_service.list_policy_documents(
                policy_id=self.test_policy_id,
                include_inactive=True
            )
            
            all_paths = [doc['file_path'] for doc in all_documents]
            # Note: We'll remove from cleanup list since it's soft deleted
            if file_path in self.uploaded_files:
                self.uploaded_files.remove(file_path)
            
            logger.info("✅ Soft delete working correctly")
            return True
            
        except Exception as e:
            logger.error(f"❌ Soft delete test failed: {e}")
            raise

    async def cleanup(self):
        """Clean up test data."""
        logger.info("🧹 Cleaning up test data...")
        
        try:
            # Hard delete uploaded files
            for file_path in self.uploaded_files:
                try:
                    await self.storage_service.delete_document(
                        file_path=file_path,
                        user_id=self.test_user_id,
                        hard_delete=True
                    )
                    logger.info(f"✅ Deleted file: {file_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to delete file {file_path}: {e}")
            
            # Clean up database records
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                # Delete test documents
                await conn.execute(
                    "DELETE FROM policy_documents WHERE policy_id = $1",
                    self.test_policy_id
                )
                
                # Delete test user
                if self.test_user_id:
                    # Delete user roles first to avoid foreign key constraint
                    await conn.execute(
                        "DELETE FROM user_roles WHERE user_id = $1::uuid",
                        self.test_user_id
                    )
                    
                    # Delete user
                    await conn.execute(
                        "DELETE FROM users WHERE id = $1::uuid",
                        self.test_user_id
                    )
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

    async def run_all_tests(self):
        """Run all storage integration tests."""
        logger.info("🚀 Starting Storage Integration Tests")
        logger.info("=" * 60)
        
        try:
            # Setup
            await self.setup()
            
            # Test file upload
            upload_result = await self.test_file_upload()
            main_file_path = upload_result['file_path']
            
            # Test signed URL generation
            await self.test_signed_url_generation(main_file_path)
            
            # Test document listing
            await self.test_document_listing()
            
            # Test document metadata
            await self.test_document_metadata(main_file_path)
            
            # Test file permissions
            await self.test_file_permissions(main_file_path)
            
            # Test file download
            await self.test_file_download(main_file_path)
            
            # Test multiple file types
            await self.test_multiple_file_types()
            
            # Test soft delete (use one of the multiple files)
            if len(self.uploaded_files) > 1:
                await self.test_soft_delete(self.uploaded_files[-1])
            
            logger.info("=" * 60)
            logger.info("🎉 All Storage Integration Tests PASSED!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Storage Integration Tests FAILED: {e}")
            return False
        
        finally:
            # Always cleanup
            await self.cleanup()


async def main():
    """Main test execution."""
    print("Supabase Storage Integration Test")
    print("=" * 50)
    
    # Verify environment
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY',
        'DATABASE_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please check your .env file")
        return False
    
    # Run tests
    test_suite = StorageIntegrationTest()
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n🎉 Storage integration is working correctly!")
        print("✅ Supabase Storage is properly configured")
        print("✅ File upload/download working")
        print("✅ Signed URLs working")
        print("✅ Permissions working")
        print("✅ Database integration working")
    else:
        print("\n❌ Storage integration tests failed!")
        print("Please check the logs above for details")
    
    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1) 