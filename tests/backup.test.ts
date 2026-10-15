import {test} from 'node:test';
import assert from 'node:assert/strict';
import {backupName, parseBackupName, retention, makeSnapshot, checkSnapshot, KEEP_DAILY} from '../lib/backup.ts';
import {seed} from '../lib/domain.ts';

test('names round-trip', () => {
  const at = '2026-10-14T09:30:05.123Z';
  for (const kind of ['daily', 'manual', 'before-restore'] as const) {
    const p = parseBackupName(backupName(kind, at))!;
    assert.equal(p.kind, kind);
    assert.equal(p.at.slice(0, 10), '2026-10-14');
  }
  assert.equal(parseBackupName('../../etc/passwd'), null);
  assert.equal(parseBackupName('daily-2026-10-14.json.exe'), null);
});

test('keeps the last 30 daily backups', () => {
  const files = Array.from({length: 35}, (_, i) => parseBackupName(backupName('daily', new Date(Date.UTC(2026, 8, 1 + i)).toISOString()))!);
  const r = retention(files);
  assert.equal(r.keep.length, KEEP_DAILY);
  assert.equal(r.remove.length, 5);
  assert.ok(r.remove.every(f => f.at < r.keep[r.keep.length - 1].at));
});

test('snapshots are checked before restore', () => {
  const snap = makeSnapshot('ws', 'manual', '2026-10-14T00:00:00.000Z', 3, seed('o', 'o@x'));
  assert.equal(checkSnapshot(JSON.parse(JSON.stringify(snap)), 'ws').revision, 3);
  assert.throws(() => checkSnapshot(snap, 'other'), /another workspace/);
  assert.throws(() => checkSnapshot({format: 'x'}, 'ws'), /not a PaveLedger backup/);
  assert.throws(() => checkSnapshot({...snap, data: {tickets: []}}, 'ws'), /incomplete/);
});
