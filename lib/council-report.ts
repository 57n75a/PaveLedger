// Monthly council report: the figures a municipality presents to its council for one calendar month.
// Pure function over tickets so the PDF and the tests use the same numbers.
import type {Ticket} from './domain.ts';
import {contractorScorecards, type Scorecard} from './scorecard.ts';

const DAY = 86_400_000;
const ENDED = ['Verified closed', 'Rejected', 'Duplicate'];

export type MonthStats = {opened: number; closed: number};
export type CouncilReport = {
  month: string;              // YYYY-MM
  from: string; to: string;   // ISO bounds, [from, to)
  opened: number; closed: number; rejected: number;
  openAtEnd: number; overdueAtEnd: number; urgentOpenAtEnd: number;
  avgDaysToClose: number | null;
  residentReports: number;
  warrantyRepairs: number;    // repairs closed this month under a contractor warranty
  bySeverity: {severity: string; opened: number; closed: number}[];
  byTeam: {team: string; opened: number; closed: number; openAtEnd: number}[];
  trend: ({month: string} & MonthStats)[]; // the six months ending with this one
  previous: MonthStats;
  oldestOpen: {id: string; road: string; team: string; severity: string; status: string; days: number}[];
  contractors: Scorecard[];
  costs: {estimated: number; actual: number; recovered: number; currency?: string} | null;
};

export function monthBounds(month: string): {from: string; to: string} {
  const [y, m] = month.split('-').map(Number);
  return {from: new Date(Date.UTC(y, m - 1, 1)).toISOString(), to: new Date(Date.UTC(y, m, 1)).toISOString()};
}
export function shiftMonth(month: string, by: number): string {
  const [y, m] = month.split('-').map(Number);
  const d = new Date(Date.UTC(y, m - 1 + by, 1));
  return d.toISOString().slice(0, 7);
}

const inRange = (iso: string | undefined, from: string, to: string) => !!iso && iso >= from && iso < to;
// When a ticket ended: closed date, or the date of its rejection or merge in the history.
function endedAt(t: Ticket): string | undefined {
  if (t.closedAt) return t.closedAt;
  if (!ENDED.includes(t.status)) return undefined;
  const h = [...(t.history || [])].reverse().find(x => x.action === t.status);
  return h?.at || t.updated;
}
const openAt = (t: Ticket, at: string) => t.created < at && !((e => e && e < at)(endedAt(t)));

function stats(tickets: Ticket[], month: string): MonthStats {
  const {from, to} = monthBounds(month);
  return {
    opened: tickets.filter(t => inRange(t.created, from, to)).length,
    closed: tickets.filter(t => t.status === 'Verified closed' && inRange(t.closedAt, from, to)).length,
  };
}

export function councilReport(all: Ticket[], month: string, now: string): CouncilReport {
  const tickets = all.filter(t => t.status !== 'Duplicate');
  const {from, to} = monthBounds(month);
  const end = to < now ? to : now;
  const opened = tickets.filter(t => inRange(t.created, from, to));
  const closed = tickets.filter(t => t.status === 'Verified closed' && inRange(t.closedAt, from, to));
  const rejected = tickets.filter(t => t.status === 'Rejected' && inRange(endedAt(t), from, to));
  const openEnd = tickets.filter(t => openAt(t, end));
  const durations = closed.map(t => (Date.parse(t.closedAt!) - Date.parse(t.created)) / DAY);
  const teams = [...new Set(tickets.map(t => t.team).filter(Boolean))].sort();
  let estimated = 0, actual = 0, recovered = 0, anyCost = false;
  for (const t of closed) {
    const c = (t as Ticket & {cost?: {estimate?: number; actual?: number; recovered?: number}}).cost;
    if (!c) continue;
    anyCost = true; estimated += c.estimate || 0; actual += c.actual || 0; recovered += c.recovered || 0;
  }
  return {
    month, from, to,
    opened: opened.length, closed: closed.length, rejected: rejected.length,
    openAtEnd: openEnd.length,
    overdueAtEnd: openEnd.filter(t => t.due < end).length,
    urgentOpenAtEnd: openEnd.filter(t => t.severity === 'Urgent').length,
    avgDaysToClose: durations.length ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length * 10) / 10 : null,
    residentReports: opened.filter(t => t.source === 'Resident report').length,
    warrantyRepairs: closed.filter(t => t.contractId && t.warranty !== 'Needs review').length,
    bySeverity: ['Urgent', 'Standard', 'Low'].map(severity => ({severity, opened: opened.filter(t => t.severity === severity).length, closed: closed.filter(t => t.severity === severity).length})),
    byTeam: teams.map(team => ({team, opened: opened.filter(t => t.team === team).length, closed: closed.filter(t => t.team === team).length, openAtEnd: openEnd.filter(t => t.team === team).length})),
    trend: [-5, -4, -3, -2, -1, 0].map(k => { const m = shiftMonth(month, k); return {month: m, ...stats(tickets, m)}; }),
    previous: stats(tickets, shiftMonth(month, -1)),
    oldestOpen: openEnd.sort((a, b) => a.created.localeCompare(b.created)).slice(0, 5)
      .map(t => ({id: t.id, road: t.road, team: t.team, severity: t.severity, status: t.status, days: Math.floor((Date.parse(end) - Date.parse(t.created)) / DAY)})),
    contractors: contractorScorecards(tickets.filter(t => t.created < to), end),
    costs: anyCost ? {estimated, actual, recovered} : null,
  };
}
