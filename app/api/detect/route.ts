import {randomUUID,createHash} from 'node:crypto';
import {z} from 'zod';
import {context,failure} from '@/lib/context';
import {saveWorkspace,adminClient,workspaceId} from '@/lib/store';
import {contractCovers,openTicketsNear,leastLoadedAnalyst,wantsNotification,isActive,type Ticket,type Evidence,type State} from '@/lib/domain';
import {AppError} from '@/lib/actions';
import {reverseStreet} from '@/lib/geo';
export const runtime='nodejs';export const dynamic='force-dynamic';

const bucket='paveledger-evidence';
const key=(ticket:string,id:string)=>`${workspaceId}/${ticket}/${id}`;
const done=()=>Response.json({status:'submitted'},{headers:{'Cache-Control':'private, no-store'}});
const SAME_DEFECT_RADIUS_M=20;   // detections inside this radius belong to the existing open ticket
const CLEAR_MIN_HOURS=12;        // a clear pass counts only this long after the ticket was created
const AUTO_CLOSE_DAYS=7;
const DAY_MS=86_400_000;

function notifyTeam(s:State,t:Ticket,text:string,now:string){
 const recipients=new Set<string>();
 for(const m of s.members){
  if(!isActive(m))continue;
  if(m.id===t.analyst||((m.teams||[]).includes(t.team)&&['Head Analyst','Analyst'].includes(m.role)))recipients.add(m.id);
 }
 for(const id of recipients){
  const m=s.members.find(x=>x.id===id);
  if(m&&wantsNotification(m,'statusChange'))s.notifications.unshift({id:randomUUID(),recipient:id,ticket:t.id,text,at:now});
 }
}

