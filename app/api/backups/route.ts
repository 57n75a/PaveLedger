// Workspace backups for administrators: list, back up now, restore a chosen day.
import {z} from 'zod';
import {context, project, failure} from '@/lib/context';
import {saveWorkspace} from '@/lib/store';
import {AppError} from '@/lib/actions';
import {normalizeState} from '@/lib/domain';
import {listBackups, writeBackup, readBackup} from '@/lib/backup-store';
export const runtime = 'nodejs'; export const dynamic = 'force-dynamic';
const headers = {'Cache-Control': 'private, no-store'};

async function admin(req: Request) {
  const c = await context(req);
  if (c.actual.role !== 'Admin' || c.member.id !== c.actual.id) throw new AppError('Only an administrator, using their own identity, can manage backups.', 403);
  return c;
}

export async function GET(req: Request) {
  try { await admin(req); return Response.json({backups: await listBackups()}, {headers}); } catch (e) { return failure(e); }
}

export async function POST(req: Request) {
  try {
    const origin = req.headers.get('origin'); if (origin && origin !== new URL(req.url).origin) throw new AppError('Origin mismatch', 403);
    const c = await admin(req);
    const body = z.object({action: z.enum(['create', 'restore']), name: z.string().max(80).optional(), revision: z.number().int()}).parse(await req.json().catch(() => ({})));
    if (body.revision !== c.row.revision) throw new AppError('Workspace changed. Refresh and review before saving.', 409);
    const now = new Date().toISOString();
    if (body.action === 'create') {
      const file = await writeBackup('manual', c.state, c.row.revision, c.actual.id);
      c.state.events.unshift({at: now, actor: c.actual.name, action: 'Backup created: ' + file.name});
      if (!await saveWorkspace(c.state, c.row.revision)) throw new AppError('Workspace changed. Refresh and try again.', 409);
      return Response.json({...project(c.state, c.member, true), revision: c.row.revision + 1, backups: await listBackups()}, {headers});
    }
    if (!body.name) throw new AppError('Choose a backup to restore.');
    const snap = await readBackup(body.name);
    // Keep the current state first, so the restore itself can be undone.
    await writeBackup('before-restore', c.state, c.row.revision, c.actual.id);
    const restored = normalizeState(snap.data);
    // The administrator doing the restore keeps access even if the backup predates their account.
    if (!restored.members.some(m => m.id === c.actual.id)) restored.members.push({...c.actual});
    restored.events.unshift({at: now, actor: c.actual.name, action: `Workspace restored from backup ${body.name} (saved ${snap.at.slice(0, 16).replace('T', ' ')} UTC)`});
    if (!await saveWorkspace(restored, c.row.revision)) throw new AppError('Workspace changed. Refresh and try again.', 409);
    return Response.json({...project(restored, c.member, true), revision: c.row.revision + 1, backups: await listBackups()}, {headers});
  } catch (e) { return failure(e instanceof z.ZodError ? new AppError('Invalid backup request.') : e instanceof Error && /^(This file|This backup|The backup)/.test(e.message) ? new AppError(e.message) : e); }
}
