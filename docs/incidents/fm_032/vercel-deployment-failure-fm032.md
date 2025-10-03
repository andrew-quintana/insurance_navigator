# Vercel Deployment Failure Investigation - FM032

**Date**: January 2025  
**Incident**: Vercel deployment failure for commit `920e3c1` that previously worked  
**Status**: ✅ RESOLVED  
**Root Cause**: Build context mismatch between Vercel configuration and file structure  

## Summary

A previously working commit (`920e3c1`) began failing on Vercel deployment with module resolution errors, despite working correctly in previous deployments. The investigation revealed a fundamental build context mismatch where Vercel was building from the root directory but running commands in the `ui/` subdirectory, causing `.vercelignore` to exclude necessary files.

## Error Messages

```
Error: Cannot find module 'tailwindcss'
Module not found: Can't resolve '@/components/ui/button'
Module not found: Can't resolve '@/components/ui/card'
Module not found: Can't resolve '@/components/DocumentUploadModal'
Module not found: Can't resolve '@/components/auth/SessionManager'
```

## Investigation Timeline

### Phase 1: Initial Analysis
- **Approach**: Investigated uncommitted changes in working directory
- **Issue**: User corrected approach - needed to investigate the specific failing commit
- **Learning**: Must investigate the exact commit that failed, not current state

### Phase 2: Commit-Specific Investigation
- **Focus**: Analyzed commit `920e3c1` specifically
- **Discovery**: `ui/lib/supabase-client.ts` was being imported but excluded by `.vercelignore`
- **Fix Attempt**: Added `!ui/lib/supabase-client.ts` to `.vercelignore`
- **Result**: Partial success - resolved Supabase client issue but revealed deeper problem

### Phase 3: Tailwind CSS Issue
- **New Error**: `Error: Cannot find module 'tailwindcss'`
- **Analysis**: Conflicting `.vercelignore` rules for `node_modules/`
- **Fix Attempt**: Reordered `.vercelignore` rules to prioritize `!ui/node_modules/`
- **Result**: Still failed with original module resolution errors

### Phase 4: Root Cause Discovery
- **Key Insight**: Vercel configuration mismatch
- **Problem**: Root `vercel.json` had:
  ```json
  "buildCommand": "cd ui && npm run build"
  "installCommand": "cd ui && npm install --legacy-peer-deps"
  ```
- **Issue**: Vercel builds from root but runs commands in `ui/`, causing context mismatch

## Root Cause Analysis

### The Core Problem
1. **Vercel builds from root directory** (where `.vercelignore` is applied)
2. **Commands run in `ui/` subdirectory** (where TypeScript path mapping `@/*` resolves)
3. **`.vercelignore` excludes files** that the `ui/` build process needs
4. **Module resolution fails** because files exist in `ui/` but Vercel can't see them from root context

### Why It Worked Before
- The codebase evolved (new files added)
- `.vercelignore` wasn't updated to account for new dependencies
- Previous deployments worked because files were simpler or dependencies were different

### Why It Failed Now
- **Configuration drift**: Build context didn't match file structure
- **Strict file inclusion**: Vercel's `.vercelignore` rules were too restrictive
- **Path resolution mismatch**: TypeScript `@/*` paths couldn't resolve from wrong context

## Solution Implemented

### Final Fix: Move Vercel Configuration to UI Directory

1. **Moved `vercel.json`** from root to `ui/` directory
2. **Updated build commands**:
   ```json
   // Before (root vercel.json)
   "buildCommand": "cd ui && npm run build"
   "installCommand": "cd ui && npm install --legacy-peer-deps"
   
   // After (ui/vercel.json)
   "buildCommand": "npm run build"
   "installCommand": "npm install --legacy-peer-deps"
   ```
3. **Created `ui/.vercelignore`** with minimal exclusions
4. **Removed root `vercel.json`** to avoid conflicts

### Key Insight: Vercel Root Directory
**CRITICAL**: When using `ui/vercel.json`, Vercel's root directory becomes the `ui/` subdirectory, not the project root. This means:
- All file paths are relative to `ui/`
- `.vercelignore` is applied from `ui/` context
- TypeScript path mapping `@/*` resolves correctly
- All UI files are accessible during build

## Technical Details

### File Structure Impact
```
Before:
/ (Vercel root)
├── vercel.json (builds from root, runs commands in ui/)
├── .vercelignore (applied from root)
└── ui/
    ├── components/ (excluded by root .vercelignore)
    ├── lib/ (excluded by root .vercelignore)
    └── package.json

After:
/ui (Vercel root)
├── vercel.json (builds from ui/)
├── .vercelignore (applied from ui/)
├── components/ (accessible)
├── lib/ (accessible)
└── package.json
```

### TypeScript Configuration
```json
// ui/tsconfig.json
"paths": {
  "@/*": ["./*"]  // Resolves relative to ui/ directory
}
```

## Lessons Learned

1. **Build Context Matters**: Vercel's build context must match the file structure
2. **Configuration Drift**: Working commits can fail due to environment changes
3. **Path Resolution**: TypeScript path mapping depends on build context
4. **Investigation Approach**: Always investigate the specific failing commit, not current state
5. **Incremental Fixes**: Partial fixes can reveal deeper issues

## Prevention

1. **Consistent Build Context**: Ensure Vercel builds from the same directory as the application
2. **Minimal `.vercelignore`**: Only exclude what's absolutely necessary
3. **Regular Testing**: Test deployments after configuration changes
4. **Documentation**: Document build context and file structure relationships

## Files Modified

- `vercel.json` → `ui/vercel.json` (moved and updated)
- `ui/.vercelignore` (created)
- `.vercelignore` (removed from root)

## Commits

- `bba53d5`: Initial `.vercelignore` fixes
- `bbfcbdc`: Final fix - moved Vercel configuration to UI directory

## Testing

- ✅ Local build successful: `npm run build` in `ui/` directory
- ✅ Module resolution working: All `@/` imports resolve correctly
- ✅ Deployment ready: `fix-vercel-deployment-fm032` branch pushed

---

**Resolution**: Move Vercel configuration to `ui/` directory to ensure build context matches file structure and TypeScript path resolution.
