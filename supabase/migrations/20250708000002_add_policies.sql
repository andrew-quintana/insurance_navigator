begin;

-- -------------------------------
-- RLS POLICIES
-- -------------------------------

-- Documents table policies
create policy "Service role can insert documents"
  on documents.documents
  for insert
  to service_role
  with check (true);

create policy "Service role can update documents"
  on documents.documents
  for update
  to service_role
  using (true)
  with check (true);

-- Document chunks table policies
create policy "Service role can insert documents"
  on documents.document_chunks
  for insert
  to service_role
  with check (true);

create policy "Service role can update documents"
  on documents.document_chunks
  for update
  to service_role
  using (true)
  with check (true);

commit;