import {adminClient,saveWorkspace,workspaceId} from '@/lib/store';
import {sendMail,mailReady} from '@/lib/mail';
import {runOutbox} from '@/lib/outbox';
import {autoCloseDue,normalizeState,type State} from '@/lib/domain';
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
  if(closed>0){
   state.events.unshift({at:now,actor:'System',action:'Auto-closed and archived '+closed+' ticket(s) after 7 days pending closure'});
   if(!await saveWorkspace(state,row.revision))return Response.json({error:'Workspace changed; the next run will retry'},{status:409});
  }
  if(mailReady()&&(state.outbox||[]).some(i=>i.status==='queued'||i.status==='sending')){let rev=closed>0?row.revision+1:row.revision;try{await runOutbox(state,now,{max:5,send:m=>sendMail(m),save:async()=>{const ok=await saveWorkspace(state,rev);if(ok)rev+=1;return ok}})}catch(e){console.error('Notice delivery failed',e)}}
  return Response.json({closed});
 }catch{return Response.json({error:'Sweep failed'},{status:503})}
}
