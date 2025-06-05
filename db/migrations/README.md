# Database Migrations - Fresh V2 Deployment

## Migration Strategy

This project uses a **consolidated migration approach** for fresh V2 deployments, moving away from incremental migrations to provide a clean, single-source database setup.

## Current Migration Structure

### Active Migration
- **`V1.0.0__fresh_v2_deployment.sql`** - Complete database schema for fresh V2 deployment
  - **Purpose**: Single comprehensive migration for new environments
  - **Contains**: All tables, indexes, RLS policies, functions, views, triggers, and seed data
  - **Features**: Full V2 system including document tracking, feature flags, monitoring views

### Legacy Migrations (Archived)
Located in `legacy_migrations/` directory:
- `000_users_schema.sql` through `010_fix_vector_architecture.sql`
- **Purpose**: Historical development iterations (preserved for reference)
- **Status**: Archived - not used in fresh deployments

## Fresh V2 Deployment Features

The consolidated migration includes:

### Core Infrastructure
- ✅ **User authentication system** (users, roles, user_roles)
- ✅ **Encryption management** (encryption_keys with rotation support)
- ✅ **Vector storage** (user_document_vectors, policy_content_vectors)
- ✅ **Policy management** (policy_records, user_policy_links)
- ✅ **Conversation system** (conversations, messages, agent_states)
- ✅ **Regulatory documents** (regulatory_documents with search enhancements)

### V2 Enhanced Features
- 🚀 **Document tracking table** with processing status pipeline
- 🚀 **Feature flags system** for progressive rollout
- 🚀 **Real-time monitoring views** (failed/stuck documents, processing stats)
- 🚀 **LlamaParse integration** ready (job tracking, webhook support)
- 🚀 **Progress tracking** (chunk processing, percentage completion)

### Security & Performance
- 🔒 **Comprehensive RLS policies** (31+ policies across all tables)
- 🔒 **Secure helper functions** (SECURITY INVOKER, fixed search paths)
- 🔒 **Encryption support** built into vector tables
- ⚡ **Optimized indexes** for all query patterns
- ⚡ **Triggers** for automatic timestamp updates

## Usage

### Fresh Environment Setup
For new deployments, run only:
```bash
psql $DATABASE_URL -f db/migrations/V1.0.0__fresh_v2_deployment.sql
```

### Existing Environment Migration
For environments with legacy migrations already applied, use the migration runner:
```bash
python db/scripts/run_migrations.py
```

## Verification

After deployment, verify with these queries:
```sql
-- Check table count (should be 17+ tables)
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';

-- Verify V2 features
SELECT flag_name, is_enabled FROM feature_flags ORDER BY flag_name;

-- Check RLS policies (should be 30+ policies)  
SELECT COUNT(*) FROM pg_policies WHERE schemaname = 'public';

-- Test feature flag evaluation
SELECT evaluate_feature_flag('enhanced_error_handling', null, 'test@example.com');
```

## V2 System Advantages

### Single Source of Truth
- **Eliminates migration ordering issues**
- **Consistent across all environments**
- **No incremental drift problems**

### V0.### Deployment Optimized
- **No legacy data migration concerns**
- **Optimized for clean installs**
- **Production-ready from day one**

### Maintenance Benefits
- **Easier to understand complete schema**
- **Single file to review for security**
- **Simplified testing and validation**

## Storage Bucket Configuration

The migration documents required Supabase Storage setup:

### Required Bucket: `documents`
- **Visibility**: Private
- **File size limit**: 50MB
- **RLS Policies**: User-scoped access (`{user_id}/*` folder structure)
- **Setup**: Via Supabase Dashboard → Storage → "New Bucket"

### Bucket RLS Policies (apply via Dashboard):
```sql
-- Upload: Users can upload to their folder
CREATE POLICY "Users can upload own files" ON storage.objects
FOR INSERT WITH CHECK (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Read: Users can read their files  
CREATE POLICY "Users can view own files" ON storage.objects
FOR SELECT USING (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Update/Delete: Users can manage their files
CREATE POLICY "Users can update own files" ON storage.objects  
FOR UPDATE USING (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can delete own files" ON storage.objects
FOR DELETE USING (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);
```

## Migration History

This consolidation was performed as part of Phase 1 infrastructure audit, moving from:
- **Before**: 15+ incremental migration files with version conflicts
- **After**: Single comprehensive V1.0.0 migration for fresh deployments

Legacy migrations preserved in `legacy_migrations/` for historical reference. 