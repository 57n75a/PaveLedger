'use client';
import { useEffect, useState, type FormEvent, type ReactNode } from 'react';
import type { Session } from '@supabase/supabase-js';
import { browserClient } from '@/lib/supabase-browser';

const MIN_PASSWORD = 8;

export default function AccessGate({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [recovery, setRecovery] = useState(false);
  const [forgot, setForgot] = useState(false);

  useEffect(() => {
    let active = true;
    try {
      const auth = browserClient().auth;
      const { data: { subscription } } = auth.onAuthStateChange((event, next) => {
        if (!active) return;
        if (event === 'PASSWORD_RECOVERY') setRecovery(true);
        setSession(next); setLoading(false);
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

  // Invited people, people given a temporary password, and people who followed a reset link must choose their own password.
  const mustChange = !!session && (recovery || session.user.user_metadata?.must_change_password === true);

  async function signIn(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setError(''); setNotice(''); setBusy(true);
    const form = new FormData(e.currentTarget);
    try {
      const { error } = await browserClient().auth.signInWithPassword({ email: String(form.get('email')).trim(), password: String(form.get('password')) });
      if (error) setError('Sign-in failed. Check your email, password, and account confirmation.');
    } catch { setError('Sign-in is unavailable. Check your connection and try again.'); }
    finally { setBusy(false); }
  }

  async function requestReset(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setError(''); setNotice(''); setBusy(true);
    const email = String(new FormData(e.currentTarget).get('email')).trim();
    try { await browserClient().auth.resetPasswordForEmail(email, { redirectTo: window.location.origin }); } catch { /* the neutral message below is shown either way */ }
    setBusy(false);
    setNotice('If an account exists for that email, a password reset link is on its way. If nothing arrives, ask your administrator to reset your password.');
  }

  async function setNewPassword(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setError(''); setNotice('');
    const form = new FormData(e.currentTarget);
    const password = String(form.get('password')), confirm = String(form.get('confirm'));
    if (password.length < MIN_PASSWORD) { setError(`Use at least ${MIN_PASSWORD} characters.`); return; }
    if (password !== confirm) { setError('The two passwords do not match.'); return; }
    setBusy(true);
    try {
      const auth = browserClient().auth;
      const { error } = await auth.updateUser({ password, data: { must_change_password: false } });
      if (error) { setError('Could not set the password. Choose a different one and try again.'); return; }
      setRecovery(false);
      const { data } = await auth.getSession(); setSession(data.session);
    } catch { setError('Could not set the password. Check your connection and try again.'); }
    finally { setBusy(false); }
  }

  if (session && !mustChange) return <div key={session.user.id}>{children}</div>;
  return <main className="access-page"><section className="access-card">
    <img src="/logo.png" width="270" height="91" alt="PaveLedger" />
    <p className="eyebrow">ROAD OPERATIONS</p>
    {session && mustChange ? <>
      <h1>Choose a new password</h1>
      <p className="muted">{recovery ? 'Enter a new password for your account.' : 'Welcome. Choose your own password to continue.'}</p>
      <form className="form" onSubmit={setNewPassword}>
        <label>New password<input name="password" type="password" autoComplete="new-password" minLength={MIN_PASSWORD} required /></label>
        <label>Confirm new password<input name="confirm" type="password" autoComplete="new-password" minLength={MIN_PASSWORD} required /></label>
        <button className="primary" disabled={busy}>{busy ? 'Saving…' : 'Save password and continue'}</button>
      </form>
      <button className="text-button" type="button" onClick={() => { setRecovery(false); void browserClient().auth.signOut(); }}>Sign out</button>
    </> : <>
      <h1>{forgot ? 'Reset your password' : 'Sign in to your workspace'}</h1>
      <p className="muted">{forgot ? 'Enter your email and we will send a reset link.' : 'Tickets, repair responsibility, and the next action in one place.'}</p>
      {loading ? <p role="status">Checking your session…</p> : forgot ? <form className="form" onSubmit={requestReset}>
        <label>Email<input name="email" type="email" autoComplete="username" required /></label>
        <button className="primary" disabled={busy}>{busy ? 'Sending…' : 'Send reset link'}</button>
      </form> : <form className="form" onSubmit={signIn}>
        <label>Email<input name="email" type="email" autoComplete="username" required /></label>
        <label>Password<input name="password" type="password" autoComplete="current-password" required /></label>
        <button className="primary" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
      </form>}
      {!loading && <button className="text-button" type="button" onClick={() => { setForgot(!forgot); setError(''); setNotice(''); }}>{forgot ? 'Back to sign in' : 'Forgot your password?'}</button>}
    </>}
    {notice && <p role="status" className="muted">{notice}</p>}
    {error && <p role="alert" className="access-error">{error}</p>}
    <p className="footnote">Access is provisioned by your workspace administrator. Contact them for a new account or password reset.</p>
    <a className="text-button" href="/concept">Explore the platform</a>
  </section></main>;
}
