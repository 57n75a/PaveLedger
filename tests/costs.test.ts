import {test} from 'node:test';
import assert from 'node:assert/strict';
import {costSummary} from '../lib/costs.ts';
import {applyAction} from '../lib/actions.ts';
import {seed, normalizeState} from '../lib/domain.ts';
import {loadDemoPack} from '../lib/demo.ts';

const t = (id: string, contractor: string, cost?: object) => ({id, contractor, status: 'Verified closed', cost}) as any;

test('totals estimated, actual, recovered and net cost', () => {
  const s = costSummary([t('a', 'X', {estimate: 100, actual: 130, recovered: 130}), t('b', 'Y', {estimate: 200, actual: 150}), t('c', '', undefined)]);
  assert.equal(s.tickets, 2);
  assert.equal(s.actual, 280);
  assert.equal(s.recovered, 130);
  assert.equal(s.net, 150);
  assert.equal(s.avgActual, 140);
  assert.equal(s.overBudget, 1);
  assert.deepEqual(s.byContractor.map(c => c.contractor), ['X', 'Y']);
});

test('cost action validates and records history', () => {
  const now = '2026-10-14T10:00:00.000Z';
  const st = normalizeState(seed('owner', 'owner@example.test'));
  loadDemoPack(st, 'serbia', st.members.filter(m => m.id === 'owner'), now, 'System');
  const owner = st.members.find(m => m.id === 'owner')!;
  const tk = st.tickets[0];
  applyAction(st, owner, owner, {action: 'cost', id: tk.id, estimate: '30000', actual: 32000, recovered: ''}, now, 'owner');
  assert.deepEqual([tk.cost?.estimate, tk.cost?.actual, tk.cost?.recovered], [30000, 32000, undefined]);
  assert.ok(tk.history.some(h => h.action === 'Cost updated'));
  assert.throws(() => applyAction(st, owner, owner, {action: 'cost', id: tk.id, actual: 100, recovered: 200}, now, 'owner'), /recovered/);
});

test('demo packs include costs on repaired tickets', () => {
  const st = seed('o', 'o@x'); loadDemoPack(st, 'canada', [], '2026-10-14T10:00:00.000Z', 'S');
  const s = costSummary(st.tickets);
  assert.ok(s.tickets >= 3);
  assert.ok(s.recovered > 0);
});
