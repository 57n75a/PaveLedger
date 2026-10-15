'use client';
// Platform settings: list workspace backups, back up now, restore a chosen backup.
import {useEffect, useState} from 'react';
import {DatabaseBackup, RotateCcw} from 'lucide-react';
import {toast} from 'sonner';
import {tx, useLang, locale} from '@/lib/i18n';
import {authorizedFetch} from '@/lib/supabase-browser';
import type {BackupFile} from '@/lib/backup';

const KIND: Record<BackupFile['kind'], string> = {daily: 'Daily', manual: 'Manual', 'before-restore': 'Before a restore'};

export default function BackupCard({revision, onChanged}: {revision: number; onChanged: () => Promise<void> | void}) {
  useLang();
  const [list, setList] = useState<BackupFile[] | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState<BackupFile | null>(null);

  async function load() {
    try { const r = await authorizedFetch('/api/backups'); const d = await r.json(); if (!r.ok) throw new Error(d.error); setList(d.backups); setError(''); }
    catch (e) { setError((e as Error).message); setList([]); }
  }
  useEffect(() => { void load(); }, []);

  async function post(body: Record<string, unknown>, ok: string) {
    setBusy(true);
    try {
      const r = await authorizedFetch('/api/backups', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({...body, revision})});
      const d = await r.json(); if (!r.ok) throw new Error(d.error);
      setList(d.backups); toast.success(tx(ok)); await onChanged();
    } catch (e) { toast.error(tx((e as Error).message)); }
    finally { setBusy(false); setConfirm(null); }
  }
  const when = (iso: string, kind: BackupFile['kind']) => kind === 'daily'
    ? new Date(iso).toLocaleDateString(locale(), {dateStyle: 'full', timeZone: 'UTC'})
    : new Date(iso).toLocaleString(locale(), {dateStyle: 'medium', timeStyle: 'short'});
  const size = (n?: number) => n ? (n > 1_000_000 ? (n / 1_000_000).toLocaleString(locale(), {maximumFractionDigits: 1}) + ' MB' : Math.round(n / 1000) + ' KB') : '';

  return <section className="backup-card">
    <div className="section-head"><div>
      <h2><DatabaseBackup size={18}/> {tx('Backups')}</h2>
      <p>{tx('A copy of the whole workspace is saved every day and kept for 30 days. Restoring replaces the current workspace; the current state is backed up first, so a restore can be undone.')}</p>
    </div><button className="secondary" disabled={busy} onClick={() => post({action: 'create'}, 'Backup saved')}>{tx(busy ? 'Working…' : 'Back up now')}</button></div>
    {error && <p className="access-error">{tx(error)}</p>}
    {list === null ? <p className="muted">{tx('Loading backups…')}</p> : !list.length ? <p className="muted">{tx('No backups yet. The first daily backup is made tomorrow morning, or back up now.')}</p> :
      <ul className="backup-list">{list.slice(0, 12).map(b => <li key={b.name}>
        <div><strong>{when(b.at, b.kind)}</strong><small>{tx(KIND[b.kind])}{b.size ? ' · ' + size(b.size) : ''}</small></div>
        <button className="text-button" disabled={busy} onClick={() => setConfirm(b)}><RotateCcw size={14}/> {tx('Restore')}</button>
      </li>)}</ul>}
    {confirm && <div className="backup-confirm" role="alertdialog" aria-label={tx('Restore this backup?')}>
      <strong>{tx('Restore this backup?')}</strong>
      <p>{tx('The workspace will go back to {0}. Changes made after that are replaced, but a backup of the current state is saved first.', [when(confirm.at, confirm.kind)])}</p>
      <div className="button-row"><button className="primary" disabled={busy} onClick={() => post({action: 'restore', name: confirm.name}, 'Workspace restored')}>{tx(busy ? 'Restoring…' : 'Restore')}</button><button className="secondary" disabled={busy} onClick={() => setConfirm(null)}>{tx('Cancel')}</button></div>
    </div>}
  </section>;
}
