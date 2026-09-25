-- Apply once to a new Supabase project. No destructive reset statements.
begin;
create table if not exists public.workspaces (
 id text primary key,
 owner uuid not null references auth.users(id) on delete restrict,
 revision integer not null default 1 check (revision > 0),
 data jsonb not null check (jsonb_typeof(data) = 'object'),
 updated_at timestamptz not null default now()
);
alter table public.workspaces enable row level security;
revoke all on table public.workspaces from anon, authenticated;
grant select,insert,update on table public.workspaces to service_role;
-- No permissive browser policy. Verified server API enforces membership and scope.
commit;
