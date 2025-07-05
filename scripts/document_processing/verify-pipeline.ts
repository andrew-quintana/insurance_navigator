import { createClient } from '@supabase/supabase-js';
import { displayProcessingResults } from '../../supabase/functions/tests/document_processing_test';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';

// Load environment variables
dotenv.config();

async function verifyPipeline() {
  // Initialize Supabase client
  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!supabaseUrl || !supabaseKey) {
    throw new Error('Missing required environment variables');
  }

  const supabase = createClient(supabaseUrl, supabaseKey);

  try {
    console.log('Starting pipeline verification...');

    // 1. Create a test user
    const testUserId = crypto.randomUUID();
    const { data: user, error: userError } = await supabase
      .from('users')
      .insert({
        id: testUserId,
        email: `test_${Date.now()}@example.com`,
        name: 'Test User'
      })
      .select()
      .single();

    if (userError) throw userError;

    // 2. Create a test document
    const { data: doc, error: docError } = await supabase
      .from('documents')
      .insert({
        user_id: testUserId,
        filename: 'scan_classic_hmo.pdf',
        content_type: 'application/pdf',
        status: 'processing',
        storage_path: `documents/${testUserId}/scan_classic_hmo.pdf`
      })
      .select()
      .single();

    if (docError) throw docError;

    // 3. Upload the test PDF
    const testFile = fs.readFileSync(path.join(process.cwd(), 'examples', 'scan_classic_hmo.pdf'));
    const { error: uploadError } = await supabase
      .storage
      .from('documents')
      .upload(doc.storage_path, testFile);

    if (uploadError) throw uploadError;

    console.log('Test document uploaded, waiting for processing...');

    // 4. Wait for processing (max 2 minutes)
    let processedDoc = null;
    const maxAttempts = 24; // 24 * 5 seconds = 2 minutes
    for (let i = 0; i < maxAttempts; i++) {
      const { data: currentDoc } = await supabase
        .from('documents')
        .select('*')
        .eq('id', doc.id)
        .single();

      if (currentDoc?.status === 'processed' || currentDoc?.status === 'error') {
        processedDoc = currentDoc;
        break;
      }

      await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
      console.log(`Checking status... (Attempt ${i + 1}/${maxAttempts})`);
    }

    if (!processedDoc) {
      throw new Error('Document processing timed out');
    }

    // 5. Display results
    await displayProcessingResults(supabase, doc.id);

    // 6. Cleanup
    console.log('\nCleaning up test data...');
    await supabase.from('documents').delete().eq('id', doc.id);
    await supabase.from('users').delete().eq('id', testUserId);
    await supabase.storage.from('documents').remove([doc.storage_path]);

  } catch (error) {
    console.error('Pipeline verification failed:', error);
    process.exit(1);
  }
}

// Run verification if called directly
if (require.main === module) {
  verifyPipeline().catch(console.error);
}

export { verifyPipeline }; 