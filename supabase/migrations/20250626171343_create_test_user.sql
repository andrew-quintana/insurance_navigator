-- Create test user in auth.users
INSERT INTO auth.users (id, email, role)
VALUES (
  '3e2d9e16-b722-4a05-9fc2-f8e4eb5e4cbe',
  'test@example.com',
  'authenticated'
) ON CONFLICT (id) DO NOTHING; 
INSERT INTO auth.users (id, email, role)
VALUES (
  '3e2d9e16-b722-4a05-9fc2-f8e4eb5e4cbe',
  'test@example.com',
  'authenticated'
) ON CONFLICT (id) DO NOTHING; 