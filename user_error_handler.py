#!/usr/bin/env python3
"""
User-Facing Error Handler for Document Upload Issues
===================================================

This script provides user-friendly error handling and feedback for:
1. Documents with missing file paths
2. Documents stuck in processing 
3. Failed uploads requiring re-upload
"""

import sys
import os
from datetime import datetime, timedelta
from supabase import create_client, Client
from typing import List, Dict, Any, Optional

# TODO: Integrate with real notification service (SendGrid, Twilio, etc.)
# TODO: Add notification preference management (email, SMS, push)
# TODO: Implement notification templates in multiple languages
# TODO: Add escalation for critical errors

class DocumentErrorHandler:
    def __init__(self):
        # Initialize Supabase client
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError('❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables')
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def check_document_health(self, document_id: str) -> Dict[str, Any]:
        """Check the health status of a document and determine appropriate action"""
        try:
            # TODO: Add more sophisticated health checks
            # TODO: Check file storage integrity
            # TODO: Validate document metadata consistency
            
            # Get document details
            doc_result = self.supabase.table('documents').select('*').eq('id', document_id).execute()
            
            if not doc_result.data:
                return {
                    'status': 'missing_document',
                    'should_delete': True,
                    'user_message': 'Document record not found',
                    'technical_details': 'Document missing from database'
                }
            
            document = doc_result.data[0]
            
            # Check for missing file path
            if not document.get('file_path') and not document.get('storage_path'):
                return {
                    'status': 'missing_file',
                    'should_delete': True,
                    'user_message': 'File not properly uploaded',
                    'technical_details': 'No file_path or storage_path found',
                    'document': document
                }
            
            # Check processing status
            if document.get('status') == 'parsing' and document.get('progress_percentage', 0) == 0:
                return {
                    'status': 'processing_error',
                    'should_delete': True,
                    'user_message': 'Document processing failed to start',
                    'technical_details': 'Stuck at 0% progress',
                    'document': document
                }
            
            # Check for stuck processing
            if document.get('status') == 'parsing' and document.get('progress_percentage', 0) > 0:
                # Calculate how long it's been stuck
                from datetime import datetime, timezone
                try:
                    updated_time = datetime.fromisoformat(document['updated_at'].replace('Z', '+00:00'))
                    current_time = datetime.now(timezone.utc)
                    stuck_minutes = (current_time - updated_time).total_seconds() / 60
                    
                    if stuck_minutes > 30:  # Stuck for more than 30 minutes
                        return {
                            'status': 'stuck_processing',
                            'should_delete': True,
                            'user_message': f'Document processing timed out (stuck for {stuck_minutes:.1f} minutes)',
                            'technical_details': f'Processing stuck at {document.get("progress_percentage", 0)}%',
                            'document': document
                        }
                except Exception as e:
                    print(f"Error parsing timestamp: {e}")
            
            # Document appears healthy
            return {
                'status': 'healthy',
                'should_delete': False,
                'user_message': 'Document is processing normally',
                'technical_details': 'No issues detected',
                'document': document
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'should_delete': False,
                'user_message': 'Unable to check document status',
                'technical_details': f'Health check failed: {str(e)}'
            }
    
    def handle_user_error(self, document_id: str, user_id: str, notify_user: bool = True) -> Dict[str, Any]:
        """Handle a document error with user-friendly response"""
        # TODO: Add error analytics and tracking
        # TODO: Implement smart retry suggestions
        # TODO: Create escalation workflow for repeated failures
        
        health_check = self.check_document_health(document_id)
        
        result = {
            'document_id': document_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'health_check': health_check,
            'actions_taken': []
        }
        
        # Take appropriate action based on health check
        if health_check.get('should_delete'):
            try:
                # Delete the problematic document
                delete_result = self.delete_document_safely(document_id)
                result['actions_taken'].append('document_deleted')
                result['delete_result'] = delete_result
                
                print(f"🗑️ Deleted problematic document {document_id}")
                
            except Exception as e:
                result['actions_taken'].append('delete_failed')
                result['delete_error'] = str(e)
                print(f"❌ Failed to delete document {document_id}: {e}")
        
        # Generate user notification if requested
        if notify_user:
            notification = self.generate_user_notification(health_check, document_id)
            result['user_notification'] = notification
            
            if notification.get('should_send'):
                # TODO: Replace with actual notification service
                print(f"📧 User notification: {notification['message']}")
                result['actions_taken'].append('user_notified')
        
        return result
    
    def delete_document_safely(self, document_id: str) -> Dict[str, Any]:
        """Safely delete a document and related data"""
        # TODO: Add storage cleanup for actual files
        # TODO: Implement backup before deletion
        # TODO: Add audit logging for all deletions
        
        try:
            # Delete processing jobs first
            jobs_result = self.supabase.table('processing_jobs').delete().eq('document_id', document_id).execute()
            
            # Delete the document
            doc_result = self.supabase.table('documents').delete().eq('id', document_id).execute()
            
            return {
                'success': True,
                'jobs_deleted': len(jobs_result.data) if jobs_result.data else 0,
                'document_deleted': len(doc_result.data) if doc_result.data else 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_user_notification(self, health_check: Dict[str, Any], document_id: str) -> Dict[str, Any]:
        """Generate a user-friendly notification based on health check"""
        # TODO: Load notification templates from database
        # TODO: Personalize based on user preferences and history
        # TODO: Add support for rich media notifications (images, videos)
        # TODO: Implement A/B testing for notification effectiveness
        
        status = health_check['status']
        
        if status in ['missing_file', 'processing_error']:
            return {
                'should_send': True,
                'priority': 'high',
                'subject': 'Document Upload Failed',
                'message': f"""
Hi there,

We encountered an issue processing your document upload.

Issue: {health_check['user_message']}

What to do next:
1. Please try uploading your document again
2. Ensure your file is not corrupted or empty
3. If you continue having issues, please contact our support team

Document ID: {document_id}

Best regards,
The Insurance Navigator Team
                """.strip()
            }
        
        elif status == 'stuck_processing':
            return {
                'should_send': True,
                'priority': 'medium',
                'subject': 'Document Processing Delayed',
                'message': f"""
Hi there,

Your document is taking longer than usual to process.

Status: {health_check['user_message']}

What you can do:
1. Wait a bit longer - processing may complete soon
2. If you're in a hurry, try uploading the document again
3. Contact support if this happens repeatedly

Document ID: {document_id}

Best regards,
The Insurance Navigator Team
                """.strip()
            }
        
        else:
            return {
                'should_send': False,
                'message': 'No notification needed - document is healthy'
            }
    
    def create_user_support_ticket(self, user_id: str, document_id: str, issue_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create a support ticket for user issues that need manual intervention"""
        # TODO: Integrate with helpdesk system (Zendesk, Freshdesk, etc.)
        # TODO: Auto-categorize tickets based on error patterns
        # TODO: Add priority scoring based on user tier and issue severity
        
        ticket_data = {
            'user_id': user_id,
            'document_id': document_id,
            'issue_type': issue_details.get('status', 'unknown'),
            'priority': self._calculate_priority(issue_details),
            'description': issue_details.get('user_message', 'No description provided'),
            'technical_details': issue_details.get('technical_details', ''),
            'created_at': datetime.now().isoformat(),
            'status': 'open'
        }
        
        print(f"🎫 Support ticket created for user {user_id}: {ticket_data['issue_type']}")
        return ticket_data
    
    def _calculate_priority(self, issue_details: Dict[str, Any]) -> str:
        """Calculate support ticket priority based on issue details"""
        # TODO: Implement machine learning for priority prediction
        # TODO: Consider user subscription tier in priority calculation
        
        status = issue_details.get('status', '')
        
        if status in ['missing_file', 'processing_error']:
            return 'high'
        elif status == 'stuck_processing':
            return 'medium'
        else:
            return 'low'
    
    def scan_user_documents(self, user_id: str, hours_back: int = 24) -> Dict[str, Any]:
        """Scan all documents for a user and identify any issues"""
        cutoff_time = (datetime.now() - timedelta(hours=hours_back)).isoformat()
        
        try:
            # Get user's recent documents
            docs_result = self.supabase.table('documents').select('*').eq('user_id', user_id).gte('created_at', cutoff_time).execute()
            
            if not docs_result.data:
                return {
                    'user_id': user_id,
                    'documents_found': 0,
                    'issues_found': 0,
                    'healthy_documents': 0
                }
            
            issues = []
            healthy = []
            
            for doc in docs_result.data:
                health_check = self.check_document_health(doc['id'])
                
                if health_check['status'] != 'healthy':
                    issues.append({
                        'document_id': doc['id'],
                        'filename': doc['original_filename'],
                        'health_check': health_check
                    })
                else:
                    healthy.append(doc['id'])
            
            return {
                'user_id': user_id,
                'documents_found': len(docs_result.data),
                'issues_found': len(issues),
                'healthy_documents': len(healthy),
                'issues': issues,
                'scan_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'user_id': user_id,
                'error': str(e),
                'scan_time': datetime.now().isoformat()
            }

def example_usage():
    """Example of how to use the error handler"""
    print('🔍 Document Error Handler - Example Usage')
    print('=' * 50)
    
    handler = DocumentErrorHandler()
    
    # Example 1: Check a specific document
    print('\n📄 Example 1: Check specific document health')
    
    # Get a recent document to test with
    recent_docs = handler.supabase.table('documents').select('id, original_filename, status').limit(1).execute()
    
    if recent_docs.data:
        doc_id = recent_docs.data[0]['id']
        print(f"Checking document: {recent_docs.data[0]['original_filename']} ({doc_id[:8]}...)")
        
        health_check = handler.check_document_health(doc_id)
        print(f"Health status: {health_check['status']}")
        print(f"User message: {health_check['user_message']}")
        print(f"Action required: {health_check['action_required']}")
    
    # Example 2: Scan for problematic documents
    print('\n🔍 Example 2: Scan for problematic documents')
    
    # Find documents with issues
    problematic = handler.supabase.table('documents').select('id, original_filename, user_id, status').in_('status', ['parsing', 'error']).limit(5).execute()
    
    if problematic.data:
        print(f"Found {len(problematic.data)} potentially problematic documents:")
        
        for doc in problematic.data:
            health_check = handler.check_document_health(doc['id'])
            print(f"  • {doc['original_filename']} ({doc['id'][:8]}...): {health_check['status']}")
            
            if health_check['action_required'] != 'none':
                print(f"    Action: {health_check['action_required']}")
    else:
        print("No problematic documents found!")

if __name__ == '__main__':
    example_usage() 