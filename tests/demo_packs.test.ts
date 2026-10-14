import test from 'node:test';import assert from 'node:assert/strict';
import {DEMO_PACKS,checkPack,loadDemoPack} from '../lib/demo.ts';
import {seed,normalizeState,statuses,canSee} from '../lib/domain.ts';
import {applyAction} from '../lib/actions.ts';
import {ticketFlow} from '../lib/workflow.ts';
const now='2026-10-14T10:00:00.000Z';
const fresh=()=>{const s=normalizeState(seed('owner','owner@example.test'));s.members.push({id:'real-1',name:'Real Analyst',email:'real@x.test',role:'Analyst',teams:['Central roads'],contractor:'',active:true,demo:false});return s};
for(const id of ['serbia','canada'] as const){
 test(id+' pack follows the workflow and references only its own people, teams and contracts',()=>assert.deepEqual(checkPack(DEMO_PACKS[id]),[]));
 test(id+' pack loads with real accounts kept and demo people replaced',()=>{
  const s=fresh();loadDemoPack(s,id,s.members.filter(m=>!m.demo),now,'Owner');const ns=normalizeState(s);
  assert.ok(ns.members.some(m=>m.id==='owner'));assert.ok(ns.members.some(m=>m.id==='real-1'));
  assert.equal(ns.members.find(m=>m.id==='real-1')!.teams.length,0,'old team removed');
  assert.equal(ns.tickets.length,DEMO_PACKS[id].tickets.length);assert.equal(ns.contracts.length,DEMO_PACKS[id].contracts.length);
  const covered=new Set(ns.tickets.map(t=>t.status));for(const st of statuses)assert.ok(covered.has(st),'has a ticket in '+st);
  for(const t of ns.tickets){assert.ok(t.created<=t.updated&&t.updated<=now,t.id+' dates in order');const f=ticketFlow(t);assert.ok(f.current>=0)}
  assert.equal(ns.events[0].action,'Demo data loaded: '+DEMO_PACKS[id].name);
  const analyst=ns.members.find(m=>m.id==='demo-analyst')!;assert.ok(ns.tickets.filter(t=>canSee(t,analyst)).length>0,'analyst persona sees tickets')});
}
test('only a real administrator can load a demo pack',()=>{
 const s=normalizeState(seed('owner','owner@example.test'));const admin=s.members[0];const analyst=s.members.find(m=>m.id==='demo-analyst')!;
 assert.throws(()=>applyAction(s,analyst,analyst,{action:'loadDemo',pack:'serbia'},now,'owner'),/administrator/);
 assert.throws(()=>applyAction(s,analyst,admin,{action:'loadDemo',pack:'serbia'},now,'owner'),/administrator/);
 applyAction(s,admin,admin,{action:'loadDemo',pack:'canada'},now,'owner');assert.ok(s.tickets.every(t=>t.id.startsWith('CA-DEMO')));
 assert.throws(()=>applyAction(s,admin,admin,{action:'loadDemo',pack:'mars'},now,'owner'))});
