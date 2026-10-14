// Demo packs: complete sample worlds (teams, people, contracts, tickets) that an admin can load or reset.
// Packs live in demo/*.json with dates relative to today, so a freshly loaded demo always looks current.
import serbia from '../demo/serbia.json' with {type: 'json'};
import canada from '../demo/canada.json' with {type: 'json'};
import {transitions, type State, type Member, type Ticket, type Status, type Role} from './domain.ts';

export type PackTicket = {id: string; title: string; road: string; address?: string; lat: number; lng: number; severity: string; team: string; analyst?: string; source: string; confidence?: number; observations: number; daysAgo: number; contractId?: string; reopened?: number; holdFrom?: string; duplicateOf?: string; path: string[]};
export type DemoPack = {name: string; description: string; teams: string[]; people: {id: string; name: string; role: string; teams: string[]; contractor?: string; vehicleTag?: string; phone?: string}[]; contracts: (State['contracts'][number])[]; notes: Record<string, string>; tickets: PackTicket[]};

export const DEMO_PACKS: Record<'serbia' | 'canada', DemoPack> = {serbia: serbia as DemoPack, canada: canada as DemoPack};
export type PackId = keyof typeof DEMO_PACKS;

const DAY = 86400000;
const iso = (ms: number) => new Date(ms).toISOString();
const DUE_DAYS: Record<string, number> = {Urgent: 2, Standard: 14, Low: 30};

/** Check a pack against the workflow so a hand-edited file cannot create impossible tickets. Returns problems found. */
export function checkPack(p: DemoPack): string[] {
  const problems: string[] = [];
  const people = new Set(p.people.map(x => x.id)), contracts = new Set(p.contracts.map(c => c.id)), teams = new Set(p.teams), ids = new Set<string>();
  for (const t of p.tickets) {
    if (ids.has(t.id)) problems.push(`${t.id}: duplicate id`); ids.add(t.id);
    if (!teams.has(t.team)) problems.push(`${t.id}: unknown team ${t.team}`);
    if (t.analyst && !people.has(t.analyst)) problems.push(`${t.id}: unknown analyst ${t.analyst}`);
    if (t.contractId && !contracts.has(t.contractId)) problems.push(`${t.id}: unknown contract ${t.contractId}`);
    let at = 'Detected';
    for (const next of t.path) {
      const allowed = at === 'On hold' ? [t.holdFrom || 'Investigating'] : transitions[at] || [];
      if (!allowed.includes(next)) { problems.push(`${t.id}: ${at} cannot move to ${next}`); break; }
      at = next;
    }
    if (t.duplicateOf && !p.tickets.some(x => x.id === t.duplicateOf)) problems.push(`${t.id}: unknown primary ${t.duplicateOf}`);
  }
  return problems;
}

