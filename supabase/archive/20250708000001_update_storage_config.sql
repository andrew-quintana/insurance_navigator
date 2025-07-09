begin;

-- Update storage bucket configuration to allow PDF files and set size limit
update storage.buckets
set 
  file_size_limit = 52428800, -- 50MB in bytes
  allowed_mime_types = array['application/pdf']
where id = 'files';

commit; 