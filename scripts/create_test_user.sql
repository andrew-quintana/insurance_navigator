-- Create test user in users table
INSERT INTO public.users (
  id,
  email,
  hashed_password,
  is_active,
  created_at,
  updated_at,
  user_role,
  access_level
)
VALUES (
  '11111111-1111-1111-1111-111111111111',
  'test@example.com',
  crypt('test-password', gen_salt('bf')),
  true,
  now(),
  now(),
  'user',
  1
)
ON CONFLICT (id) DO NOTHING;
INSERT INTO public.users (
  id,
  email,
  hashed_password,
  is_active,
  created_at,
  updated_at,
  user_role,
  access_level
)
VALUES (
  '11111111-1111-1111-1111-111111111111',
  'test@example.com',
  crypt('test-password', gen_salt('bf')),
  true,
  now(),
  now(),
  'user',
  1
)
ON CONFLICT (id) DO NOTHING;