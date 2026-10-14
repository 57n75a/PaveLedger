import {test} from 'node:test';
import assert from 'node:assert/strict';
import {addObservation} from '../lib/observe.ts';
import {applyAction} from '../lib/actions.ts';
import {seed, normalizeState} from '../lib/domain.ts';
import {loadDemoPack} from '../lib/demo.ts';

const now = '2026-10-14T10:00:00.000Z';
const ticket = (o: Record<string, unknown> = {}) => ({id: 'T', title: 't', road: 'Main', lat: 0, lng: 0, accuracy: 5, severity: 'Low', status: 'Investigating', team: 'A', analyst: '', contractor: '', warranty: 'Needs review', source: 's', confidence: 0, created: '2026-10-01T00:00:00.000Z', updated: '2026-10-01T00:00:00.000Z', due: '2026-10-30T00:00:00.000Z', reopened: 0, observations: 1, note: '', history: [], ...o}) as any;
const state = () => ({members: [], notifications: [], events: [], tickets: []}) as any;

test('repeated reports raise the priority step by step', () => {
  const s = state(), t = ticket();
  addObservation(s, t, {now, actor: 'a', note: 'again'});
  assert.equal(t.severity, 'Low');
  const r = addObservation(s, t, {now, actor: 'a', note: 'third'});
  assert.equal(t.observations, 3);
  assert.equal(r.raised, true);
  assert.equal(t.severity, 'Standard');
  addObservation(s, t, {now, actor: 'a', note: '4'}); addObservation(s, t, {now, actor: 'a', note: '5'});
  assert.equal(t.severity, 'Urgent');
  assert.ok(t.due <= '2026-10-16T10:00:00.000Z');
});

test('a report marked urgent raises it at once', () => {
  const s = state(), t = ticket({severity: 'Standard'});
  addObservation(s, t, {now, actor: 'a', note: 'dangerous', urgent: true});
  assert.equal(t.severity, 'Urgent');
  assert.ok(t.history.some((h: any) => h.action === 'Priority raised'));
});

test('the observe action adds to an open ticket and refuses closed ones', () => {
  const s = normalizeState(seed('owner', 'owner@example.test'));
  loadDemoPack(s, 'serbia', s.members.filter(m => m.id === 'owner'), now, 'System');
  s.members.forEach(m => { if (m.id === 'owner') m.teams = [...s.teams]; });
  const owner = s.members.find(m => m.id === 'owner')!;
  const open = s.tickets.find(t => t.status === 'Investigating')!;
  const count = s.tickets.length, obs = open.observations;
  applyAction(s, owner, owner, {action: 'observe', id: open.id, note: 'Seen again during inspection'}, now, 'owner');
  assert.equal(s.tickets.length, count);
  assert.equal(open.observations, obs + 1);
  const shut = s.tickets.find(t => t.status === 'Verified closed')!;
  assert.throws(() => applyAction(s, owner, owner, {action: 'observe', id: shut.id, note: 'Seen again during inspection'}, now, 'owner'), /closed/);
});
