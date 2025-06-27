-- Check auth.users table
SELECT id, email, role FROM auth.users WHERE id = '11111111-1111-1111-1111-111111111111';
 
-- Check public.users table
SELECT id, email FROM public.users WHERE id = '11111111-1111-1111-1111-111111111111'; 
SELECT id, email, role FROM auth.users WHERE id = '11111111-1111-1111-1111-111111111111';
 
-- Check public.users table
SELECT id, email FROM public.users WHERE id = '11111111-1111-1111-1111-111111111111'; 