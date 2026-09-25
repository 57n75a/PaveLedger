// Local contract checks against the built app and an in-memory Supabase HTTP double.
// This does not validate a real Supabase project, SQL permissions, or cloud deployment.
import http from 'node:http';
import {spawn} from 'node:child_process';
import assert from 'node:assert/strict';
import {seed,normalizeState} from '../lib/domain.ts';
console.log('Starting local integration service');
const owner='d226cfb5-73e3-41f2-8a21-d7721b3a40de', analyst='a226cfb5-73e3-41f2-8a21-d7721b3a40de', contractor='c226cfb5-73e3-41f2-8a21-d7721b3a40de';
let row={id:'integration',owner,revision:1,data:normalizeState(seed(owner,'owner@example.test'))};
for(const [id,uid] of [['demo-analyst',analyst],['demo-contractor',contractor]]){Object.assign(row.data.members.find(m=>m.id===id),{demo:false,authUserId:uid});}
const m=row.data.members.find(m=>m.id==='demo-analyst');
row.data.tickets[0].analyst=m.id;
row.data.tickets[0].history.push({at:new Date().toISOString(),actor:'staff',action:'Note added',note:'INTERNAL CANARY',visibility:'internal'});
row.data.tickets[0].status='Notice prepared';
const tokenUsers={owner,analyst,contractor,outsider:'f226cfb5-73e3-41f2-8a21-d7721b3a40de'};
const objects=new Map();
const mock=http.createServer(async(req,res)=>{let body='';for await(const b of req)body+=b;const url=new URL(req.url,'http://local');res.setHeader('content-type','application/json');const send=(status,obj)=>{res.statusCode=status;res.end(JSON.stringify(obj))};
 if(url.pathname==='/auth/v1/user'){const token=(req.headers.authorization||'').replace('Bearer ','');const id=tokenUsers[token];return id?send(200,{id,email:id===owner?'owner@example.test':token+'@example.test',email_confirmed_at:'2026-01-01T00:00:00Z',aud:'authenticated',role:'authenticated'}):send(401,{message:'invalid token'});}
 if(url.pathname==='/rest/v1/workspaces'){
  if(req.method==='GET')return send(200,[row]);
  if(req.method==='PATCH'){if(url.searchParams.get('revision')!==`eq.${row.revision}`)return send(200,[]);row={...row,...JSON.parse(body)};return send(200,[{id:row.id}]);}
 }
 if(url.pathname.startsWith('/storage/v1/object/sign/'))return send(200,{signedURL:'/object/sign/local?token=test-only'});
 if(url.pathname.startsWith('/storage/v1/object/')&&req.method==='POST'){objects.set(url.pathname,body);return send(200,{Key:url.pathname});}
 if(url.pathname.startsWith('/storage/v1/object/')&&req.method==='DELETE')return send(200,[]);
 send(404,{message:'Unhandled mock path '+url.pathname});
});
console.log('Binding local mock');
await new Promise(resolve=>mock.listen(0,'127.0.0.1',resolve));const supabasePort=mock.address().port;
console.log('Mock ready');
const port=4319,base=`http://127.0.0.1:${port}`;
console.log('Starting built Next server');
const app=spawn(process.execPath,['node_modules/next/dist/bin/next','start','-H','127.0.0.1','-p',String(port)],{env:{...process.env,NEXT_PUBLIC_SUPABASE_URL:`http://127.0.0.1:${supabasePort}`,SUPABASE_SECRET_KEY:'integration-test-secret-only',OWNER_EMAIL:'owner@example.test',WORKSPACE_ID:'integration'},stdio:['ignore','pipe','pipe']});
let appLog='';app.stdout.on('data',x=>appLog+=x);app.stderr.on('data',x=>appLog+=x);
setTimeout(()=>{console.error('Integration timeout',appLog);app.kill('SIGTERM');mock.closeAllConnections();mock.close();process.exit(1)},45000).unref();
const auth=token=>({'authorization':`Bearer ${token}`});let checks=0;
const check=(actual,expected,label)=>{assert.deepEqual(actual,expected,label);checks++;console.log('PASS '+label)};
async function get(token,path='/api/workspace'){return fetch(base+path,{headers:token?auth(token):{}})}
async function post(token,body,headers={}){return fetch(base+'/api/workspace',{method:'POST',headers:{...auth(token),'Content-Type':'application/json',...headers},body:JSON.stringify(body)})}
try{
 for(let n=0;n<100;n++){try{if((await fetch(base+'/api/health',{signal:AbortSignal.timeout(1000)})).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
 check((await fetch(base+'/')).status,200,'sign-in page loads');
 check((await fetch(base+'/concept')).status,200,'concept page loads');
 check((await get()).status,401,'missing bearer rejected');
 check((await get('bad')).status,401,'invalid auth rejected');
 check((await get('outsider')).status,403,'unbound identity rejected');
 const a=await get('owner');check(a.status,200,'administrator loads workspace');check(a.headers.get('cache-control'),'private, no-store','workspace never cached');
 const scoped=await (await get('analyst')).json();check(scoped.tickets.every(t=>t.analyst===m.id),true,'analyst receives assigned cases only');check(scoped.events.length,0,'analyst receives no global audit');
 const cp=await (await get('contractor')).json();check(JSON.stringify(cp).includes('INTERNAL CANARY'),false,'contractor cannot receive internal notes');check(cp.tickets.every(t=>t.contractor==='Northline Civil (demo)'),true,'contractor scope filtered');
 check((await post('owner',{action:'team',name:'New team',revision:0})).status,409,'stale revision rejected');
 check((await post('owner',{action:'team',name:'New team',revision:1},{origin:'https://untrusted.invalid'})).status,403,'foreign origin rejected');
 check((await post('analyst',{action:'team',name:'New team',revision:1})).status,403,'analyst cannot change teams');
 check((await post('owner',{action:'team',name:'New team',revision:1})).status,200,'accepted update persisted');check(row.revision,2,'revision incremented');
 const ticket=row.data.tickets[0];const f=new FormData();for(const [k,v] of Object.entries({ticket:ticket.id,revision:String(row.revision),authorized:'true',purpose:'detection',capturedAt:new Date(Date.now()-60000).toISOString(),lat:String(ticket.lat),lng:String(ticket.lng),accuracy:'3',lane:ticket.lane,quality:'clear'}))f.set(k,v);
 f.set('file',new Blob([Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jxP8AAAAASUVORK5CYII=','base64')],{type:'image/png'}),'field.png');
 const upload=await fetch(base+'/api/evidence',{method:'POST',headers:auth('owner'),body:f});check(upload.status,200,'evidence upload accepted');const evidence=await upload.json();check(objects.size,1,'binary sent to private storage adapter');
 check(row.data.tickets[0].evidence[0].visibility,'internal','evidence defaults internal');
 check((await get('contractor',`/api/evidence?ticket=${ticket.id}&id=${evidence.id}`)).status,403,'contractor cannot open internal evidence');
 check((await get('owner',`/api/evidence?ticket=${ticket.id}&id=${evidence.id}`)).status,200,'authorized evidence produces signed URL');
 check((await fetch(base+'/api/evidence',{method:'POST',headers:auth('owner'),body:f})).status,409,'stale evidence update rejected');
 console.log(`${checks} integration assertions passed. Supabase endpoints were simulated.`);
}catch(error){console.error(appLog);throw error;}finally{app.kill('SIGTERM');mock.closeAllConnections();await new Promise(r=>mock.close(r));}
