'use client';
import { useEffect, useState, type FormEvent, type ReactNode } from 'react';
import type { Session } from '@supabase/supabase-js';
import { browserClient } from '@/lib/supabase-browser';

export default function AccessGate({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    try {
      const auth = browserClient().auth;
      const { data: { subscription } } = auth.onAuthStateChange((_event, next) => {
        if (active) { setSession(next); setLoading(false); }
      });
      auth.getSession().then(({ data, error }) => {
        if (!active) return;
        if (error) setError('Could not restore your session. Sign in again.');
        setSession(data.session); setLoading(false);
      }).catch(() => { if (active) { setError('Sign-in is unavailable. Please retry.'); setLoading(false); } });
      return () => { active = false; subscription.unsubscribe(); };
    } catch (e) { setError((e as Error).message); setLoading(false); }
    return () => { active = false; };
  }, []);

  async function signIn(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setError(''); setBusy(true);
    const form = new FormData(e.currentTarget);
    try {
      const { error } = await browserClient().auth.signInWithPassword({ email: String(form.get('email')).trim(), password: String(form.get('password')) });
      if (error) setError('Sign-in failed. Check your email, password, and account confirmation.');
    } catch { setError('Sign-in is unavailable. Check your connection and try again.'); }
    finally { setBusy(false); }
  }

  if (session) return <div key={session.user.id}>{children}</div>;
  return <main className="access-page"><section className="access-card">
    <img src="/logo.png" width="270" height="91" alt="PaveLedger" />
    <p className="eyebrow">ROAD OPERATIONS</p><h1>Sign in to your workspace</h1>
    <p className="muted">Investigations, repair responsibility, and the next action in one place.</p>
    {loading ? <p role="status">Checking your session…</p> : <form className="form" onSubmit={signIn}>
      <label>Email<input name="email" type="email" autoComplete="username" required /></label>
      <label>Password<input name="password" type="password" autoComplete="current-password" required /></label>
      <button className="primary" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
    </form>}
    {error && <p role="alert" className="access-error">{error}</p>}
    <p className="footnote">Access is provisioned by your workspace administrator. Contact them for a new account or password reset.</p>
    <a className="text-button" href="/concept">Explore the platform</a>
  </section></main>;
}
