import 'server-only';
// Storage side of backups (Supabase private bucket).
import {adminClient, workspaceId} from './store';
import {BACKUP_BUCKET, backupPrefix, backupName, parseBackupName, retention, makeSnapshot, checkSnapshot, type BackupKind, type BackupFile} from './backup';
import type {State} from './domain';

const bucket = () => adminClient().storage.from(BACKUP_BUCKET);

export async function listBackups(): Promise<BackupFile[]> {
  const {data, error} = await bucket().list(backupPrefix(workspaceId), {limit: 200, sortBy: {column: 'name', order: 'desc'}});
  if (error) throw new Error('503:Backups are unavailable. Check the private storage bucket.');
  const out: BackupFile[] = [];
  for (const f of data || []) { const p = parseBackupName(f.name); if (p) out.push({...p, size: (f.metadata as {size?: number} | null)?.size}); }
  return out.sort((a, b) => b.at.localeCompare(a.at));
}

export async function writeBackup(kind: BackupKind, state: State, revision: number, by?: string): Promise<BackupFile> {
  const at = new Date().toISOString();
  const name = backupName(kind, at);
  const body = JSON.stringify(makeSnapshot(workspaceId, kind, at, revision, state, by));
  const {error} = await bucket().upload(`${backupPrefix(workspaceId)}/${name}`, new Blob([body], {type: 'application/json'}), {contentType: 'application/json', upsert: true});
  if (error) throw new Error('503:The backup could not be stored. Check the private storage bucket.');
  try {
    const {remove} = retention(await listBackups());
    if (remove.length) await bucket().remove(remove.map(f => `${backupPrefix(workspaceId)}/${f.name}`));
  } catch { /* retention is best effort */ }
  return {name, kind, at, size: body.length};
}

export async function readBackup(name: string) {
  if (!parseBackupName(name)) throw new Error('400:Unknown backup.');
  const {data, error} = await bucket().download(`${backupPrefix(workspaceId)}/${name}`);
  if (error || !data) throw new Error('404:Backup not found.');
  return checkSnapshot(JSON.parse(await data.text()), workspaceId);
}
