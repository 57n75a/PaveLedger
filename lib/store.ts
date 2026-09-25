import 'server-only';
import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import { seed,normalizeState, type State } from './domain';

type WorkspaceRow = { id: string; owner: string; revision: number; data: State };
export const workspaceId = process.env.WORKSPACE_ID?.trim() || 'municipality-pilot';
let client: SupabaseClient | undefined;

export function adminClient() {
  if (client) return client;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SECRET_KEY;
  if (!url || !key) throw new Error('503:Workspace storage is not configured. Follow DEPLOYMENT.md.');
  client = createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false } });
  return client;
}

export async function authenticatedUser(req: Request) {
  const header = req.headers.get('authorization');
  if (!header?.startsWith('Bearer ') || header.length > 8192) throw new Error('401:Sign in to open this workspace.');
  const token = header.slice(7).trim();
  if (!token) throw new Error('401:Sign in to open this workspace.');
  // Validate with the Auth server. Never trust a decoded client JWT or a supplied role.
  const { data, error } = await adminClient().auth.getUser(token);
  if (error || !data.user?.id || !data.user.email || !data.user.email_confirmed_at) {
    throw new Error('401:A verified sign-in is required. Sign in again.');
  }
  return { userId: data.user.id, email: data.user.email.toLowerCase() };
}

export async function readWorkspace(user: { userId: string; email: string }): Promise<WorkspaceRow> {
  const db = adminClient();
  const read = () => db.from('workspaces').select('id,owner,revision,data').eq('id', workspaceId).maybeSingle();
  let result = await read();
  if (result.error) throw new Error('503:Workspace storage is unavailable. Check the database migration and server key.');
  if (!result.data) {
    const owner = process.env.OWNER_EMAIL?.trim().toLowerCase();
    if (!owner) throw new Error('503:Set OWNER_EMAIL before initializing this workspace.');
    if (user.email !== owner) throw new Error('403:The designated owner must initialize this workspace first.');
    const inserted = await db.from('workspaces').upsert({
      id: workspaceId, owner: user.userId, revision: 1, data: initialState(user.userId, user.email),
    }, { onConflict: 'id', ignoreDuplicates: true });
    if (inserted.error) throw new Error('503:Could not initialize the workspace. Check the database migration.');
    result = await read();
  }
  if (result.error || !result.data) throw new Error('503:Workspace could not be loaded.');
  const row=result.data as WorkspaceRow;row.data=normalizeState(row.data);return row;
}

export async function saveWorkspace(state: State, revision: number): Promise<boolean> {
  // Compare-and-swap is one PostgreSQL statement; stale writes cannot overwrite accepted changes.
  const { data, error } = await adminClient().from('workspaces')
    .update({ data: state, revision: revision + 1, updated_at: new Date().toISOString() })
    .eq('id', workspaceId).eq('revision', revision).select('id');
  if (error) throw new Error('503:The workspace could not be saved. Please retry.');
  return !!data?.length;
}

function initialState(id:string,email:string){const s=seed(id,email);if(process.env.SEED_DEMO_DATA!=='true'){s.tickets=[];s.members=s.members.filter(m=>m.id===id);s.contracts=[];}return normalizeState(s);}
