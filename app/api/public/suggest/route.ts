// Public address suggestions for the resident report form, limited to this deployment's country.
import {failure} from '@/lib/context';
import {AppError} from '@/lib/actions';
import {makeLimiter} from '@/lib/mail';
import {suggestAddresses} from '@/lib/geo';
import {instance} from '@/lib/instance';
export const runtime = 'nodejs'; export const dynamic = 'force-dynamic';

const limiter = makeLimiter(60, 10 * 60_000);

export async function GET(req: Request) {
  try {
    const ip = (req.headers.get('x-forwarded-for') || '').split(',')[0].trim() || 'unknown';
    if (!limiter(ip, Date.now())) throw new AppError('Too many lookups. Please wait a few minutes or tap the map instead.', 429);
    const url = new URL(req.url);
    const q = (url.searchParams.get('q') || '').trim();
    if (q.length < 3) return Response.json([], {headers: {'Cache-Control': 'private, no-store'}});
    if (q.length > 200) throw new AppError('Enter a shorter address.');
    let rows;
    try { rows = await suggestAddresses(q, {country: instance.geocodeCountry, bbox: instance.bbox, lang: url.searchParams.get('lang') || undefined}); }
    catch { throw new AppError('Address lookup is unavailable right now. Tap the map instead.', 503); }
    return Response.json(rows, {headers: {'Cache-Control': 'private, no-store'}});
  } catch (e) { return failure(e); }
}
