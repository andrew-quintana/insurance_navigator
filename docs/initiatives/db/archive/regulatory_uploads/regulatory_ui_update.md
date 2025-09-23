# Regulatory Document Management UI Enhancements (Deferred)

This file tracks all UI-related tasks for the regulatory document management MVP, originally scoped for Phase 2 but now deferred. Complete backend and API validation must be finished before these UI updates are implemented.

## Deferred UI Tasks (from TODO001 Phase 2)

### Admin Upload UI Enhancements
- [ ] Find current upload interface/component
- [ ] Add admin role detection in frontend
- [ ] Add document type selection for admin users:
  - `user_document` (default)
  - `regulatory_document`
- [ ] Update form submission to include `documentType` in form data sent to upload-handler
- [ ] Test admin upload functionality via UI
- [ ] Verify regular users see no UI changes

### User Access UI Enhancements
- [ ] Find current document search/list interface
- [ ] Include regulatory documents in search queries
- [ ] Add document type indicators in search results:
  - User documents: existing styling
  - Regulatory documents: clear visual indicator (badge, icon, or different styling)
- [ ] Enable viewing regulatory documents (read-only)
- [ ] Test user search and access functionality via UI

### UI Integration Testing
- [ ] Test end-to-end admin workflow: login → upload regulatory doc → verify processing → confirm searchable (UI)
- [ ] Test end-to-end user workflow: login → search documents → find regulatory doc → view content (UI)
- [ ] Verify existing user document upload/search unchanged
- [ ] Test error handling and edge cases in UI

## Constraints
- Minimal changes: Leverage existing components, avoid creating new UI from scratch
- Backward compatibility: Existing user functionality must remain unchanged
- Simple UI: Focus on functionality over polish (MVP)
- No advanced features: No bulk upload, advanced search, metadata editing, etc.

## Next Steps
- UI work will resume after backend/API validation is complete and sign-off is received on core regulatory document functionality.
- Refer to this file for all future UI implementation and tracking for regulatory document management. 