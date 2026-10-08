import test from 'node:test';import assert from 'node:assert/strict';
import {seed,normalizeState,type Member,type State} from '../lib/domain.ts';
import {syncMemberEmail} from '../lib/users.ts';
const now='2026-10-07T12:00:00.000Z',owner='d226cfb5-73e3-41f2-8a21-d7721b3a40de';
const fixture=()=>{const s:State=normalizeState(seed(owner,'owner@example.test'));const m:Member={id:'u-1',name:'Linked Person',email:'old@example.test',role:'Analyst',teams:['Central roads'],contractor:'',authUserId:crypto.randomUUID(),active:true};s.members.push(m);return {s,m}};

test('a changed sign-in email is copied to the membership and logged',()=>{const {s,m}=fixture();assert.equal(syncMemberEmail(s,m,'New@Example.test ',now),true);assert.equal(m.email,'new@example.test');assert.match(s.events[0].action,/Email updated for Linked Person/);assert.equal(/example\.test/.test(s.events[0].action),false)});
test('nothing changes when the emails already match, ignoring case and spaces',()=>{const {s,m}=fixture();const before=s.events.length;assert.equal(syncMemberEmail(s,m,'  OLD@example.test',now),false);assert.equal(m.email,'old@example.test');assert.equal(s.events.length,before)});
test('an email already used by another member is never copied',()=>{const {s,m}=fixture();assert.equal(syncMemberEmail(s,m,'owner@example.test',now),false);assert.equal(m.email,'old@example.test')});
test('an empty sign-in email is ignored',()=>{const {s,m}=fixture();assert.equal(syncMemberEmail(s,m,'   ',now),false);assert.equal(m.email,'old@example.test')});
