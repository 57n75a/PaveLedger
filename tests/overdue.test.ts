import {test} from 'node:test';
import assert from 'node:assert/strict';
import {overdueSweep, overdueDigests, deadlineOf} from '../lib/overdue.ts';
import {seed, normalizeState} from '../lib/domain.ts';

function world() {
  const s = normalizeState(seed('owner', 'owner@example.test'));
  s.teams = ['North'];
  s.members = [
    {id: 'lead', name: 'Lead', email: 'lead@city.rs', role: 'Head Analyst', teams: ['North'], active: true} as any,
    {id: 'ana', name: 'Ana', email: 'ana@city.rs', role: 'Analyst', teams: ['North'], active: true} as any,
    {id: 'dir', name: 'Director', email: 'dir@city.rs', role: 'Director', teams: [], active: true} as any,
    {id: 'firm', name: 'Firm user', email: 'firm@asphalt.rs', role: 'Contractor', contractor: 'Asphalt', teams: [], active: true} as any,
  ];
  s.notifications = []; s.events = [];
  s.tickets = [{id: 'T1', title: 't', road: 'Main', lat: 0, lng: 0, accuracy: 5, severity: 'Standard', status: 'Investigating', team: 'North', analyst: 'ana', contractor: '', warranty: 'Needs review', source: 's', confidence: 0, created: '2026-10-01T00:00:00.000Z', updated: '2026-10-01T00:00:00.000Z', due: '2026-10-05T00:00:00.000Z', reopened: 0, observations: 1, note: '', history: [], evidence: []} as any];
  return s;
}

test('not overdue before the due date', () => {
  const s = world();
  const r = overdueSweep(s, '2026-10-04T00:00:00.000Z');
  assert.equal(r.overdue, 0);
  assert.equal(s.notifications.length, 0);
});

test('first alert goes to the analyst and team lead, once', () => {
  const s = world();
  const r = overdueSweep(s, '2026-10-06T00:00:00.000Z');
  assert.equal(r.overdue, 1);
  assert.deepEqual(r.alerts.map(a => a.recipient.id).sort(), ['ana', 'lead']);
  assert.equal(s.tickets[0].overdue?.level, 1);
  const again = overdueSweep(s, '2026-10-06T12:00:00.000Z');
  assert.equal(again.alerts.length, 0);
});

test('still overdue after the grace period escalates up the chain', () => {
  const s = world();
  overdueSweep(s, '2026-10-06T00:00:00.000Z');
  const r = overdueSweep(s, '2026-10-09T00:00:00.000Z'); // 4-day window -> 2-day grace
  assert.equal(r.escalated, 1);
  assert.equal(s.tickets[0].escalatedTo, 'Director');
  assert.deepEqual(r.alerts.map(a => a.recipient.id), ['dir']);
  assert.ok(s.tickets[0].history.some(h => h.action === 'Escalated'));
});

test('contractor stage uses the repair window from the notice and alerts the firm', () => {
  const s = world();
  Object.assign(s.tickets[0], {status: 'Acknowledged', contractor: 'Asphalt', due: '2030-01-01T00:00:00.000Z', history: [{at: '2026-10-02T00:00:00.000Z', action: 'Notice prepared', actor: 'x', note: ''}]});
  assert.equal(deadlineOf(s.tickets[0]).stage, 'contractor');
  const r = overdueSweep(s, '2026-10-17T00:00:00.000Z'); // 14-day window from Oct 2
  assert.deepEqual(r.alerts.map(a => a.recipient.id).sort(), ['firm', 'lead']);
});

test('moving to another stage clears the mark so the new owner can be alerted', () => {
  const s = world();
  overdueSweep(s, '2026-10-06T00:00:00.000Z');
  Object.assign(s.tickets[0], {status: 'Notice prepared', contractor: 'Asphalt', history: [{at: '2026-10-06T00:00:00.000Z', action: 'Notice prepared', actor: 'x', note: ''}]});
  const r = overdueSweep(s, '2026-10-07T00:00:00.000Z');
  assert.equal(r.cleared, 1);
  assert.equal(s.tickets[0].overdue, undefined);
});

test('closed and on-hold tickets are ignored', () => {
  const s = world();
  s.tickets[0].status = 'On hold' as any;
  assert.equal(overdueSweep(s, '2026-10-20T00:00:00.000Z').overdue, 0);
});

test('one digest email per person, never to demo addresses', () => {
  const s = world();
  s.members.push({id: 'demo', name: 'Demo', email: 'x@example.invalid', role: 'Head Analyst', teams: ['North'], active: true} as any);
  const r = overdueSweep(s, '2026-10-06T00:00:00.000Z');
  const mails = overdueDigests(r.alerts, (k, a = []) => k.replace(/\{(\d+)\}/g, (_, i) => a[+i]), 'https://example.test');
  assert.deepEqual(mails.map(m => m.to).sort(), ['ana@city.rs', 'lead@city.rs']);
  assert.match(mails[0].text, /T1 · Main/);
});