export async function POST(req:Request){try{
 const origin=req.headers.get('origin');if(origin&&origin!==new URL(req.url).origin)throw new AppError('Origin mismatch',403);
 if(Number(req.headers.get('content-length'))>3_300_000)throw new AppError('Use an image smaller than 3 MB.',413);
 const c=await context(req);
 if(c.member.role!=='Vehicle')throw new AppError('This endpoint is for registered vehicle accounts only.',403);
 const form=await req.formData();
 const v=z.object({
  lat:z.coerce.number().min(-90).max(90),
  lng:z.coerce.number().min(-180).max(180),
  accuracy:z.coerce.number().positive().max(1000),
  capturedAt:z.string().datetime(),
  outcome:z.enum(['detected','clear']).default('detected'),
  road:z.string().trim().max(150).optional(),
  lane:z.string().trim().max(100).optional(),
  confidence:z.coerce.number().min(0).max(1).optional(),
 }).parse(Object.fromEntries(form));
 if(Date.parse(v.capturedAt)>Date.now()+5*60_000)throw new AppError('Capture time is in the future.');
 if(v.outcome==='detected'&&v.confidence===undefined)throw new AppError('confidence is required for detections.');

 const file=form.get('file');
 if(!(file instanceof File)||file.size<12||file.size>3_000_000)throw new AppError('Choose a JPEG, PNG or WebP file up to 3 MB.');
 const upload:File=file;
 const bytes=Buffer.from(await upload.arrayBuffer());
 let mime='';
 if(bytes[0]===255&&bytes[1]===216&&bytes[2]===255)mime='image/jpeg';
 else if(bytes.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])))mime='image/png';
 else if(bytes.subarray(0,4).toString()==='RIFF'&&bytes.subarray(8,12).toString()==='WEBP')mime='image/webp';
 if(!mime)throw new AppError('File contents are not a supported image.');
 const sha256=createHash('sha256').update(bytes).digest('hex');

 const now=new Date().toISOString(),state=c.state,lane=v.lane||'Lane 1';
 const nearby=openTicketsNear(state,v.lat,v.lng,SAME_DEFECT_RADIUS_M);

 const makeEvidence=(purpose:Evidence['purpose'],quality:Evidence['quality']):Evidence=>({id:randomUUID(),name:upload.name.slice(0,150),mime,bytes:upload.size,sha256,purpose,capturedAt:v.capturedAt,uploadedAt:now,uploadedBy:c.actual.id,lat:v.lat,lng:v.lng,accuracy:v.accuracy,lane,quality,visibility:'internal'});
 const commit=async(t:Ticket,e:Evidence,apply:()=>void)=>{
  const {error}=await adminClient().storage.from(bucket).upload(key(t.id,e.id),bytes,{contentType:mime,upsert:false});
  if(error)throw new AppError('Upload failed. Check the private evidence bucket setup.',503);
  try{
   t.evidence??=[];t.evidence.push(e);
   apply();
   if(!await saveWorkspace(state,c.row.revision))throw new AppError('Workspace changed while uploading; retry.',409);
  }catch(err){await adminClient().storage.from(bucket).remove([key(t.id,e.id)]);throw err}
 };

 // 1) The original vehicle drives the location again and finds the road clear: start pending closure.
 if(v.outcome==='clear'){
  const t=nearby.find(x=>x.reportedBy===c.actual.id);
  if(!t||t.autoCloseAt||(t.evidence||[]).length>=40||(t.evidence||[]).some(x=>x.sha256===sha256))return done();
  if((Date.parse(v.capturedAt)-Date.parse(t.created))/3_600_000<CLEAR_MIN_HOURS)return done();
  const due=new Date(Date.now()+AUTO_CLOSE_DAYS*DAY_MS).toISOString();
  const e=makeEvidence('verification','clear');
  await commit(t,e,()=>{
   t.pendingClosureAt=now;t.autoCloseAt=due;t.pendingClosureEvidence=e.id;t.updated=now;
   t.history.push({at:now,actor:c.actual.name,action:'Pending closure',note:`Vehicle re-check at the original location found the road clear (evidence ${e.id}). Auto-closes and archives on ${due.slice(0,10)} unless the team reopens or cancels it.`,visibility:'internal'});
   state.events.unshift({at:now,actor:c.actual.name,action:'Pending closure '+t.id});
   notifyTeam(state,t,`Pending closure: ${t.road} appears repaired. Auto-closes on ${due.slice(0,10)}.`,now);
  });
  return done();
 }

 // 2) A detection inside an open ticket's radius: add the photo (max 3 per day) instead of a new ticket.
 const existing=nearby[0];
 if(existing){
  const today=now.slice(0,10);
  const todays=(existing.evidence||[]).filter(x=>x.uploadedAt.slice(0,10)===today&&x.purpose==='detection').length;
  if(todays>=3||(existing.evidence||[]).length>=40||(existing.evidence||[]).some(x=>x.sha256===sha256))return done();
  const e=makeEvidence('detection','clear');
  await commit(existing,e,()=>{
   existing.observations++;existing.updated=now;
   existing.history.push({at:now,actor:c.actual.name,action:'Evidence uploaded',note:`Automated detection ${e.id}; SHA-256 ${sha256}`,visibility:'internal'});
   state.events.unshift({at:now,actor:c.actual.name,action:'Evidence uploaded '+existing.id+' '+e.id});
   if(existing.autoCloseAt){
    delete existing.pendingClosureAt;delete existing.autoCloseAt;delete existing.pendingClosureEvidence;
    existing.history.push({at:now,actor:c.actual.name,action:'Pending closure cancelled',note:'A new detection at this location cancelled the pending closure.',visibility:'internal'});
    notifyTeam(state,existing,`Pending closure cancelled: ${existing.road} was detected again.`,now);
   }
  });
  return done();
 }

 // 3) A new defect: resolve the street from the GPS fix, tag any covering contract, assign a team.
 if(state.tickets.length>=500)throw new AppError('Pilot workspace limit of 500 cases reached.');
 const street=await reverseStreet(v.lat,v.lng);
 const road=street||(v.road||'').trim()||`Unnamed road (${v.lat.toFixed(5)}, ${v.lng.toFixed(5)})`;
 const day=now.slice(0,10);
 const contract=state.contracts.find(k=>k.start<=day&&k.end>=day&&contractCovers(k,{road,lat:v.lat,lng:v.lng}));
 const analyst=leastLoadedAnalyst(state);
 const id=`PL-${now.slice(0,4)}-${randomUUID().slice(0,8).toUpperCase()}`;
 const e=makeEvidence('detection','clear');
 const ticket:Ticket={id,title:'Automated pothole detection',road,lat:v.lat,lng:v.lng,accuracy:v.accuracy,lane,severity:'Standard',status:analyst?'Analyst assigned':'Detected',team:analyst?.teams?.[0]||state.teams[0]||'',analyst:analyst?.id||'',contractor:contract?.contractor||'',warranty:contract?'Candidate match':'Needs review',source:c.actual.vehicleTag||'Automated dashcam',confidence:v.confidence??0,created:now,updated:now,due:new Date(Date.now()+DAY_MS).toISOString(),reopened:0,observations:1,note:`Automated detection. Street "${road}" was resolved from the vehicle GPS fix (GPS accuracy +/- ${v.accuracy} m; the street is the nearest mapped road). Location, confidence and contractor are unconfirmed pending analyst review.`,reportedBy:c.actual.id,evidence:[],history:[{at:now,actor:c.actual.name,action:'Detected',note:'Automated dashcam detection.',visibility:'internal'}]};
 await commit(ticket,e,()=>{
  state.tickets.unshift(ticket);
  state.events.unshift({at:now,actor:c.actual.name,action:'Created '+id});
  if(analyst&&wantsNotification(analyst,'assignment'))state.notifications.unshift({id:randomUUID(),recipient:analyst.id,ticket:id,text:`Assigned to you: ${road}`,at:now});
 });
 return done();
}catch(err){return failure(err instanceof z.ZodError?new AppError('Check detection metadata (lat, lng, accuracy, capturedAt, outcome).'):err)}}
