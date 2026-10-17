import test from 'node:test';import assert from 'node:assert/strict';
import {seed,normalizeState} from '../lib/domain.ts';
import {applyAction} from '../lib/actions.ts';
const now='2026-10-18T10:00:00.000Z',owner='d226cfb5-73e3-41f2-8a21-d7721b3a40de';
test('demo reset removes users added by the admin and keeps only the admin and owner',()=>{
 const s=normalizeState(seed(owner,'owner@example.test'));const admin=s.members[0];
 applyAction(s,admin,admin,{action:'member',name:'Added Person',email:'added@example.test',role:'Analyst',teams:[s.teams[0]],contractor:'',active:true,authUserId:crypto.randomUUID()},now,owner);
 assert.ok(s.members.some(x=>x.email==='added@example.test'));
 applyAction(s,admin,admin,{action:'loadDemo',pack:'canada'},now,owner);
 assert.equal(s.members.some(x=>x.email==='added@example.test'),false);
 assert.ok(s.members.some(x=>x.id===admin.id));
});
