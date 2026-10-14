import {test} from 'node:test';
import assert from 'node:assert/strict';
import {seed, normalizeState} from '../lib/domain.ts';
import {loadDemoPack} from '../lib/demo.ts';
import {applyResidentReport, publicStatus, makePublicCode, normalizeCode} from '../lib/public-report.ts';

const now = '2026-10-14T10:00:00.000Z';
function world() {
  const s = seed('owner', 'owner@example.test');
  loadDemoPack(s, 'serbia', s.members.filter(m => m.id === 'owner'), now, 'System');
  return normalizeState(s);
}
const code = makePublicCode(n => new Uint8Array(n).map((_, i) => i * 7));

test('codes are readable and normalise from loose input', () => {
  assert.match(code, /^[2-9A-HJKMNP-Z]{5}-[2-9A-HJKMNP-Z]{5}$/);
  assert.equal(normalizeCode(code.toLowerCase().replace('-', ' ')), code);
});

test('a report far from open tickets creates a new Detected ticket', () => {
  const s = world(), before = s.tickets.length;
  const {ticket, merged} = applyResidentReport(s, {lat: 45.25, lng: 19.83, description: 'Deep hole near the bus stop', dangerous: false, email: 'a@b.rs'}, now, {ticketId: 'PL-2026-NEW', code});
  assert.equal(merged, false);
  assert.equal(s.tickets.length, before + 1);
  assert.equal(ticket.status, 'Detected');
  assert.equal(ticket.source, 'Resident report');
  assert.equal(ticket.severity, 'Standard');
  assert.equal(ticket.publicCode, code);
  assert.equal(ticket.reporterEmail, 'a@b.rs');
});

test('dangerous reports are urgent', () => {
  const s = world();
  const {ticket} = applyResidentReport(s, {lat: 45.25, lng: 19.83, description: 'Car tyres burst here', dangerous: true}, now, {ticketId: 'PL-2026-URG', code});
  assert.equal(ticket.severity, 'Urgent');
});

test('a report within 20 m of an open ticket is added to it, not duplicated', () => {
  const s = world();
  const open = s.tickets.find(t => !['Verified closed', 'Rejected', 'Duplicate'].includes(t.status))!;
  const before = s.tickets.length, obs = open.observations;
  const {ticket, merged} = applyResidentReport(s, {lat: open.lat + 0.00005, lng: open.lng, description: 'Still there', dangerous: true}, now, {ticketId: 'PL-2026-DUP', code});
  assert.equal(merged, true);
  assert.equal(ticket.id, open.id);
  assert.equal(s.tickets.length, before);
  assert.equal(ticket.observations, obs + 1);
  assert.equal(ticket.severity, 'Urgent');
  assert.ok(ticket.publicCode);
});

test('public status shows steps and dates but no internal notes', () => {
  const s = world();
  const {ticket} = applyResidentReport(s, {lat: 45.25, lng: 19.83, description: 'Private detail about my neighbour', dangerous: false, email: 'secret@example.rs'}, now, {ticketId: 'PL-2026-PUB', code});
  const p = publicStatus(s, ticket.publicCode!.toLowerCase())!;
  assert.equal(p.steps.length, 7);
  assert.equal(p.steps[0].state, 'current');
  assert.equal(p.outcome, 'in-progress');
  const text = JSON.stringify(p);
  assert.ok(!text.includes('neighbour'));
  assert.ok(!text.includes('secret@example.rs'));
  assert.ok(!text.includes(ticket.id));
});

test('unknown or malformed codes return nothing', () => {
  const s = world();
  assert.equal(publicStatus(s, 'ZZZZZ-ZZZZZ'), null);
  assert.equal(publicStatus(s, "'; drop"), null);
});
