// Overdue alerts and escalation, run once a day (and on demand by an admin).
// A ticket is overdue when its current owner misses the deadline:
//  - with the contractor (notice prepared to repair in progress): the repair window from the notice;
//  - otherwise: the ticket's due date.
// First the owner and the team lead are alerted; if it is still overdue after a grace period it escalates
// one step up the workspace escalation chain. Each step happens once per stage, so nobody is spammed.
import {escalationTarget, isActive, wantsNotification, type State, type Ticket, type Member} from './domain.ts';
import {REPAIR_DAYS, noticeAt} from './scorecard.ts';

const DAY = 86_400_000;
const CONTRACTOR_STAGES = ['Notice prepared', 'Acknowledged', 'Repair in progress'];
const SKIP = ['Verified closed', 'Rejected', 'Duplicate', 'On hold', 'Awaiting verification'];
const TEAM_SCOPED = ['Head Analyst', 'Analyst'];

export type OverdueMark = {stage: 'team' | 'contractor'; level: 1 | 2; since: string; at: string; escalatedTo?: string};
export type Alert = {recipient: Member; ticket: Ticket; kind: 'overdue' | 'escalated'; days: number; to?: string};

export function deadlineOf(t: Ticket): {stage: 'team' | 'contractor'; at: number} {
  if (CONTRACTOR_STAGES.includes(t.status) && t.contractor) return {stage: 'contractor', at: Date.parse(noticeAt(t)) + (REPAIR_DAYS[t.severity] || 14) * DAY};
  return {stage: 'team', at: Date.parse(t.due)};
}
/** Extra days after the deadline before escalation: half the window, at least 2 days. */
const grace = (t: Ticket, stage: 'team' | 'contractor') => Math.max(2, Math.round((stage === 'contractor' ? (REPAIR_DAYS[t.severity] || 14) : (Date.parse(t.due) - Date.parse(t.created)) / DAY) / 2)) * DAY;

function owners(s: State, t: Ticket, stage: 'team' | 'contractor'): Member[] {
  const out = new Map<string, Member>();
  for (const m of s.members) {
    if (!isActive(m) || m.demo && !m.email) continue;
    const lead = m.role === 'Head Analyst' && (m.teams || []).includes(t.team);
    const analyst = stage === 'team' && m.id === t.analyst;
    const firm = stage === 'contractor' && m.role === 'Contractor' && m.contractor === t.contractor;
    if (lead || analyst || firm) out.set(m.id, m);
  }
  return [...out.values()];
}
function roleMembers(s: State, t: Ticket, role: string): Member[] {
  return s.members.filter(m => isActive(m) && m.role === role && (!TEAM_SCOPED.includes(role) || (m.teams || []).includes(t.team)));
}

export function overdueSweep(s: State, now: string): {alerts: Alert[]; overdue: number; escalated: number; cleared: number} {
  const nowMs = Date.parse(now);
  const alerts: Alert[] = [];
  let overdue = 0, escalated = 0, cleared = 0;
  for (const t of s.tickets) {
    const mark = t.overdue;
    if (t.archived || SKIP.includes(t.status) || t.autoCloseAt) { if (mark) { delete t.overdue; cleared++; } continue; }
    const d = deadlineOf(t);
    if (!Number.isFinite(d.at)) continue;
    if (nowMs <= d.at || (mark && mark.stage !== d.stage)) {
      if (mark) { delete t.overdue; cleared++; }
      if (nowMs <= d.at) continue;
    }
    overdue++;
    const days = Math.floor((nowMs - d.at) / DAY);
    const cur = t.overdue;
    if (!cur) {
      t.overdue = {stage: d.stage, level: 1, since: new Date(d.at).toISOString(), at: now};
      const who = d.stage === 'contractor' ? t.contractor : 'the team';
      t.history.push({at: now, actor: 'System', action: 'Overdue', note: `Past the ${d.stage === 'contractor' ? 'contractor repair window' : 'due date'} (${new Date(d.at).toISOString().slice(0, 10)}). Waiting on ${who}.`, visibility: d.stage === 'contractor' ? 'shared' : 'internal'});
      for (const m of owners(s, t, d.stage)) {
        if (wantsNotification(m, 'overdue')) s.notifications.unshift({id: `od1-${t.id}-${m.id}-${now}`, recipient: m.id, ticket: t.id, text: `Overdue: ${t.road} (${t.id})`, at: now});
        alerts.push({recipient: m, ticket: t, kind: 'overdue', days});
      }
      continue;
    }
    if (cur.level === 1 && nowMs > d.at + grace(t, d.stage)) {
      const from = t.escalatedTo || 'Head Analyst';
      const to = escalationTarget(s, from) || (from !== 'Head Analyst' ? null : 'Director');
      cur.level = 2; cur.at = now;
      if (to && t.escalatedTo !== to) {
        t.escalatedTo = to; cur.escalatedTo = to; escalated++;
        t.history.push({at: now, actor: 'System', action: 'Escalated', note: `Escalated to ${to}: overdue by ${days} day(s).`, visibility: 'internal'});
        for (const m of roleMembers(s, t, to)) {
          if (wantsNotification(m, 'overdue')) s.notifications.unshift({id: `od2-${t.id}-${m.id}-${now}`, recipient: m.id, ticket: t.id, text: `Escalated to ${to}: ${t.road} is ${days} day(s) overdue`, at: now});
          alerts.push({recipient: m, ticket: t, kind: 'escalated', days, to});
        }
      }
    }
  }
  if (overdue || escalated) s.events.unshift({at: now, actor: 'System', action: `Overdue check: ${overdue} overdue, ${alerts.length} alert(s), ${escalated} escalated`});
  return {alerts, overdue, escalated, cleared};
}

/** One email per person per run, listing the tickets that newly became overdue or were escalated to them. */
export function overdueDigests(alerts: Alert[], tr: (key: string, args?: string[]) => string, appUrl: string): {to: string; subject: string; text: string}[] {
  const by = new Map<string, Alert[]>();
  for (const a of alerts) if (a.recipient.email && !a.recipient.email.endsWith('.invalid')) by.set(a.recipient.email, [...(by.get(a.recipient.email) || []), a]);
  return [...by].map(([to, list]) => ({
    to,
    subject: tr('PaveLedger: {0} ticket(s) need attention', [String(list.length)]),
    text: [
      tr('Hello {0},', [list[0].recipient.name]), '',
      tr('These tickets are past their deadline:'), '',
      ...list.map(a => `• ${a.ticket.id} · ${a.ticket.road} · ${a.kind === 'escalated' ? tr('escalated to {0}', [tr(a.to || '')]) : tr('overdue')} · ${tr('{0} day(s) late', [String(a.days)])}`),
      '', tr('Open the workspace: {0}', [appUrl]), '', tr('You receive this because overdue alerts are on in your notification settings.'),
    ].join('\n'),
  }));
}
