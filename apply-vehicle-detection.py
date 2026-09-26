import pathlib

def replace_once(path, old, new, label):
    p = pathlib.Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        print(f"SKIP ({count} matches, expected 1): {label} in {path}")
        return False
    p.write_text(text.replace(old, new, 1))
    print(f"OK: {label}")
    return True

# ---------- lib/domain.ts ----------

replace_once('lib/domain.ts',
    "export type Role = 'Admin'|'Team lead'|'Analyst'|'Reviewer'|'Contractor'|'Auditor';",
    "export type Role = 'Admin'|'Team lead'|'Analyst'|'Reviewer'|'Contractor'|'Auditor'|'Vehicle';",
    "Role type: add Vehicle")

replace_once('lib/domain.ts',
    "export type Member={id:string,name:string,email:string,role:Role,team:string,contractor:string;active?:boolean;authUserId?:string;demo?:boolean};",
    "export type Member={id:string,name:string,email:string,role:Role,team:string,contractor:string;vehicleTag?:string;active?:boolean;authUserId?:string;demo?:boolean};",
    "Member type: add vehicleTag")

replace_once('lib/domain.ts',
    "lane?:string;contractId?:string;duplicateOf?:string;",
    "lane?:string;contractId?:string;reportedBy?:string;duplicateOf?:string;",
    "Ticket type: add reportedBy")

replace_once('lib/domain.ts',
    "export const roles:Role[]=['Admin','Team lead','Analyst','Reviewer','Contractor','Auditor'];",
    "export const roles:Role[]=['Admin','Team lead','Analyst','Reviewer','Contractor','Auditor','Vehicle'];",
    "roles array: add Vehicle")

helpers = """
export function activeContractFor(s:State,road:string,dateISO:string){return s.contracts.find(c=>c.road===road&&c.start<=dateISO&&c.end>=dateISO);}
export function nearbyOpenTicket(s:State,road:string,lat:number,lng:number,radius=20){return s.tickets.find(t=>t.road===road&&!closed(t)&&distanceMeters({lat,lng},t)<=radius);}
export function leastLoadedAnalyst(s:State){const analysts=s.members.filter(m=>m.role==='Analyst'&&m.active!==false);if(!analysts.length)return undefined;const load=(id:string)=>s.tickets.filter(t=>t.analyst===id&&!closed(t)).length;return [...analysts].sort((a,b)=>load(a.id)-load(b.id))[0];}
"""
dp = pathlib.Path('lib/domain.ts')
domain_text = dp.read_text()
if 'export function activeContractFor' not in domain_text:
    dp.write_text(domain_text + helpers)
    print("OK: appended activeContractFor, nearbyOpenTicket, leastLoadedAnalyst helpers")
else:
    print("SKIP: helper functions already present in lib/domain.ts")

# ---------- lib/actions.ts ----------

replace_once('lib/actions.ts',
    "if(v.role==='Contractor'&&!s.contracts.some(x=>x.contractor===v.contractor))throw new AppError('Choose an existing contractor firm.');",
    "if(v.role==='Contractor'&&!s.contracts.some(x=>x.contractor===v.contractor))throw new AppError('Choose an existing contractor firm.');\n  if(v.role==='Vehicle'&&!v.vehicleTag.trim())throw new AppError('Enter a vehicle tag (e.g. Truck-07).');",
    "member action: validate vehicleTag")

replace_once('lib/actions.ts',
    "const clean={...v,team:['Team lead','Analyst','Reviewer','Admin'].includes(v.role)?v.team:'',contractor:v.role==='Contractor'?v.contractor:'',demo:false};",
    "const clean={...v,team:['Team lead','Analyst','Reviewer','Admin'].includes(v.role)?v.team:'',contractor:v.role==='Contractor'?v.contractor:'',vehicleTag:v.role==='Vehicle'?v.vehicleTag:'',demo:false};",
    "member action: include vehicleTag in clean object")

# ---------- app/workspace.tsx ----------

replace_once('app/workspace.tsx',
    "{role==='Contractor'&&<Pick label=\"Firm\" value={firm} onChange={setFirm} items={[{value:'none',label:'Choose contractor firm'},...Array.from(new Set(data.contracts.map(c=>c.contractor))).map(x=>({value:x,label:x}))]}/>}",
    "{role==='Contractor'&&<Pick label=\"Firm\" value={firm} onChange={setFirm} items={[{value:'none',label:'Choose contractor firm'},...Array.from(new Set(data.contracts.map(c=>c.contractor))).map(x=>({value:x,label:x}))]}/>}{role==='Vehicle'&&<label>Vehicle tag<input name=\"vehicleTag\" required defaultValue={initial?.vehicleTag||''} placeholder=\"e.g. Truck-07\"/></label>}",
    "MemberForm: add vehicle tag input field")

# ---------- new file: app/api/detect/route.ts ----------

route_path = pathlib.Path('app/api/detect/route.ts')
route_path.parent.mkdir(parents=True, exist_ok=True)

route_code = """import {randomUUID,createHash} from 'node:crypto';
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
"""

if route_path.exists():
    print(f"SKIP: {route_path} already exists — not overwriting. Delete it first if you want it regenerated.")
else:
    route_path.write_text(route_code)
    print(f"OK: created {route_path}")

print("\nDone. Now run:")
print("  git diff")
print("  npm run build")
print("If the build passes, commit and push.")
