-- Supabase Storage bucket. Users must access evidence through the authorized API.
insert into storage.buckets (id,name,public,file_size_limit,allowed_mime_types)
values ('paveledger-evidence','paveledger-evidence',false,3000000,array['image/jpeg','image/png','image/webp'])
on conflict (id) do update set public=false,file_size_limit=3000000,allowed_mime_types=excluded.allowed_mime_types;
-- Deliberately no anon/authenticated object policy for this bucket.
-- Review existing broad storage policies in reused projects; prefer a dedicated project.
