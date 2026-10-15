// Workspace backups: a JSON copy of the whole workspace in private storage, one per day plus manual ones.
// Pure helpers here; storage calls live in the API route and the daily job.
import type {State} from './domain.ts';

export const BACKUP_BUCKET = 'paveledger-evidence';
export const KEEP_DAILY = 30;
export const KEEP_MANUAL = 20;

export type BackupKind = 'daily' | 'manual' | 'before-restore';
export type BackupFile = {name: string; kind: BackupKind; at: string; size?: number};
export type Snapshot = {format: 'paveledger-backup'; version: 1; workspace: string; kind: BackupKind; at: string; revision: number; by?: string; data: State};

export const backupPrefix = (workspace: string) => `${workspace}/_backups`;
/** daily-2026-10-14.json, manual-2026-10-14T09-30-00Z.json, before-restore-… */
export function backupName(kind: BackupKind, at: string): string {
  return kind === 'daily' ? `daily-${at.slice(0, 10)}.json` : `${kind}-${at.slice(0, 19).replace(/:/g, '-')}Z.json`;
}
export function parseBackupName(name: string): BackupFile | null {
  let m = name.match(/^daily-(\d{4}-\d{2}-\d{2})\.json$/);
  if (m) return {name, kind: 'daily', at: m[1] + 'T00:00:00.000Z'};
  m = name.match(/^(manual|before-restore)-(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2})Z\.json$/);
  if (m) return {name, kind: m[1] as BackupKind, at: `${m[2]}T${m[3]}:${m[4]}:${m[5]}.000Z`};
  return null;
}
/** Newest first; files beyond the retention limits are returned for deletion. */
export function retention(files: BackupFile[]): {keep: BackupFile[]; remove: BackupFile[]} {
  const sorted = [...files].sort((a, b) => b.at.localeCompare(a.at));
  const daily = sorted.filter(f => f.kind === 'daily'), other = sorted.filter(f => f.kind !== 'daily');
  const remove = [...daily.slice(KEEP_DAILY), ...other.slice(KEEP_MANUAL)];
  return {keep: sorted.filter(f => !remove.includes(f)), remove};
}
export function makeSnapshot(workspace: string, kind: BackupKind, at: string, revision: number, data: State, by?: string): Snapshot {
  return {format: 'paveledger-backup', version: 1, workspace, kind, at, revision, by, data};
}
/** Check a downloaded file before it may replace the live workspace. */
export function checkSnapshot(x: unknown, workspace: string): Snapshot {
  const s = x as Snapshot;
  if (!s || s.format !== 'paveledger-backup' || s.version !== 1) throw new Error('This file is not a PaveLedger backup.');
  if (s.workspace !== workspace) throw new Error('This backup belongs to another workspace.');
  const d = s.data as State;
  if (!d || !Array.isArray(d.tickets) || !Array.isArray(d.members) || !Array.isArray(d.teams) || !Array.isArray(d.contracts)) throw new Error('The backup is incomplete.');
  return s;
}