/** Replace the demo content of a workspace with a pack. Real sign-in accounts are kept; demo people are replaced. */
export function loadDemoPack(s: State, packId: PackId, keep: Member[], nowISO: string, actorName: string): void {
  const p = DEMO_PACKS[packId];
  const problems = checkPack(p);
  if (problems.length) throw new Error('Demo pack is invalid: ' + problems.join('; '));
  const now = Date.parse(nowISO);
  const firmOf = (contractId?: string) => p.contracts.find(c => c.id === contractId)?.contractor || '';
  const byRole = (role: string) => p.people.find(x => x.role === role);
  const lead = byRole('Head Analyst'), auditor = byRole('Auditor'), vehicle = byRole('Vehicle');

  const members: Member[] = [
    ...keep.map(m => ({...m, teams: (m.teams || []).filter(t => p.teams.includes(t))})),
    ...p.people.map(x => ({id: x.id, name: x.name, email: x.id.replace(/^demo-/, '') + '@example.invalid', role: x.role as Role, teams: x.teams, contractor: x.contractor || '', vehicleTag: x.vehicleTag, phone: x.phone, active: true, demo: true})),
  ];
  const notifications: State['notifications'] = [];

  const tickets: Ticket[] = p.tickets.map((pt, n) => {
    const created = now - pt.daysAgo * DAY - (n % 5) * 3600_000 - 2 * 3600_000;
    const end = now - (1 + (n % 3)) * 3600_000;
    const steps = pt.path.length;
    const at = (i: number) => iso(created + (end - created) * (i + 1) / (steps + 1));
    const analyst = pt.analyst ? p.people.find(x => x.id === pt.analyst) : undefined;
    const contractorPerson = p.people.find(x => x.role === 'Contractor' && x.contractor === firmOf(pt.contractId));
    const fromDashcam = pt.source === 'Automated dashcam';
    const actorFor = (st: string) => {
      if (['Team assigned', 'Analyst assigned', 'On hold'].includes(st)) return lead?.name || actorName;
      if (['Acknowledged', 'Repair in progress', 'Awaiting verification'].includes(st)) return contractorPerson?.name || lead?.name || actorName;
      if (['Verified closed', 'Reopened'].includes(st)) return auditor?.name || actorName;
      return analyst?.name || lead?.name || actorName;
    };
    const history: Ticket['history'] = [{at: iso(created), actor: fromDashcam ? vehicle?.name || 'System' : 'System', action: 'Detected', note: p.notes['Detected'] || '', visibility: 'internal'}];
    let completedAt: string | undefined, closedAt: string | undefined;
    pt.path.forEach((st, i) => {
      const when = at(i);
      history.push({at: when, actor: actorFor(st), action: st, note: p.notes[st] || '', visibility: ['Notice prepared', 'Acknowledged', 'Repair in progress', 'Awaiting verification', 'Verified closed', 'Reopened'].includes(st) ? 'shared' : 'internal'});
      if (st === 'Awaiting verification') completedAt = when;
      if (st === 'Verified closed') closedAt = when;
      if (st === 'Reopened') closedAt = undefined;
    });
    const status = (pt.path[pt.path.length - 1] || 'Detected') as Status;
    const updated = history[history.length - 1].at;
    if (pt.analyst && ['Analyst assigned', 'Investigating', 'Confirmed', 'Reopened'].includes(status)) notifications.push({id: 'demo-n-' + pt.id, recipient: pt.analyst, ticket: pt.id, text: 'Assigned to you: ' + pt.road, at: history.find(h => h.action === 'Analyst assigned')?.at || updated});
    return {
      id: pt.id, title: pt.title, road: pt.road, address: pt.address, lat: pt.lat, lng: pt.lng, accuracy: fromDashcam ? 4.5 : 8, lane: 'Lane 1',
      severity: pt.severity, status, team: pt.team, analyst: pt.analyst || '', contractor: firmOf(pt.contractId), contractId: pt.contractId,
      warranty: pt.contractId ? 'Candidate match' : 'Needs review', source: pt.source, confidence: pt.confidence || 0,
      created: iso(created), observedAt: iso(created - 3600_000), updated, due: iso(created + (DUE_DAYS[pt.severity] || 14) * DAY),
      reopened: pt.reopened || 0, observations: pt.observations, note: p.notes[status] || '', history, evidence: [],
      reportedBy: fromDashcam ? vehicle?.id : lead?.id, holdFrom: status === 'On hold' ? (pt.holdFrom as Status) : undefined, duplicateOf: pt.duplicateOf,
      completedAt, completedBy: completedAt ? contractorPerson?.id || lead?.id : undefined, closedAt, closedBy: closedAt ? auditor?.id : undefined,
    } as Ticket;
  });

  s.teams = [...p.teams];
  s.teamProfiles = {};
  s.members = members;
  s.contracts = p.contracts.map(c => ({...c}));
  s.tickets = tickets;
  s.notifications = notifications;
  s.outbox = [];
  s.events = [{at: nowISO, actor: actorName, action: 'Demo data loaded: ' + p.name}];
}
