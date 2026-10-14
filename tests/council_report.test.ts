import {test} from 'node:test';
import assert from 'node:assert/strict';
import {councilReport, monthBounds, shiftMonth} from '../lib/council-report.ts';
import {seed} from '../lib/domain.ts';
import {loadDemoPack} from '../lib/demo.ts';

const t = (o: Record<string, unknown>) => ({id: 'T', title: 't', road: 'r', lat: 0, lng: 0, accuracy: 5, severity: 'Standard', status: 'Investigating', team: 'North', analyst: '', contractor: '', warranty: 'Needs review', source: 'Manual report', confidence: 0, created: '2026-09-10T00:00:00.000Z', updated: '2026-09-10T00:00:00.000Z', due: '2026-09-24T00:00:00.000Z', reopened: 0, observations: 1, note: '', history: [], ...o}) as any;

test('month helpers', () => {
  assert.deepEqual(monthBounds('2026-12'), {from: '2026-12-01T00:00:00.000Z', to: '2027-01-01T00:00:00.000Z'});
  assert.equal(shiftMonth('2026-01', -1), '2025-12');
  assert.equal(shiftMonth('2026-10', 2), '2026-12');
});

test('counts opened, closed, open at month end and time to close', () => {
  const r = councilReport([
    t({id: 'a', created: '2026-09-02T00:00:00.000Z', status: 'Verified closed', closedAt: '2026-09-12T00:00:00.000Z', contractId: 'C1', warranty: 'Candidate match'}),
    t({id: 'b', created: '2026-09-20T00:00:00.000Z', severity: 'Urgent', due: '2026-09-22T00:00:00.000Z'}),
    t({id: 'c', created: '2026-08-20T00:00:00.000Z', status: 'Verified closed', closedAt: '2026-09-05T00:00:00.000Z'}),
    t({id: 'd', created: '2026-10-02T00:00:00.000Z'}),
    t({id: 'e', created: '2026-09-03T00:00:00.000Z', source: 'Resident report', status: 'Duplicate'}),
  ], '2026-09', '2026-10-14T00:00:00.000Z');
  assert.equal(r.opened, 2);            // a, b (duplicates do not count)
  assert.equal(r.closed, 2);            // a, c
  assert.equal(r.openAtEnd, 1);         // b
  assert.equal(r.overdueAtEnd, 1);
  assert.equal(r.urgentOpenAtEnd, 1);
  assert.equal(r.avgDaysToClose, 13);   // (10 + 16) / 2
  assert.equal(r.warrantyRepairs, 1);
  assert.equal(r.previous.opened, 1);   // c in August
  assert.equal(r.trend.length, 6);
  assert.equal(r.trend[5].month, '2026-09');
  assert.equal(r.byTeam[0].team, 'North');
  assert.equal(r.oldestOpen[0].id, 'b');
});

test('demo pack gives a non-empty report for the current month', () => {
  const now = new Date().toISOString();
  const s = seed('o', 'o@x'); loadDemoPack(s, 'serbia', [], now, 'S');
  const r = councilReport(s.tickets, now.slice(0, 7), now);
  assert.ok(r.opened + r.openAtEnd > 0);
  assert.ok(r.byTeam.length >= 2);
});
