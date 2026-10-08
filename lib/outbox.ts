import type {State,Ticket,Member,OutboxItem} from './domain.ts';
import type {MailMessage,MailResult} from './mail.ts';

// Contractor notice emails. A notice is queued when a case reaches "Notice prepared" (after a person confirmed
// the contract and scope) or when someone chooses to email it. Sending is at-most-once: an item is claimed and
// saved as "sending" before any email leaves, so a failed save can never cause a duplicate.
type Contract=State['contracts'][number];
export const MAX_OUTBOX=100;
const STALE_MS=30*60_000;
const EMAIL=/^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const oneLine=(x:string)=>x.replace(/[\r\n]+/g,' ').trim();

// Only information that is meant for the contractor. Internal notes and history are never included.
export function buildNotice(t:Ticket,c:Contract):{subject:string,text:string}{
 const where=`${t.lat}, ${t.lng} (estimated accuracy +/- ${t.accuracy} m)\nMap: https://www.google.com/maps?q=${t.lat},${t.lng}`;
 return {
  subject:oneLine(`PaveLedger repair review request: ${t.road} (${t.id})`).slice(0,200),
  text:[
   `Hello ${oneLine(c.poc||'')||'contract contact'},`,
   '',
   'PaveLedger repair review request',
   '',
   `Ticket: ${t.id}`,
   `Road: ${oneLine(t.road)}`,
   `Location: ${where}`,
   `Issue: ${oneLine(t.title)}`,
   `Priority: ${t.severity}`,
   `Contract: ${c.id}`,
   `Scope: ${oneLine(c.scope||'')||'See the contract'}`,
   `Observed: ${t.created}`,
   `Evidence: ${(t.evidence||[]).length} file(s) are held in PaveLedger.`,
   '',
   'Please review the reported defect and confirm responsibility, intended repair action and schedule under the applicable contract. This request does not determine liability. Urgent municipal safety action continues independently.',
   '',
   'Reply to this email to reach the person who prepared the notice.',
  ].join('\n'),
 };
}

function prune(s:State){
 const keep=[...(s.outbox||[])];
 for(const status of ['sent','failed'] as const){
  while(keep.length>MAX_OUTBOX){const i=keep.findLastIndex(x=>x.status===status);if(i<0)break;keep.splice(i,1)}
 }
 s.outbox=keep;
}

// Queue a notice to the contract contact. Returns null when nothing was queued.
export function queueNotice(s:State,t:Ticket,c:Contract,sender:Member,now:string):OutboxItem|null{
 const to=(c.email||'').trim();
 if(!EMAIL.test(to)){t.history.push({at:now,actor:'System',action:'Notice email not queued',note:'The contract has no valid contact email.',visibility:'internal'});return null}
 if((s.outbox||[]).some(i=>i.ticket===t.id&&(i.status==='queued'||i.status==='sending')))return null;
 const {subject,text}=buildNotice(t,c);
 const item:OutboxItem={id:crypto.randomUUID(),to,replyTo:EMAIL.test(sender.email)?sender.email:undefined,subject,text,ticket:t.id,contract:c.id,created:now,attempts:0,status:'queued'};
 s.outbox=[item,...(s.outbox||[])];
 prune(s);
 t.history.push({at:now,actor:sender.name,action:'Notice email queued',note:`For the contract contact at ${c.contractor}.`,visibility:'internal'});
 return item;
}

// Put failed items back in the queue (administrator action).
export function retryFailed(s:State):number{
 let n=0;
 for(const i of s.outbox||[])if(i.status==='failed'){i.status='queued';i.attempts=0;delete i.lastError;delete i.claimedAt;n++}
 return n;
}

// Items stuck in "sending" (the save after delivery failed) are never re-sent automatically.
function reconcile(s:State,now:string):boolean{
 let changed=false;
 for(const i of s.outbox||[])if(i.status==='sending'&&Date.parse(now)-Date.parse(i.claimedAt||i.created)>STALE_MS){
  i.status='failed';i.lastError='Delivery status unknown. Check with the contractor before retrying.';changed=true;
 }
 return changed;
}

export type OutboxIO={save:()=>Promise<boolean>,send:(m:MailMessage)=>Promise<MailResult>,appUrl?:string,max?:number};

// Claim queued items, save, send, then record the outcome. `save` must persist the workspace and report success.
export async function runOutbox(s:State,now:string,io:OutboxIO):Promise<{sent:number,failed:number}>{
 const stale=reconcile(s,now);
 const claimed=(s.outbox||[]).filter(i=>i.status==='queued').reverse().slice(0,io.max??5);
 if(!claimed.length){if(stale)await io.save();return {sent:0,failed:0}}
 for(const i of claimed){i.status='sending';i.claimedAt=now;i.attempts+=1}
 if(!await io.save())return {sent:0,failed:0};
 let sent=0,failed=0;
 for(const i of claimed){
  let r:MailResult;
  try{r=await io.send({to:i.to,subject:i.subject,text:i.text+(io.appUrl?`\n\nOpen PaveLedger: ${io.appUrl}`:''),replyTo:i.replyTo})}
  catch(e){r={ok:false,reason:'unavailable',detail:(e as Error).message}}
  const t=s.tickets.find(x=>x.id===i.ticket);
  if(r.ok){
   i.status='sent';i.sentAt=now;delete i.lastError;sent++;
   if(t){t.noticeEmailedAt=now;t.history.push({at:now,actor:'System',action:'Notice emailed',note:`Sent to ${i.to}.`,visibility:'internal'})}
   s.events.unshift({at:now,actor:'System',action:'Notice emailed '+i.ticket});
  }else if(r.reason==='not-configured'){
   i.status='queued';i.attempts-=1;
  }else{
   i.lastError=(r.reason+(r.detail?': '+r.detail.slice(0,120):''));
   if(r.reason==='rejected'||i.attempts>=3){
    i.status='failed';failed++;
    if(t)t.history.push({at:now,actor:'System',action:'Notice email failed',note:'Delivery failed. An administrator can retry it from User Profile.',visibility:'internal'});
   }else i.status='queued';
  }
 }
 await io.save();
 return {sent,failed};
}
