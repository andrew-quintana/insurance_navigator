\d public.documents;
\d public.processing_jobs;
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name IN ('documents', 'processing_jobs')
ORDER BY table_name, ordinal_position; 
\d public.processing_jobs;
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name IN ('documents', 'processing_jobs')
ORDER BY table_name, ordinal_position; 