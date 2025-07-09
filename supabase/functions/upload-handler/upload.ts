import { SupabaseClient } from '@supabase/supabase-js';
import { getPipelineFilename } from '../_shared/date_utils.ts';

export async function handleUpload(
  req: Request,
  userId: string,
  supabase: SupabaseClient
) {
  console.log('Starting file upload process...');
  console.log('User ID:', userId);

  let formData;
  try {
    formData = await req.formData();
    console.log('Form data parsed successfully');
  } catch (error) {
    console.error('Failed to parse form data:', error);
    throw new Error('Invalid form data');
  }

  const file = formData.get('file') as File;
  if (!file) {
    console.error('No file found in form data');
    throw new Error('File missing');
  }

  console.log('File details:', {
    name: file.name,
    type: file.type,
    size: file.size
  });

  try {
    // Convert file to buffer for upload
    console.log('Converting file to buffer...');
    const arrayBuffer = await file.arrayBuffer();
    const buffer = new Uint8Array(arrayBuffer);
    console.log('File converted to buffer, size:', buffer.length);

    // Generate file path using verified user ID and timestamp
    const uploadTimestamp = new Date();
    const filePath = `user/${userId}/raw/${getPipelineFilename(uploadTimestamp, file.name)}`;
    console.log('Generated file path:', filePath);

    // Check if file exists and clean it up if needed
    const { data: existingFile } = await supabase.storage
      .from('files')
      .list(`user/${userId}/raw`, {
        search: file.name
      });

    if (existingFile?.length > 0) {
      console.log('Found existing file, removing it first...');
      const { error: removeError } = await supabase.storage
        .from('files')
        .remove([filePath]);
      
      if (removeError) {
        console.error('Failed to remove existing file:', removeError);
        throw new Error('Failed to remove existing file');
      }
    }

    // Upload file to files bucket
    console.log('Starting Supabase storage upload...');
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('files')
      .upload(filePath, buffer, {
        contentType: file.type,
        upsert: false
      });

    if (uploadError) {
      console.error('Upload error:', uploadError);
      throw new Error('Upload to storage failed');
    }

    console.log('Upload successful:', uploadData);

    // Add record to documents table
    console.log('Creating document record...');
    const insertResponse = await supabase
      .schema('documents')  // Explicitly set schema
      .from('documents')
      .insert([
        {
          owner: userId,
          name: file.name,
          source_path: filePath,
          processing_status: 'uploaded',
          uploaded_at: uploadTimestamp.toISOString()
        }
      ])
      .select()
      .single();
    
    console.log('Full insert response:', insertResponse);

    const { data: documentData, error: documentError } = insertResponse;

    if (documentError && Object.keys(documentError).length > 0) {
      console.error('Raw document error:', documentError);
      console.error('Document creation error:', {
        error: documentError,
        code: documentError.code,
        details: documentError.details,
        hint: documentError.hint,
        message: documentError.message
      });
      console.error('Document data attempted:', {
        owner: userId,
        name: file.name,
        source_path: filePath,
        processing_status: 'uploaded'
      });
      
      throw new Error(`Failed to create document record: ${JSON.stringify(documentError)}`);
    }

    console.log('Document record created:', documentData);

    return {
      document: documentData,
      file: {
        filePath,
        fileName: file.name,
        userId,
        contentType: file.type,
        size: buffer.length
      }
    };

  } catch (error) {
    console.error('Storage error:', error instanceof Error ? {
      message: error.message,
      name: error.name,
      stack: error.stack
    } : error);
    throw error;
  }
}