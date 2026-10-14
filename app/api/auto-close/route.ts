import {adminClient,saveWorkspace,workspaceId} from '@/lib/store';
import {sendMail,mailReady} from '@/lib/mail';
import {runOutbox} from '@/lib/outbox';
import {autoCloseDue,normalizeState,type State} from '@/lib/domain';
import {overdueSweep,overdueDigests} from '@/lib/overdue';
import {serverTx} from '@/lib/server-i18n';
export const runtime='nodejs';export const dynamic='force-dynamic';

export async function GET(req:Request){
 const secret=process.env.CRON_SECRET;
 if(!secret||req.headers.get('authorization')!=='Bearer '+secret)return Response.json({error:'Unauthorized'},{status:401});
 try{
  const {data:row,error}=await adminClient().from('workspaces').select('id,revision,data').eq('id',workspaceId).maybeSingle();
  if(error)return Response.json({error:'Workspace unavailable'},{status:503});
  if(!row)return Response.json({closed:0,note:'No workspace yet'});
  const state=normalizeState(row.data as State);
  const now=new Date().toISOString();
  const closed=autoCloseDue(state,now);
  if(closed>0)state.events.unshift({at:now,actor:'System',action:'Auto-closed and archived '+closed+' ticket(s) after 7 days pending closure'});
  // Overdue alerts and escalation (once per stage, see lib/overdue.ts).
  const sweep=overdueSweep(state,now);
  const changed=closed>0||sweep.alerts.length>0||sweep.cleared>0||sweep.escalated>0;
  if(changed&&!await saveWorkspace(state,row.revision))return Response.json({error:'Workspace changed; the next run will retry'},{status:409});
  let mailed=0;
  if(mailReady()&&sweep.alerts.length){for(const m of overdueDigests(sweep.alerts,serverTx,new URL(req.url).origin)){const r=await sendMail(m);if(r.ok)mailed++;else console.error('Overdue email failed',r.reason)}}
  if(mailReady()&&(state.outbox||[]).some(i=>i.status==='queued'||i.status==='sending')){let rev=changed?row.revision+1:row.revision;try{await runOutbox(state,now,{max:5,send:m=>sendMail(m),save:async()=>{const ok=await saveWorkspace(state,rev);if(ok)rev+=1;return ok}})}catch(e){console.error('Notice delivery failed',e)}}
  return Response.json({closed,overdue:sweep.overdue,alerts:sweep.alerts.length,escalated:sweep.escalated,mailed});
 }catch{return Response.json({error:'Sweep failed'},{status:503})}
}
