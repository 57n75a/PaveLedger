// Contractor scorecard: how each firm performs on the repairs it was notified about.
// Pure function over tickets, so the same numbers appear in the app, the council report and tests.
import type {Ticket} from './domain.ts';

export type Scorecard = {
  contractor: string;
  tickets: number;          // all tickets linked to the firm
  open: number;             // not yet closed, rejected or merged
  completed: number;        // repair reported done (awaiting verification or closed)
  avgRepairDays: number | null;  // contractor notice (or ticket creation) to repair reported
  onTimeRate: number | null;     // completed repairs reported within the repair window after the notice
  reopenRate: number | null;     // completed repairs that later had to be reopened
  overdueOpen: number;      // notified open tickets past their repair window
  warrantyCases: number;    // tickets matched to one of the firm's warranty contracts
  score: number | null;     // 0-100, null until the firm has a completed repair
  grade: 'A' | 'B' | 'C' | 'D' | null;
};

const ENDED = ['Verified closed', 'Rejected', 'Duplicate'];
const DAY = 86_400_000;
/** Repair window from the contractor notice, by priority. */
export const REPAIR_DAYS: Record<string, number> = {Urgent: 3, Standard: 14, Low: 30};
const deadline = (t: Ticket) => Date.parse(noticeAt(t)) + (REPAIR_DAYS[t.severity] || 14) * DAY;

export function noticeAt(t: Ticket): string {
  const h = (t.history || []).find(x => x.action === 'Notice prepared' || x.action === 'Acknowledged');
  return t.noticeEmailedAt || h?.at || t.created;
}

export function contractorScorecards(tickets: Ticket[], now: string): Scorecard[] {
  const by = new Map<string, Ticket[]>();
  for (const t of tickets) {
    if (!t.contractor || t.status === 'Duplicate' || t.status === 'Rejected') continue;
    by.set(t.contractor, [...(by.get(t.contractor) || []), t]);
  }
  const nowMs = Date.parse(now);
  const out: Scorecard[] = [];
  for (const [contractor, list] of by) {
    const open = list.filter(t => !ENDED.includes(t.status));
    const done = list.filter(t => t.completedAt);
    const days = done.map(t => Math.max(0, (Date.parse(t.completedAt!) - Date.parse(noticeAt(t))) / DAY));
    const onTime = done.filter(t => Date.parse(t.completedAt!) <= deadline(t)).length;
    const reopened = done.filter(t => t.reopened > 0).length;
    const overdueOpen = open.filter(t => noticeAt(t) !== t.created && deadline(t) < nowMs).length;
    const onTimeRate = done.length ? onTime / done.length : null;
    const reopenRate = done.length ? reopened / done.length : null;
    let score: number | null = null;
    if (done.length) {
      const backlog = open.length ? 1 - overdueOpen / open.length : 1;
      score = Math.round(100 * (0.4 * onTimeRate! + 0.4 * (1 - reopenRate!) + 0.2 * backlog));
    }
    out.push({
      contractor, tickets: list.length, open: open.length, completed: done.length,
      avgRepairDays: days.length ? Math.round(days.reduce((a, b) => a + b, 0) / days.length * 10) / 10 : null,
      onTimeRate, reopenRate, overdueOpen,
      warrantyCases: list.filter(t => t.contractId && t.warranty !== 'Needs review').length,
      score, grade: score === null ? null : score >= 85 ? 'A' : score >= 70 ? 'B' : score >= 55 ? 'C' : 'D',
    });
  }
  return out.sort((a, b) => (b.score ?? -1) - (a.score ?? -1) || b.tickets - a.tickets || a.contractor.localeCompare(b.contractor));
}
