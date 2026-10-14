'use client';
// Top-bar chip: shows when the device is offline and how many changes are waiting, and sends them when back online.
import {useCallback, useEffect, useState} from 'react';
import {CloudOff, RefreshCw, AlertTriangle} from 'lucide-react';
import {toast} from 'sonner';
import {tx, useLang} from '@/lib/i18n';
import {authorizedFetch} from '@/lib/supabase-browser';
import {queued, flushQueue, onQueueChange, remove, type QueueItem} from '@/lib/offline-queue';

export default function SyncStatus({onSynced}: {onSynced: () => void | Promise<void>}) {
  useLang();
  const [online, setOnline] = useState(true);
  const [items, setItems] = useState<QueueItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false);
  const refresh = useCallback(async () => setItems(await queued()), []);

  const send = useCallback(async () => {
    if (busy || !navigator.onLine) return;
    const waiting = (await queued()).filter(i => !i.error);
    if (!waiting.length) return;
    setBusy(true);
    try {
      const r = await flushQueue((u, init) => authorizedFetch(u, init), p => '/api/workspace' + (!p || p === 'owner' ? '' : '?persona=' + encodeURIComponent(p)));
      if (r.sent) { toast.success(tx('{0} change(s) made offline were sent.', [String(r.sent)])); await onSynced(); }
      if (r.failed.length) toast.error(tx('{0} change(s) could not be sent. Open the list to see why.', [String(r.failed.length)]));
    } finally { setBusy(false); void refresh(); }
  }, [busy, onSynced, refresh]);

  useEffect(() => {
    setOnline(navigator.onLine); void refresh();
    const up = () => { setOnline(true); void send(); }, down = () => setOnline(false);
    window.addEventListener('online', up); window.addEventListener('offline', down);
    const off = onQueueChange(() => void refresh());
    const timer = setInterval(() => { if (navigator.onLine) void send(); }, 30_000);
    return () => { window.removeEventListener('online', up); window.removeEventListener('offline', down); off(); clearInterval(timer); };
  }, [refresh, send]);
  useEffect(() => { if (online && items.some(i => !i.error)) void send(); }, [online]); // eslint-disable-line react-hooks/exhaustive-deps

  const failed = items.filter(i => i.error);
  if (online && !items.length) return null;
  return <div className="sync">
    <button type="button" className={'sync-chip ' + (!online ? 'offline' : failed.length ? 'failed' : 'pending')} onClick={() => setOpen(!open)} aria-expanded={open}>
      {!online ? <CloudOff size={15}/> : failed.length ? <AlertTriangle size={15}/> : <RefreshCw size={15} className={busy ? 'spin' : ''}/>}
      <span>{!online ? tx('Offline') : busy ? tx('Sending…') : failed.length ? tx('{0} not sent', [String(failed.length)]) : tx('{0} waiting', [String(items.length)])}</span>
      {!online && items.length > 0 && <b>{items.length}</b>}
    </button>
    {open && <div className="sync-pop" role="dialog" aria-label={tx('Changes on this device')}>
      <strong>{!online ? tx('You are offline') : tx('Changes on this device')}</strong>
      <p className="muted">{!online ? tx('You can keep working. Notes, stage changes, new tickets and photos are saved here and sent automatically when the connection returns.') : tx('These changes were made without a connection.')}</p>
      {items.length ? <ul>{items.map(i => <li key={i.id}>
        <span>{i.label}</span>
        {i.error && <small className="access-error">{tx(i.error)}</small>}
        {i.error && <button type="button" className="text-button" onClick={() => { if (confirm(tx('Discard this change? It will not be sent.'))) void remove(i.id!); }}>{tx('Discard')}</button>}
      </li>)}</ul> : <p className="muted">{tx('Nothing is waiting.')}</p>}
      {online && items.some(i => !i.error) && <button type="button" className="secondary" disabled={busy} onClick={() => void send()}>{tx('Send now')}</button>}
    </div>}
  </div>;
}
