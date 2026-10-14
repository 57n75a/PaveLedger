// Resident reports: anyone can report a road problem without an account and follow it with a tracking code.
// Pure functions so the rules are tested without a server. The API routes call these.
import {openTicketsNear, wantsNotification, isActive, type State, type Ticket, type Status} from './domain.ts';
import {ticketFlow, PHASES} from './workflow.ts';

export const SAME_DEFECT_RADIUS_M = 20;
export const MAX_DESCRIPTION = 1000;

export type ResidentReport = {
  lat: number; lng: number; accuracy?: number;
  address?: string; road?: string;
  description: string;
  dangerous: boolean;
  email?: string;
};

// Codes avoid look-alike characters (0/O, 1/I/L) so people can read them out over the phone.
const ALPHABET = '23456789ABCDEFGHJKMNPQRSTUVWXYZ';
export function makePublicCode(random: (n: number) => Uint8Array): string {
  const bytes = random(10);
  let out = '';
  for (let i = 0; i < 10; i++) out += ALPHABET[bytes[i] % ALPHABET.length];
  return out.slice(0, 5) + '-' + out.slice(5);
}
export const normalizeCode = (code: string) => code.trim().toUpperCase().replace(/[^0-9A-Z]/g, '').replace(/^(.{5})(.{5})$/, '$1-$2');

export type ApplyResult = {ticket: Ticket; merged: boolean};

/**
 * Add a resident report to the workspace. A report within 20 m of an open ticket is added to that ticket
 * (one more observation, and urgent if the resident says it is dangerous) instead of creating a duplicate.
 */
export function applyResidentReport(s: State, r: ResidentReport, now: string, ids: {ticketId: string; code: string}): ApplyResult {
  const note = r.description.trim().slice(0, MAX_DESCRIPTION);
  const existing = openTicketsNear(s, r.lat, r.lng, SAME_DEFECT_RADIUS_M)[0];
  if (existing) {
    existing.observations++;
    existing.residentReports = (existing.residentReports || 0) + 1;
    existing.updated = now;
    if (r.dangerous && existing.severity !== 'Urgent') {
      existing.severity = 'Urgent';
      existing.history.push({at: now, actor: 'Resident', action: 'Priority raised', note: 'A resident reported this location as dangerous.', visibility: 'internal'});
    }
    existing.history.push({at: now, actor: 'Resident', action: 'Resident report added', note, visibility: 'internal'});
    existing.publicCode ||= ids.code;
    if (r.email && !existing.reporterEmail) existing.reporterEmail = r.email;
    notifyLeads(s, existing, `Another resident report: ${existing.road}`, now);
    s.events.unshift({at: now, actor: 'Resident', action: 'Resident report added to ' + existing.id});
    return {ticket: existing, merged: true};
  }
  const road = (r.road || r.address || '').trim().slice(0, 150) || `Location ${r.lat.toFixed(5)}, ${r.lng.toFixed(5)}`;
  const severity = r.dangerous ? 'Urgent' : 'Standard';
  const t: Ticket = {
    id: ids.ticketId, title: 'Resident report', road, address: r.address?.trim().slice(0, 300) || undefined,
    lat: r.lat, lng: r.lng, accuracy: Math.min(Math.max(r.accuracy || 25, 1), 1000), lane: 'Lane 1',
    severity, status: 'Detected' as Status, team: s.teams[0] || '', analyst: '', contractor: '', warranty: 'Needs review',
    source: 'Resident report', confidence: 0, created: now, updated: now,
    due: new Date(Date.parse(now) + (severity === 'Urgent' ? 2 : 14) * 86_400_000).toISOString(),
    reopened: 0, observations: 1, note, evidence: [], publicCode: ids.code, reporterEmail: r.email || undefined, residentReports: 1,
    history: [{at: now, actor: 'Resident', action: 'Detected', note, visibility: 'internal'}],
  };
  s.tickets.unshift(t);
  s.events.unshift({at: now, actor: 'Resident', action: 'Created ' + t.id + ' from a resident report'});
  notifyLeads(s, t, `New resident report: ${road}`, now);
  return {ticket: t, merged: false};
}

function notifyLeads(s: State, t: Ticket, text: string, now: string) {
  for (const m of s.members) {
    if (!isActive(m)) continue;
    const lead = m.role === 'Head Analyst' && (m.teams || []).includes(t.team);
    if ((lead || m.id === t.analyst) && wantsNotification(m, 'assignment'))
      s.notifications.unshift({id: 'n-' + t.id + '-' + now + '-' + m.id, recipient: m.id, ticket: t.id, text, at: now});
  }
}

export type PublicStatus = {
  code: string; road: string; address?: string; reported: string; updated: string;
  steps: {label: string; state: string; at?: string}[];
  outcome: 'in-progress' | 'repaired' | 'not-a-defect' | 'merged' | 'on-hold';
  reports: number;
};

/** What the public tracking page may show: progress and dates only, never notes, names or evidence. */
export function publicStatus(s: State, code: string): PublicStatus | null {
  const c = normalizeCode(code);
  if (!/^[0-9A-Z]{5}-[0-9A-Z]{5}$/.test(c)) return null;
  let t = s.tickets.find(x => x.publicCode === c);
  if (!t) return null;
  const merged = t.status === 'Duplicate' && t.duplicateOf ? s.tickets.find(x => x.id === t!.duplicateOf) : undefined;
  if (merged) t = merged;
  const flow = ticketFlow(t);
  return {
    code: c, road: t.road, address: t.address, reported: t.created, updated: t.updated,
    steps: flow.steps.map((st, i) => ({label: PHASES[i].label, state: st.state, at: st.state === 'upcoming' ? undefined : st.at})),
    outcome: merged ? 'merged' : t.status === 'Verified closed' ? 'repaired' : t.status === 'Rejected' ? 'not-a-defect' : t.status === 'On hold' ? 'on-hold' : 'in-progress',
    reports: t.residentReports || 1,
  };
}
