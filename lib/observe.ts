// Another report of a problem that already has an open ticket: add it to that ticket instead of a duplicate.
// Used for staff reports and resident reports. Repeated reports raise the priority.
import {wantsNotification, isActive, type State, type Ticket} from './domain.ts';

export const MERGE_RADIUS_M = 20;
/** Priority rises with the number of independent observations. */
export const RAISE_AT = {toStandard: 3, toUrgent: 5};

export function addObservation(s: State, t: Ticket, o: {now: string; actor: string; note: string; urgent?: boolean; source?: string}): {raised: boolean} {
  t.observations++;
  t.updated = o.now;
  t.history.push({at: o.now, actor: o.actor, action: 'Observation added', note: [o.source, o.note].filter(Boolean).join(': ').slice(0, 2000), visibility: 'internal'});
  const before = t.severity;
  if (o.urgent) t.severity = 'Urgent';
  else if (t.severity === 'Low' && t.observations >= RAISE_AT.toStandard) t.severity = 'Standard';
  else if (t.severity === 'Standard' && t.observations >= RAISE_AT.toUrgent) t.severity = 'Urgent';
  const raised = t.severity !== before;
  if (raised) {
    t.history.push({at: o.now, actor: 'System', action: 'Priority raised', note: o.urgent ? `Raised to ${t.severity}: reported as dangerous.` : `Raised to ${t.severity}: reported ${t.observations} times.`, visibility: 'internal'});
    // The due date follows the new priority, but never moves later.
    const days = t.severity === 'Urgent' ? 2 : 14;
    const due = new Date(Date.parse(o.now) + days * 86_400_000).toISOString();
    if (due < t.due) t.due = due;
  }
  for (const m of s.members) {
    if (!isActive(m)) continue;
    const lead = m.role === 'Head Analyst' && (m.teams || []).includes(t.team);
    if ((m.id === t.analyst || (raised && lead)) && wantsNotification(m, 'statusChange'))
      s.notifications.unshift({id: `obs-${t.id}-${m.id}-${o.now}`, recipient: m.id, ticket: t.id, text: raised ? `Priority raised to ${t.severity}: ${t.road}` : `New observation: ${t.road}`, at: o.now});
  }
  return {raised};
}
