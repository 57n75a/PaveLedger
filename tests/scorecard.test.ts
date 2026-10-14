import {test} from 'node:test';
import assert from 'node:assert/strict';
import {contractorScorecards} from '../lib/scorecard.ts';
import {seed} from '../lib/domain.ts';
import {loadDemoPack} from '../lib/demo.ts';

const base = (o: Record<string, unknown>) => ({id: 'T', title: 't', road: 'r', lat: 0, lng: 0, accuracy: 5, severity: 'Standard', status: 'Investigating', team: 'A', analyst: '', contractor: 'Firm', warranty: 'Needs review', source: 's', confidence: 0, created: '2026-10-01T00:00:00.000Z', updated: '2026-10-01T00:00:00.000Z', due: '2026-10-10T00:00:00.000Z', reopened: 0, observations: 1, note: '', history: [], ...o}) as any;

test('scores on-time, first-time-fix repairs highly', () => {
  const [s] = contractorScorecards([
    base({id: 'a', status: 'Verified closed', completedAt: '2026-10-05T00:00:00.000Z', history: [{at: '2026-10-02T00:00:00.000Z', action: 'Notice prepared', actor: 'x', note: ''}]}),
    base({id: 'b', status: 'Awaiting verification', completedAt: '2026-10-06T00:00:00.000Z'}),
  ], '2026-10-08T00:00:00.000Z');
  assert.equal(s.completed, 2);
  assert.equal(s.onTimeRate, 1);
  assert.equal(s.reopenRate, 0);
  assert.equal(s.avgRepairDays, 4); // 3 days from notice, 5 days from creation
  assert.equal(s.score, 100);
  assert.equal(s.grade, 'A');
});

test('late, reopened and overdue work lowers the score', () => {
  const [s] = contractorScorecards([
    base({id: 'a', status: 'Verified closed', completedAt: '2026-10-20T00:00:00.000Z', reopened: 1}),
    base({id: 'b', status: 'Repair in progress', history: [{at: '2026-10-02T00:00:00.000Z', action: 'Notice prepared', actor: 'x', note: ''}]}),
  ], '2026-10-25T00:00:00.000Z');
  assert.equal(s.onTimeRate, 0);
  assert.equal(s.reopenRate, 1);
  assert.equal(s.overdueOpen, 1);
  assert.equal(s.score, 0);
  assert.equal(s.grade, 'D');
});

test('firms without a completed repair have no score yet', () => {
  const [s] = contractorScorecards([base({id: 'a', status: 'Acknowledged'})], '2026-10-05T00:00:00.000Z');
  assert.equal(s.score, null);
  assert.equal(s.grade, null);
});

test('rejected and duplicate tickets do not count', () => {
  const list = contractorScorecards([base({id: 'a', status: 'Rejected'}), base({id: 'b', status: 'Duplicate'})], '2026-10-05T00:00:00.000Z');
  assert.equal(list.length, 0);
});

test('demo packs produce a scorecard for each firm with work', () => {
  for (const pack of ['serbia', 'canada'] as const) {
    const st = seed('o', 'o@x'); loadDemoPack(st, pack, [], '2026-10-14T10:00:00.000Z', 'S');
    const cards = contractorScorecards(st.tickets, '2026-10-14T10:00:00.000Z');
    assert.ok(cards.length >= 2, pack);
    assert.ok(cards.some(c => c.score !== null), pack);
  }
});
