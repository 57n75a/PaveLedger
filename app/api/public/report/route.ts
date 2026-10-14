// Public endpoint: a resident reports a road problem, with an optional photo. No account needed.
import {randomUUID, randomBytes, createHash} from 'node:crypto';
import {z} from 'zod';
import {adminClient, readWorkspaceRow, saveWorkspace, workspaceId} from '@/lib/store';
import {failure} from '@/lib/context';
import {AppError} from '@/lib/actions';
import {makeLimiter} from '@/lib/mail';
import {reverseStreet} from '@/lib/geo';
import {instance} from '@/lib/instance';
import {applyResidentReport, makePublicCode, MAX_DESCRIPTION} from '@/lib/public-report';
import type {Evidence} from '@/lib/domain';
export const runtime = 'nodejs'; export const dynamic = 'force-dynamic';

const bucket = 'paveledger-evidence';
const perPerson = makeLimiter(5, 60 * 60_000);     // 5 reports per hour from one connection
const perDay = makeLimiter(300, 24 * 60 * 60_000); // overall daily ceiling for the whole workspace
const headers = {'Cache-Control': 'private, no-store'};

const Fields = z.object({
  lat: z.coerce.number().min(-90).max(90),
  lng: z.coerce.number().min(-180).max(180),
  accuracy: z.coerce.number().positive().max(5000).optional(),
  address: z.string().trim().max(300).optional(),
  description: z.string().trim().min(5).max(MAX_DESCRIPTION),
  dangerous: z.enum(['true', 'false']).optional(),
  email: z.string().trim().email().max(200).optional().or(z.literal('')),
  website: z.string().max(0).optional(), // honeypot: people never fill this hidden field
});

function clientKey(req: Request) {
  const ip = (req.headers.get('x-forwarded-for') || '').split(',')[0].trim() || req.headers.get('x-real-ip') || 'unknown';
  return createHash('sha256').update(ip).digest('hex').slice(0, 16);
}

function sniff(bytes: Buffer): string {
  if (bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255) return 'image/jpeg';
  if (bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) return 'image/png';
  if (bytes.subarray(0, 4).toString() === 'RIFF' && bytes.subarray(8, 12).toString() === 'WEBP') return 'image/webp';
  return '';
}

export async function POST(req: Request) {
  try {
    const origin = req.headers.get('origin'); if (origin && origin !== new URL(req.url).origin) throw new AppError('Origin mismatch', 403);
    if (Number(req.headers.get('content-length')) > 6_300_000) throw new AppError('Use a photo smaller than 6 MB.', 413);
    const form = await req.formData();
    const raw = Object.fromEntries([...form.entries()].filter(([, v]) => typeof v === 'string'));
    let v: z.infer<typeof Fields>;
    try { v = Fields.parse(raw); } catch { throw new AppError('Mark the location on the map and describe the problem in at least 5 characters.'); }
    if (v.website) return Response.json({code: 'XXXXX-XXXXX', merged: false}, {headers}); // quietly ignore bots
    const [w, south, e, north] = instance.bbox;
    if (v.lng < w || v.lng > e || v.lat < south || v.lat > north) throw new AppError('This location is outside the area this service covers.');
    const now = Date.now();
    if (!perPerson(clientKey(req), now)) throw new AppError('You have sent several reports in a short time. Please try again later.', 429);
    if (!perDay('all', now)) throw new AppError('The service is receiving many reports right now. Please try again tomorrow.', 429);

    // Optional photo, checked by its contents rather than its name.
    const file = form.get('photo');
    let photo: {bytes: Buffer; mime: string; name: string; sha256: string} | null = null;
    if (file instanceof File && file.size > 0) {
      if (file.size > 6_000_000) throw new AppError('Use a photo smaller than 6 MB.', 413);
      const bytes = Buffer.from(await file.arrayBuffer());
      const mime = sniff(bytes);
      if (!mime) throw new AppError('The photo must be a JPEG, PNG or WebP image.');
      photo = {bytes, mime, name: file.name.slice(0, 150) || 'photo', sha256: createHash('sha256').update(bytes).digest('hex')};
    }

    const street = await reverseStreet(v.lat, v.lng).catch(() => null);
    const nowIso = new Date().toISOString();
    const code = makePublicCode(n => randomBytes(n));
    const ticketId = `PL-${nowIso.slice(0, 4)}-${randomUUID().slice(0, 8).toUpperCase()}`;

    // Save with compare-and-swap; retry if staff changed the workspace at the same moment.
    for (let attempt = 0; attempt < 4; attempt++) {
      const row = await readWorkspaceRow();
      if (!row) throw new AppError('Reporting is not open yet for this municipality.', 503);
      const s = row.data;
      if (s.tickets.length >= 500) throw new AppError('The service cannot accept new reports right now. Please contact the municipality directly.', 503);
      const {ticket, merged} = applyResidentReport(s, {
        lat: v.lat, lng: v.lng, accuracy: v.accuracy, address: v.address, road: street || undefined,
        description: v.description, dangerous: v.dangerous === 'true', email: v.email || undefined,
      }, nowIso, {ticketId, code});
      let evidenceKey = '';
      if (photo && (ticket.evidence || []).length < 40 && !(ticket.evidence || []).some(x => x.sha256 === photo!.sha256)) {
        const id = randomUUID();
        evidenceKey = `${workspaceId}/${ticket.id}/${id}`;
        const ev: Evidence = {id, name: photo.name, mime: photo.mime, bytes: photo.bytes.length, sha256: photo.sha256, purpose: 'detection', capturedAt: nowIso, uploadedAt: nowIso, uploadedBy: 'resident', lat: v.lat, lng: v.lng, accuracy: Math.min(v.accuracy || 25, 1000), lane: 'Lane 1', quality: 'clear', visibility: 'internal'};
        const {error} = await adminClient().storage.from(bucket).upload(evidenceKey, photo.bytes, {contentType: photo.mime, upsert: false});
        if (error) evidenceKey = ''; // keep the report even if the photo cannot be stored
        else { ticket.evidence = [...(ticket.evidence || []), ev]; ticket.history.push({at: nowIso, actor: 'Resident', action: 'Evidence uploaded', note: `Resident photo ${id}; SHA-256 ${photo.sha256}`, visibility: 'internal'}); }
      }
      if (await saveWorkspace(s, row.revision)) return Response.json({code: ticket.publicCode, merged}, {headers});
      if (evidenceKey) await adminClient().storage.from(bucket).remove([evidenceKey]);
    }
    throw new AppError('The service is busy. Please send the report again.', 409);
  } catch (err) { return failure(err); }
}
