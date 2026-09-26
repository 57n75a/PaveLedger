import {randomUUID,createHash} from 'node:crypto';
import {z} from 'zod';
import {context,failure} from '@/lib/context';
import {saveWorkspace,adminClient,workspaceId} from '@/lib/store';
import {closed,activeContractFor,nearbyOpenTicket,leastLoadedAnalyst,type Ticket,type Evidence} from '@/lib/domain';
import {AppError} from '@/lib/actions';
export const runtime='nodejs';export const dynamic='force-dynamic';
const bucket='paveledger-evidence';
const key=(ticket:string,id:string)=>`${workspaceId}/${ticket}/${id}`;

export async function POST(req:Request){try{
 const origin=req.headers.get('origin');if(origin&&origin!==new URL(req.url).origin)throw new AppError('Origin mismatch',403);
 if(Number(req.headers.get('content-length'))>3_300_000)throw new AppError('Use an image smaller than 3 MB.',413);
 const c=await context(req);
 if(c.member.role!=='Vehicle')throw new AppError('This endpoint is for registered vehicle accounts only.',403);
 const form=await req.formData();
 if(Number(form.get('revision'))!==c.row.revision)throw new AppError('Workspace changed; retry.',409);
 const v=z.object({road:z.string().trim().min(1).max(150),lat:z.coerce.number().min(-90).max(90),lng:z.coerce.number().min(-180).max(180),accuracy:z.coerce.number().positive().max(1000),lane:z.string().trim().min(1).max(100),capturedAt:z.string().datetime(),confidence:z.coerce.number().min(0).max(1)}).parse(Object.fromEntries(form));
 const file=form.get('file');if(!(file instanceof File)||file.size<12||file.size>3_000_000)throw new AppError('Choose a JPEG, PNG or WebP file up to 3 MB.');
 const bytes=Buffer.from(await file.arrayBuffer());let mime='';if(bytes[0]===255&&bytes[1]===216&&bytes[2]===255)mime='image/jpeg';else if(bytes.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])))mime='image/png';else if(bytes.subarray(0,4).toString()==='RIFF'&&bytes.subarray(8,12).toString()==='WEBP')mime='image/webp';if(!mime)throw new AppError('File contents are not a supported image.');
 const sha256=createHash('sha256').update(bytes).digest('hex');
 const now=new Date().toISOString();
 const state=c.state;
 const existing=nearbyOpenTicket(state,v.road,v.lat,v.lng,20);
 if(existing){
  const today=now.slice(0,10);
  const todaysCount=(existing.evidence||[]).filter(e=>e.uploadedAt.slice(0,10)===today&&e.purpose==='detection').length;
  if(todaysCount>=3||existing.evidence?.some(e=>e.sha256===sha256))return Response.json({status:'submitted'},{headers:{'Cache-Control':'private, no-store'}});
  const id=randomUUID();
  const evidence:Evidence={id,name:file.name.slice(0,150),mime,bytes:file.size,sha256,purpose:'detection',capturedAt:v.capturedAt,uploadedAt:now,uploadedBy:c.actual.id,lat:v.lat,lng:v.lng,accuracy:v.accuracy,lane:v.lane,quality:'clear',visibility:'internal'};
  const {error}=await adminClient().storage.from(bucket).upload(key(existing.id,id),bytes,{contentType:mime,upsert:false});
  if(error)throw new AppError('Upload failed.',503);
  try{
   existing.evidence??=[];existing.evidence.push(evidence);existing.observations++;existing.updated=now;
   existing.history.push({at:now,actor:c.actual.name,action:'Evidence uploaded',note:`Automated detection ${id}; SHA-256 ${sha256}`,visibility:'internal'});
   state.events.unshift({at:now,actor:c.actual.name,action:'Evidence uploaded '+existing.id+' '+id});
   if(!await saveWorkspace(state,c.row.revision))throw new AppError('Workspace changed; retry.',409);
  }catch(err){await adminClient().storage.from(bucket).remove([key(existing.id,id)]);throw err;}
  return Response.json({status:'submitted'},{headers:{'Cache-Control':'private, no-store'}});
 }
 if(state.tickets.length>=500)throw new AppError('Pilot workspace limit of 500 cases reached.');
 const id=`PL-${now.slice(0,4)}-${randomUUID().slice(0,8).toUpperCase()}`;
 const contract=activeContractFor(state,v.road,now.slice(0,10));
 const analyst=leastLoadedAnalyst(state);
 const ticket:Ticket={id,title:'Automated pothole detection',road:v.road,lat:v.lat,lng:v.lng,accuracy:v.accuracy,lane:v.lane,severity:'Standard',status:analyst?'Analyst assigned':'Detected',team:analyst?.team||state.teams[0]||'',analyst:analyst?.id||'',contractor:contract?.contractor||'',warranty:contract?'Candidate match':'Needs review',source:c.actual.vehicleTag||'Automated dashcam',confidence:v.confidence,created:now,updated:now,due:new Date(Date.parse(now)+86400000).toISOString(),reopened:0,observations:1,note:'Automated detection. Location, confidence and contractor are unconfirmed pending analyst review.',reportedBy:c.actual.id,evidence:[],history:[{at:now,actor:c.actual.name,action:'Detected',note:'Automated dashcam detection.',visibility:'internal'}]};
 const evId=randomUUID();
 const evidence:Evidence={id:evId,name:file.name.slice(0,150),mime,bytes:file.size,sha256,purpose:'detection',capturedAt:v.capturedAt,uploadedAt:now,uploadedBy:c.actual.id,lat:v.lat,lng:v.lng,accuracy:v.accuracy,lane:v.lane,quality:'clear',visibility:'internal'};
 const {error}=await adminClient().storage.from(bucket).upload(key(id,evId),bytes,{contentType:mime,upsert:false});
 if(error)throw new AppError('Upload failed.',503);
 try{
  ticket.evidence=[evidence];
  state.tickets.unshift(ticket);
  state.events.unshift({at:now,actor:c.actual.name,action:'Created '+id});
  if(analyst)state.notifications.unshift({id:randomUUID(),recipient:analyst.id,ticket:id,text:`Assigned to you: ${ticket.road}`,at:now});
  if(!await saveWorkspace(state,c.row.revision))throw new AppError('Workspace changed; retry.',409);
 }catch(err){await adminClient().storage.from(bucket).remove([key(id,evId)]);throw err;}
 return Response.json({status:'submitted'},{headers:{'Cache-Control':'private, no-store'}});
}catch(e){return failure(e instanceof z.ZodError?new AppError('Check detection metadata.'):e)}}
