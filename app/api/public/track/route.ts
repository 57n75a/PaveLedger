// Public endpoint: progress of a resident report by its tracking code. Shows steps and dates only.
import {readWorkspaceRow} from '@/lib/store';
import {failure} from '@/lib/context';
import {AppError} from '@/lib/actions';
import {makeLimiter} from '@/lib/mail';
import {publicStatus} from '@/lib/public-report';
export const runtime = 'nodejs'; export const dynamic = 'force-dynamic';

const lookups = makeLimiter(60, 10 * 60_000);

export async function GET(req: Request) {
  try {
    const ip = (req.headers.get('x-forwarded-for') || '').split(',')[0].trim() || 'unknown';
    if (!lookups(ip, Date.now())) throw new AppError('Too many lookups. Please wait a few minutes.', 429);
    const code = new URL(req.url).searchParams.get('code') || '';
    const row = await readWorkspaceRow();
    const status = row ? publicStatus(row.data, code) : null;
    if (!status) throw new AppError('No report was found with this code. Check the code and try again.', 404);
    return Response.json(status, {headers: {'Cache-Control': 'private, no-store'}});
  } catch (err) { return failure(err); }
}
