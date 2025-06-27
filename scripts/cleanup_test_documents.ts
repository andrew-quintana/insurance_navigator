import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const RETENTION_HOURS = 24 // Keep successful documents younger than this
const MAX_FAILED_RETENTION_HOURS = 72 // Keep failed documents for longer for debugging

// Initialize Supabase client
const supabase = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
)

async function cleanupTestDocuments() {
  console.log('🧹 Starting cleanup process...')
  
  try {
    // 1. Get documents to clean up
    const retentionDate = new Date()
    retentionDate.setHours(retentionDate.getHours() - RETENTION_HOURS)
    
    const failedRetentionDate = new Date()
    failedRetentionDate.setHours(failedRetentionDate.getHours() - MAX_FAILED_RETENTION_HOURS)

    // Get documents to delete
    const { data: documentsToDelete, error: docError } = await supabase
      .from('documents')
      .select('id, status, storage_path, created_at')
      .or(
        `created_at.lt.${retentionDate.toISOString()},and(status.eq.failed,created_at.lt.${failedRetentionDate.toISOString()})`
      )

    if (docError) {
      throw new Error(`Failed to fetch documents: ${docError.message}`)
    }

    if (!documentsToDelete?.length) {
      console.log('✅ No documents to clean up')
      return
    }

    console.log(`📄 Found ${documentsToDelete.length} documents to clean up`)

    // 2. Delete associated processing jobs first
    const documentIds = documentsToDelete.map(d => d.id)
    const { error: jobError } = await supabase
      .from('processing_jobs')
      .delete()
      .in('document_id', documentIds)

    if (jobError) {
      console.error('⚠️ Failed to delete processing jobs:', jobError)
      // Continue with document cleanup even if job cleanup fails
    }

    // 3. Delete documents from storage
    const storagePaths = documentsToDelete
      .filter(d => d.storage_path)
      .map(d => d.storage_path)

    if (storagePaths.length > 0) {
      const { error: storageError } = await supabase.storage
        .from('documents')
        .remove(storagePaths)

      if (storageError) {
        console.error('⚠️ Failed to delete some storage files:', storageError)
        // Continue with document record cleanup even if storage cleanup fails
      }
    }

    // 4. Delete document records
    const { error: deleteError } = await supabase
      .from('documents')
      .delete()
      .in('id', documentIds)

    if (deleteError) {
      throw new Error(`Failed to delete documents: ${deleteError.message}`)
    }

    console.log('✅ Cleanup completed successfully:', {
      documentsDeleted: documentIds.length,
      storagePathsDeleted: storagePaths.length
    })

  } catch (error) {
    console.error('❌ Cleanup failed:', error)
    throw error
  }
}

// Run cleanup
cleanupTestDocuments()
  .catch(console.error)
  .finally(() => {
    console.log('🏁 Cleanup script finished')
  }) 