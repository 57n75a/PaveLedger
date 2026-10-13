import test from 'node:test';import assert from 'node:assert/strict';
import {checkRow,parseDate,autoMapColumns,contractKey,CONTRACT_SCHEMA} from '../lib/contract-schema.ts';
import {seed,normalizeState} from '../lib/domain.ts';
import {applyAction} from '../lib/actions.ts';
const ok={contractor:'Putevi Užice d.o.o.',road:'Kralja Petra I',start:'2026-03-01',end:'2028-03-01',poc:'Marko Petrović',email:'Marko@Putevi-Uzice.rs'};
test('dates: ISO, Serbian dotted, Excel serial and Date objects',()=>{
 assert.equal(parseDate('2026-03-01'),'2026-03-01');assert.equal(parseDate('1.3.2026.'),'2026-03-01');assert.equal(parseDate('01.03.2026'),'2026-03-01');
 assert.equal(parseDate(46082),'2026-03-01');assert.equal(parseDate(new Date(2026,2,1)),'2026-03-01');
 assert.equal(parseDate('03/01/2026'),null);assert.equal(parseDate('2026-02-30'),null);assert.equal(parseDate('31.02.2026'),null)});
test('a complete row is accepted and normalised',()=>{const r=checkRow({...ok,start:'01.03.2026',addressCountry:'Srbija',additionalRoads:'Vuka Karadžića; Dušanova'});assert.deepEqual(r.errors,[]);assert.equal(r.value!.start,'2026-03-01');assert.equal(r.value!.email,'marko@putevi-uzice.rs');assert.equal(r.value!.addressCountry,'SRB');assert.deepEqual(r.value!.additionalRoads,['Vuka Karadžića','Dušanova'])});
test('missing required fields are reported by name',()=>{const r=checkRow({contractor:'X'});assert.equal(r.value,null);for(const f of CONTRACT_SCHEMA.filter(f=>f.required&&f.key!=='contractor'))assert.ok(r.errors.includes(f.label+' is required.'),f.key)});
test('bad email, reversed dates, unknown country and half a map area are rejected',()=>{
 assert.ok(checkRow({...ok,email:'marko@'}).errors.some(e=>e.includes('valid email')));
 assert.ok(checkRow({...ok,start:'2028-01-01',end:'2026-01-01'}).errors.includes('Warranty ends before it begins.'));
 assert.ok(checkRow({...ok,addressCountry:'Narnia'}).errors.some(e=>e.includes('SRB, EU')));
 assert.ok(checkRow({...ok,scopeLat:'43.85'}).errors.includes('Map area needs latitude, longitude and radius together.'));
 assert.deepEqual(checkRow({...ok,scopeLat:'43,85',scopeLng:'19.84',scopeRadius:'500'}).errors,[]);
 assert.ok(checkRow({...ok,scopeRadius:'10',scopeLat:'1',scopeLng:'1'}).errors.some(e=>e.includes('out of range')))});
test('headers map automatically in English, Serbian and template keys',()=>{
 assert.deepEqual(autoMapColumns(CONTRACT_SCHEMA.map(f=>f.key)),Object.fromEntries(CONTRACT_SCHEMA.map(f=>[f.key,f.key])));
 const m=autoMapColumns(['Izvođač','Ulica','Početak garancije','Kraj garancije','Kontakt osoba','E-pošta','Telefon']);
 assert.equal(m.contractor,'Izvođač');assert.equal(m.road,'Ulica');assert.equal(m.start,'Početak garancije');assert.equal(m.end,'Kraj garancije');assert.equal(m.poc,'Kontakt osoba');assert.equal(m.email,'E-pošta');assert.equal(m.phone,'Telefon');
 const e=autoMapColumns(['Company','Street','Warranty start','Warranty end','Contact person','Contact email']);assert.equal(e.poc,'Contact person');assert.equal(e.email,'Contact email')});
test('duplicate key ignores case and accents',()=>assert.equal(contractKey({contractor:'PUTEVI UZICE D.O.O.',road:'kralja petra i',start:'2026-03-01',end:'2028-03-01'}),contractKey(ok)));
test('server import adds valid rows and skips invalid rows and duplicates',()=>{
 const s=normalizeState(seed('owner','owner@example.test'));const admin=s.members[0];const before=s.contracts.length;
 applyAction(s,admin,admin,{action:'bulkImportContracts',items:[ok,{...ok},{...ok,email:'nope'},{...ok,road:'Užička',start:'15.04.2026',end:'14.04.2029',scopeLat:43.85,scopeLng:19.84,scopeRadius:500}]},'2026-10-13T10:00:00Z','owner');
 assert.equal(s.contracts.length,before+2);const u=s.contracts.find(c=>c.road==='Užička')!;assert.equal(u.start,'2026-04-15');assert.equal(u.scopeRadius,500);
 assert.match(s.events[0].action,/Bulk imported 2 contract\(s\), skipped 1 invalid row\(s\), skipped 1 duplicate\(s\)/)});
test('a list sent as an array keeps its items',()=>assert.deepEqual(checkRow({...ok,additionalRoads:['Vuka Karadžića','Dušanova']}).value!.additionalRoads,['Vuka Karadžića','Dušanova']));
