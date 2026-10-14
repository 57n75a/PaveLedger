'use client';
// Changes made without a connection wait here (IndexedDB, on this device) and are sent in order when it returns.
// Each item is replayed against the latest workspace revision, so other people's changes made meanwhile are kept.

export type QueuedAction = {kind: 'action'; body: Record<string, unknown>; label: string};
export type QueuedEvidence = {kind: 'evidence'; ticket: string; fields: Record<string, string>; file: Blob; fileName: string; label: string};
export type QueuedCreate = {kind: 'create'; fields: Record<string, unknown>; files: {blob: Blob; name: string}[]; quality: string; label: string};
export type QueueItem = (QueuedAction | QueuedEvidence | QueuedCreate) & {id?: number; at: string; persona?: string; error?: string};

const DB = 'paveledger-offline', STORE = 'queue';
let dbp: Promise<IDBDatabase> | null = null;
function db(): Promise<IDBDatabase> {
  dbp ??= new Promise((ok, bad) => {
    const r = indexedDB.open(DB, 1);
    r.onupgradeneeded = () => r.result.createObjectStore(STORE, {keyPath: 'id', autoIncrement: true});
    r.onsuccess = () => ok(r.result);
    r.onerror = () => { dbp = null; bad(r.error); };
  });
  return dbp;
}
async function run<T>(mode: IDBTransactionMode, fn: (s: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const d = await db();
  return new Promise((ok, bad) => { const t = d.transaction(STORE, mode); const r = fn(t.objectStore(STORE)); r.onsuccess = () => ok(r.result); r.onerror = () => bad(r.error); });
}

const listeners = new Set<() => void>();
export const onQueueChange = (fn: () => void) => { listeners.add(fn); return () => { listeners.delete(fn); }; };
const changed = () => listeners.forEach(fn => fn());

export async function enqueue(item: QueueItem) { await run('readwrite', s => s.add(item)); changed(); }
export async function queued(): Promise<QueueItem[]> { try { return await run('readonly', s => s.getAll()) as QueueItem[]; } catch { return []; } }
export async function remove(id: number) { await run('readwrite', s => s.delete(id)); changed(); }
async function update(item: QueueItem) { await run('readwrite', s => s.put(item)); changed(); }
export async function clearQueue() { try { await run('readwrite', s => s.clear()); } catch {} changed(); }

/** True when a request failed because there is no connection, as opposed to the server refusing it. */
export const isOffline = (e: unknown) => (typeof navigator !== 'undefined' && navigator.onLine === false) || e instanceof TypeError;

type Fetcher = (input: string, init?: RequestInit) => Promise<Response>;
type Result = {sent: number; failed: QueueItem[]};
let flushing: Promise<Result> | null = null;

/** Send everything waiting, oldest first. Items the server refuses are kept with the reason, so nothing is lost silently. */
export function flushQueue(fetcher: Fetcher, endpointFor: (persona?: string) => string): Promise<Result> {
  flushing ??= (async () => {
    const items = (await queued()).filter(i => !i.error);
    let sent = 0; const failed: QueueItem[] = [];
    for (const item of items) {
      try {
        const endpoint = endpointFor(item.persona);
        const ws = await fetcher(endpoint); const cur = await ws.json(); if (!ws.ok) throw new Error(cur.error || 'Workspace unavailable');
        let revision: number = cur.revision;
        const suffix = endpoint.includes('?') ? endpoint.slice(endpoint.indexOf('?')) : '';
        const send = async (form: FormData) => { const r = await fetcher('/api/evidence' + suffix, {method: 'POST', body: form}); const d = await r.json(); if (!r.ok) throw new Error(d.error); revision += 1; };
        if (item.kind === 'action') {
          const r = await fetcher(endpoint, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({...item.body, revision})});
          const d = await r.json(); if (!r.ok) throw new Error(d.error);
        } else if (item.kind === 'evidence') {
          const f = new FormData(); Object.entries(item.fields).forEach(([k, v]) => f.set(k, v)); f.set('ticket', item.ticket); f.set('revision', String(revision)); f.set('file', new File([item.file], item.fileName, {type: item.file.type}));
          await send(f);
        } else {
          const before = new Set((cur.tickets || []).map((t: {id: string}) => t.id));
          const r = await fetcher(endpoint, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'create', ...item.fields, revision})});
          const d = await r.json(); if (!r.ok) throw new Error(d.error);
          revision = d.revision;
          const created = (d.tickets || []).find((t: {id: string}) => !before.has(t.id));
          if (created) for (const file of item.files) {
            const f = new FormData(); f.set('ticket', created.id); f.set('revision', String(revision)); f.set('authorized', 'true'); f.set('purpose', 'detection');
            f.set('capturedAt', String(item.fields.observedAt || item.at)); f.set('lat', String(item.fields.lat)); f.set('lng', String(item.fields.lng)); f.set('accuracy', String(item.fields.accuracy)); f.set('lane', String(item.fields.lane || 'Lane 1')); f.set('quality', item.quality);
            f.set('file', new File([file.blob], file.name, {type: file.blob.type}));
            await send(f);
          }
        }
        await remove(item.id!); sent++;
      } catch (e) {
        if (isOffline(e)) break; // still no connection: try again later, keep the order
        const failedItem = {...item, error: (e as Error).message || 'Refused by the server'};
        await update(failedItem); failed.push(failedItem);
      }
    }
    return {sent, failed};
  })().finally(() => { flushing = null; });
  return flushing;
}
