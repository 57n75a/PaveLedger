'use client';
import { createClient, type SupabaseClient } from '@supabase/supabase-js';

let client: SupabaseClient | undefined;
export function browserClient() {
  if (client) return client;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key) throw new Error('Sign-in is not configured. Follow DEPLOYMENT.md and redeploy.');
  client = createClient(url, key);
  return client;
}

export async function authorizedFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  const { data: { session }, error } = await browserClient().auth.getSession();
  if (error || !session) throw new Error('Your session has ended. Sign in again.');
  const headers = new Headers(init.headers);
  headers.set('Authorization', `Bearer ${session.access_token}`);
  return fetch(input, { ...init, headers, cache: 'no-store' });
}
