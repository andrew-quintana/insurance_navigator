#!/usr/bin/env python3
"""
Fix Documents with Null File Paths
=================================

This script:
1. Identifies documents with null file_path but valid storage_path
2. Updates file_path to match storage_path for stuck documents
3. Implements cleanup for truly broken documents
4. Provides user-facing error handling for future uploads
"""

import sys
import os
from datetime import datetime, timedelta
from supabase import create_client, Client
from typing import List, Dict, Any

class NullFilePathFixer:
    def __init__(self):
        # Initialize Supabase client
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError('❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables')
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
    def analyze_problem(self) -> Dict[str, Any]:
        """Analyze the scope of the null file_path problem"""
        print('🔍 Analyzing Null File Path Problem')
        print('=' * 50)
        
        # Get documents with null file_path
        null_file_path = self.supabase.table('documents').select('*').is_('file_path', 'null').execute().data
        
        # Categorize the problems
        fixable = []  # Has storage_path, can be fixed
        broken = []   # No storage_path or file reference
        
        for doc in null_file_path:
            if doc.get('storage_path'):
                fixable.append(doc)
            else:
                broken.append(doc)
        
        print(f'📊 Analysis Results:')
        print(f'  • Total documents with null file_path: {len(null_file_path)}')
        print(f'  • Fixable (has storage_path): {len(fixable)}')
        print(f'  • Broken (no file reference): {len(broken)}')
        
        return {
            'total_null': len(null_file_path),
            'fixable': fixable,
            'broken': broken
        }
    
    def fix_null_file_paths(self, fixable_docs: List[Dict]) -> Dict[str, Any]:
        """Fix documents by copying storage_path to file_path"""
        print(f'\n🔧 Fixing {len(fixable_docs)} documents with null file_path...')
        
        fixed = []
        failed = []
        
        for doc in fixable_docs:
            try:
                doc_id = doc['id']
                storage_path = doc['storage_path']
                
                # Update file_path to match storage_path
                result = self.supabase.table('documents').update({
                    'file_path': storage_path,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', doc_id).execute()
                
                if result.data:
                    fixed.append(doc_id)
                    print(f'  ✅ Fixed: {doc["original_filename"]} ({doc_id[:8]}...)')
                else:
                    failed.append({'id': doc_id, 'error': 'No data returned'})
                    print(f'  ❌ Failed: {doc["original_filename"]} ({doc_id[:8]}...)')
                    
            except Exception as e:
                failed.append({'id': doc_id, 'error': str(e)})
                print(f'  ❌ Error fixing {doc["original_filename"]}: {e}')
        
        return {
            'fixed_count': len(fixed),
            'failed_count': len(failed),
            'fixed_ids': fixed,
            'failed_details': failed
        }
    
    def cleanup_broken_documents(self, broken_docs: List[Dict], confirm: bool = False) -> Dict[str, Any]:
        """Clean up documents that have no file reference at all"""
        if not broken_docs:
            print('\n✅ No broken documents found to clean up')
            return {'deleted_count': 0, 'deleted_ids': []}
            
        print(f'\n🗑️ Found {len(broken_docs)} broken documents with no file reference')
        
        if not confirm:
            print('⚠️ DRY RUN: Would delete the following documents:')
            for doc in broken_docs:
                age = (datetime.now() - datetime.fromisoformat(doc['created_at'].replace('Z', '+00:00'))).total_seconds() / 3600
                print(f'  • {doc["original_filename"]} ({doc["id"][:8]}...) - Age: {age:.1f}h - Status: {doc["status"]}')
            
            print('\n💡 To actually delete these documents, call with confirm=True')
            return {'deleted_count': 0, 'deleted_ids': [], 'dry_run': True}
        
        # Actually delete broken documents
        deleted = []
        failed = []
        
        for doc in broken_docs:
            try:
                doc_id = doc['id']
                
                # First delete any related processing jobs
                job_result = self.supabase.table('processing_jobs').delete().eq('document_id', doc_id).execute()
                
                # Then delete the document
                doc_result = self.supabase.table('documents').delete().eq('id', doc_id).execute()
                
                if doc_result.data or doc_result.status_code == 204:  # 204 = successful deletion
                    deleted.append(doc_id)
                    print(f'  🗑️ Deleted: {doc["original_filename"]} ({doc_id[:8]}...)')
                else:
                    failed.append({'id': doc_id, 'error': 'Delete operation failed'})
                    print(f'  ❌ Failed to delete: {doc["original_filename"]} ({doc_id[:8]}...)')
                    
            except Exception as e:
                failed.append({'id': doc_id, 'error': str(e)})
                print(f'  ❌ Error deleting {doc["original_filename"]}: {e}')
        
        return {
            'deleted_count': len(deleted),
            'failed_count': len(failed),
            'deleted_ids': deleted,
            'failed_details': failed
        }
    
    def update_doc_parser_function(self):
        """Generate updated doc-parser code that handles both file_path and storage_path"""
        print('\n🔧 Doc-Parser Update Recommendation')
        print('-' * 40)
        
        updated_code = '''
// Updated doc-parser download logic to handle both file_path and storage_path
const downloadPath = document.file_path || document.storage_path;

if (!downloadPath) {
    console.error('❌ Neither file_path nor storage_path found for document:', documentId);
    await updateDocumentError(supabase, documentId, 'No file path found - please re-upload document');
    return new Response(
        JSON.stringify({ error: 'No file path found - please re-upload document' }),
        { status: 400 }
    );
}

console.log('⬇️ Downloading file from storage path:', downloadPath);
const { data: fileData, error: downloadError } = await supabase.storage
    .from('raw_documents')
    .download(downloadPath);
'''
        
        print('💡 The doc-parser function should be updated to handle both file_path and storage_path:')
        print(updated_code)
        
        return updated_code
    
    def create_validation_trigger(self):
        """Generate SQL for a database trigger to validate file paths on insert/update"""
        print('\n🛡️ Database Validation Trigger')
        print('-' * 40)
        
        trigger_sql = '''
-- Trigger to ensure documents always have a file reference
CREATE OR REPLACE FUNCTION validate_document_file_path()
RETURNS TRIGGER AS $$
BEGIN
    -- Ensure at least one file path field is populated
    IF NEW.file_path IS NULL AND NEW.storage_path IS NULL THEN
        RAISE EXCEPTION 'Document must have either file_path or storage_path populated';
    END IF;
    
    -- If only storage_path is set, copy it to file_path for compatibility
    IF NEW.file_path IS NULL AND NEW.storage_path IS NOT NULL THEN
        NEW.file_path := NEW.storage_path;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to documents table
DROP TRIGGER IF EXISTS ensure_document_file_path ON documents;
CREATE TRIGGER ensure_document_file_path
    BEFORE INSERT OR UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION validate_document_file_path();
'''
        
        print('💡 Database trigger to automatically sync file_path and storage_path:')
        print(trigger_sql)
        
        return trigger_sql
    
    def run_complete_fix(self, confirm_deletions: bool = False) -> Dict[str, Any]:
        """Run the complete fix process"""
        print('🚀 Running Complete Null File Path Fix')
        print('=' * 60)
        
        # Step 1: Analyze the problem
        analysis = self.analyze_problem()
        
        # Step 2: Fix documents with storage_path
        fix_results = self.fix_null_file_paths(analysis['fixable'])
        
        # Step 3: Clean up truly broken documents
        cleanup_results = self.cleanup_broken_documents(analysis['broken'], confirm=confirm_deletions)
        
        # Step 4: Provide update recommendations
        self.update_doc_parser_function()
        self.create_validation_trigger()
        
        # Summary
        total_processed = fix_results['fixed_count'] + cleanup_results['deleted_count']
        
        print(f'\n📊 Complete Fix Summary:')
        print(f'  • Documents analyzed: {analysis["total_null"]}')
        print(f'  • Documents fixed: {fix_results["fixed_count"]}')
        print(f'  • Documents deleted: {cleanup_results["deleted_count"]}')
        print(f'  • Total processed: {total_processed}')
        
        if fix_results['failed_count'] > 0:
            print(f'  • Fix failures: {fix_results["failed_count"]}')
        
        if cleanup_results.get('failed_count', 0) > 0:
            print(f'  • Deletion failures: {cleanup_results["failed_count"]}')
        
        return {
            'analysis': analysis,
            'fix_results': fix_results,
            'cleanup_results': cleanup_results,
            'total_processed': total_processed
        }


def main():
    """Main execution function"""
    print('🔧 Insurance Navigator - Null File Path Fixer')
    print('=' * 60)
    
    try:
        fixer = NullFilePathFixer()
        
        # Run analysis and fixes
        results = fixer.run_complete_fix(confirm_deletions=False)  # Set to True to actually delete broken docs
        
        if results['total_processed'] > 0:
            print(f'\n✅ Successfully processed {results["total_processed"]} documents!')
            print('\n🔄 Next steps:')
            print('  1. Deploy the updated doc-parser function')
            print('  2. Apply the database trigger (optional)')
            print('  3. Test document processing')
            print('  4. Monitor for any remaining issues')
        else:
            print('\n✅ No documents needed fixing!')
            
    except Exception as e:
        print(f'❌ Error running fix: {e}')
        return 1
    
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 