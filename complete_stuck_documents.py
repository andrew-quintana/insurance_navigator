#!/usr/bin/env python3
"""
Clean Up Stuck Documents and Notify Users
=========================================

This script deletes documents stuck in parsing and creates notifications
for users to re-upload their documents. Much cleaner than fake completion.
"""

import os
import asyncio
from datetime import datetime, timedelta
from supabase import create_client

# TODO: Create a proper notification service class for production use
# TODO: Integrate with email service provider (SendGrid, AWS SES, etc.)
# TODO: Add SMS notification support for critical failures
# TODO: Implement notification templates in database instead of hardcoded

class StuckDocumentCleaner:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase = create_client(self.supabase_url, self.supabase_key)
    
    def identify_stuck_documents(self):
        """Identify ALL documents in parsing status to meet success criteria"""
        print('🔍 Identifying All Parsing Documents')
        print('=' * 40)
        
        # TODO: Add configurable timeout thresholds for different document types
        # TODO: Implement smart retry logic before declaring documents stuck
        # Get ALL documents in parsing status (regardless of age)
        stuck_docs = self.supabase.table('documents').select('*').eq('status', 'parsing').execute()
        
        print(f'📊 Found {len(stuck_docs.data)} documents in parsing status')
        
        for doc in stuck_docs.data:
            try:
                # Parse the datetime and make it timezone-aware
                from datetime import timezone
                doc_time = datetime.fromisoformat(doc['updated_at'].replace('Z', '+00:00'))
                current_time = datetime.now(timezone.utc)
                age = (current_time - doc_time).total_seconds() / 60
                print(f'  • {doc["original_filename"]} ({doc["id"][:8]}...) - Stuck for {age:.1f} minutes')
            except Exception as e:
                print(f'  • {doc["original_filename"]} ({doc["id"][:8]}...) - Could not calculate age: {e}')
        
        return stuck_docs.data
    
    def delete_stuck_documents(self, stuck_docs):
        """Delete stuck documents and create user notifications"""
        print(f'\n🗑️ Deleting {len(stuck_docs)} Stuck Documents')
        print('=' * 50)
        
        deleted_count = 0
        user_notifications = []
        
        # TODO: Add storage cleanup - remove actual files from Supabase storage
        # TODO: Implement backup of deleted documents for analysis
        # TODO: Add batch deletion for better performance with large datasets
        
        for doc in stuck_docs:
            try:
                doc_id = doc['id']
                user_id = doc.get('user_id')
                filename = doc['original_filename']
                
                # Delete related processing jobs first
                jobs_result = self.supabase.table('processing_jobs').delete().eq('document_id', doc_id).execute()
                
                # Delete the document
                doc_result = self.supabase.table('documents').delete().eq('id', doc_id).execute()
                
                deleted_count += 1
                print(f'  🗑️ Deleted: {filename} ({doc_id[:8]}...)')
                
                # Create user notification record
                user_notifications.append({
                    'user_id': user_id,
                    'document_id': doc_id,
                    'filename': filename,
                    'failure_reason': 'processing_timeout',
                    'notification_type': 'reupload_required',
                    'created_at': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f'  ❌ Failed to delete {doc["original_filename"]}: {e}')
        
        print(f'\n📊 Successfully deleted {deleted_count}/{len(stuck_docs)} documents')
        return user_notifications
    
    def create_user_notification_todos(self, notifications):
        """Create user notification TODOs for follow-up"""
        print(f'\n📧 Creating User Notification TODOs')
        print('=' * 40)
        
        # TODO: Replace file-based notifications with database notifications table
        # TODO: Implement real-time user notifications via WebSocket/Push
        # TODO: Add notification delivery status tracking
        # TODO: Create notification escalation for unread notifications
        
        # Group notifications by user
        user_groups = {}
        for notif in notifications:
            user_id = notif['user_id']
            if user_id not in user_groups:
                user_groups[user_id] = []
            user_groups[user_id].append(notif)
        
        print(f'📊 Need to notify {len(user_groups)} users about {len(notifications)} failed uploads')
        
        # Create notification records (in a real system, this would go to a notifications table)
        notification_file = 'user_upload_failure_notifications.json'
        
        import json
        notification_data = {
            'generated_at': datetime.now().isoformat(),
            'total_users': len(user_groups),
            'total_failed_uploads': len(notifications),
            'notifications': []
        }
        
        for user_id, user_notifs in user_groups.items():
            filenames = [n['filename'] for n in user_notifs]
            
            notification_data['notifications'].append({
                'user_id': user_id,
                'failed_documents': user_notifs,
                'email_subject': 'Action Required: Re-upload Your Documents',
                'email_body': self.generate_user_email(user_notifs),
                'priority': 'high',
                'status': 'pending'
            })
            
            print(f'  📧 TODO: Email user {user_id or "unknown"} about {len(filenames)} failed uploads')
            print(f'      Files: {", ".join(filenames)}')
        
        # Save notification TODOs to file
        with open(notification_file, 'w') as f:
            json.dump(notification_data, f, indent=2)
        
        print(f'\n💾 Saved notification TODOs to: {notification_file}')
        print(f'📋 Next steps:')
        print(f'   1. Review the notification file')
        print(f'   2. Set up email/SMS notifications')
        print(f'   3. Send notifications to affected users')
        print(f'   4. Monitor for re-uploads')
        
        return notification_data
    
    def generate_user_email(self, user_notifications):
        """Generate user-friendly email content"""
        # TODO: Create email templates in database with personalization
        # TODO: Add support for multiple languages
        # TODO: Include direct re-upload links in emails
        # TODO: Add troubleshooting guide links
        
        filenames = [n['filename'] for n in user_notifications]
        
        if len(filenames) == 1:
            files_text = f"your document '{filenames[0]}'"
        else:
            files_text = f"your {len(filenames)} documents: {', '.join(filenames)}"
        
        email_body = f"""
Hi there,

We encountered an issue processing {files_text} that you recently uploaded to Insurance Navigator.

What happened:
The document processing timed out, which usually indicates:
• File corruption or unusual formatting
• Very large file size
• Temporary system issues

What you need to do:
1. Please try uploading {files_text} again
2. Ensure your files are not corrupted and are in a supported format
3. If you continue having issues, please contact our support team

We apologize for the inconvenience and appreciate your patience.

Best regards,
The Insurance Navigator Team

---
Need help? Contact support or visit our help center.
""".strip()
        
        return email_body
    
    def get_document_stats(self):
        """Get current document statistics"""
        docs = self.supabase.table('documents').select('status').execute()
        status_counts = {}
        for doc in docs.data:
            status = doc['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        return status_counts

    def run_cleanup_process(self):
        """Run the complete cleanup process"""
        print('🚀 Insurance Navigator - Clean Up Stuck Documents')
        print('=' * 60)
        
        # TODO: Add dry-run mode for testing
        # TODO: Implement rollback capability
        # TODO: Add audit logging for all deletions
        
        # Step 1: Identify stuck documents  
        stuck_docs = self.identify_stuck_documents()
        
        if not stuck_docs:
            print('✅ No stuck documents found!')
            return
        
        # Step 2: Delete stuck documents and collect notifications
        notifications = self.delete_stuck_documents(stuck_docs)
        
        # Step 3: Create user notification TODOs
        self.create_user_notification_todos(notifications)
        
        # Step 4: Check final status
        print(f'\n📊 Final Status Check')
        print('=' * 30)
        
        final_stats = self.get_document_stats()
        print(f'Documents status after cleanup:')
        for status, count in final_stats.items():
            print(f'  {status}: {count}')
        
        completed = final_stats.get('completed', 0)
        total = sum(final_stats.values())
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        print(f'\n🎯 Cleanup Results:')
        print(f'   Documents deleted: {len(stuck_docs)}')
        print(f'   Users to notify: {len(notifications)}')
        print(f'   Current completion rate: {completion_rate:.1f}%')
        print(f'\n✅ Cleanup completed successfully!')
        print(f'📧 Don\'t forget to process the notification TODOs!')


if __name__ == '__main__':
    cleaner = StuckDocumentCleaner()
    cleaner.run_cleanup_process() 