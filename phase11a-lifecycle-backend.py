import pathlib, re, json
from datetime import date

VERSION = "2.3.0"
TODAY = date.today().isoformat()

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

def write_file(path, code, label):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    existed = p.exists()
    p.write_text(code, encoding='utf-8')
    print(f"OK: {'rewrote' if existed else 'created'} {path} ({label})")

# ============================================================
# lib/domain.ts
# ============================================================
replace_once('lib/domain.ts',
    "archived?:boolean;archiveRequested?:boolean;duplicateOf?:string;",
    "archived?:boolean;archiveRequested?:boolean;pendingClosureAt?:string;autoCloseAt?:string;pendingClosureEvidence?:string;duplicateOf?:string;",
    "domain.ts: Ticket gets pending-closure fields")

domain_helpers = r"""
const ROAD_ABBR:Record<string,string>={st:'street',ave:'avenue',av:'avenue',rd:'road',blvd:'boulevard',dr:'drive',hwy:'highway',ln:'lane',ct:'court',pkwy:'parkway',cres:'crescent',e:'east',w:'west',n:'north',s:'south',ne:'northeast',nw:'northwest',se:'southeast',sw:'southwest'};
export function normRoad(r:string){return r.toLowerCase().replace(/[.,]/g,' ').split(/\s+/).filter(Boolean).map(w=>ROAD_ABBR[w]||w).join(' ')}
export function contractCovers(c:{road:string,scopeLat?:number|null,scopeLng?:number|null,scopeRadius?:number|null},t:{road:string,lat:number,lng:number}){if(typeof c.scopeLat==='number'&&typeof c.scopeLng==='number'&&typeof c.scopeRadius==='number')return distanceMeters({lat:c.scopeLat,lng:c.scopeLng},t)<=c.scopeRadius;return normRoad(c.road)===normRoad(t.road)}
export function openTicketsNear(s:State,lat:number,lng:number,radius=20){return s.tickets.filter(t=>!closed(t)&&distanceMeters({lat,lng},t)<=radius).sort((a,b)=>distanceMeters({lat,lng},a)-distanceMeters({lat,lng},b))}
export function autoCloseDue(s:State,now:string):number{let n=0;for(const t of s.tickets){if(!t.autoCloseAt||closed(t)||t.autoCloseAt>now)continue;const ev=(t.evidence||[]).find(e=>e.id===t.pendingClosureEvidence);t.status='Verified closed';t.closedAt=now;t.closedBy='system';t.archived=true;t.archiveRequested=false;t.verification='Auto-closed by the system after the 7-day pending-closure window. Clear repeat pass '+(t.pendingClosureEvidence||'')+(ev?' captured '+ev.capturedAt:'')+'.';t.updated=now;t.history.push({at:now,actor:'System',action:'Verified closed',note:'Auto-closed and archived after 7 days in pending closure with no team objection.',visibility:'shared'});delete t.autoCloseAt;delete t.pendingClosureAt;delete t.pendingClosureEvidence;n++}return n}
"""
dp = pathlib.Path('lib/domain.ts')
dtext = dp.read_text()
if 'export function contractCovers' in dtext:
    print("SKIP: domain.ts helpers already present")
else:
    dp.write_text(dtext + domain_helpers)
    print("OK: domain.ts: added normRoad, contractCovers, openTicketsNear, autoCloseDue")

# ============================================================
# lib/actions.ts
# ============================================================
A = 'lib/actions.ts'
replace_once(A,
    "wantsNotification,type State,type Member,type Ticket,type Status} from './domain.ts';",
    "wantsNotification,contractCovers,type State,type Member,type Ticket,type Status} from './domain.ts';",
    "actions.ts: import contractCovers")
replace_once(A,
    "contract.road!==t.road||contract.start>observed||contract.end<observed||body.scopeConfirmed!==true",
    "!contractCovers(contract,t)||contract.start>observed||contract.end<observed||body.scopeConfirmed!==true",
    "actions.ts: Notice prepared uses contract coverage (scope area or road name)")
replace_once(A,
    "!contract||contract.road!==t.road||contract.start>observed||contract.end<observed)throw new AppError('Choose a contract covering this road and observation date.')",
    "!contract||!contractCovers(contract,t)||contract.start>observed||contract.end<observed)throw new AppError('Choose a contract covering this ticket location and observation date.')",
    "actions.ts: assignContractor uses contract coverage")
replace_once(A,
    "if(lt&&lt.road===existing.road){",
    "if(lt&&contractCovers(existing,lt)){",
    "actions.ts: contract incident linking uses coverage")
replace_once(A,
    "t.status=next as Status;event=t.status;",
    "t.status=next as Status;event=t.status;delete t.pendingClosureAt;delete t.autoCloseAt;delete t.pendingClosureEvidence;",
    "actions.ts: any manual stage change cancels pending closure")
replace_once(A,
    "event='Contractor assigned: '+contract.contractor;}",
    "event='Contractor assigned: '+contract.contractor;}else if(action==='cancelPendingClosure'){requireRole(['Admin','Team lead','Head Analyst','Analyst','Reviewer']);if(!t.autoCloseAt)throw new AppError('This ticket is not pending closure.');delete t.pendingClosureAt;delete t.autoCloseAt;delete t.pendingClosureEvidence;event='Pending closure cancelled';}",
    "actions.ts: add cancelPendingClosure action")

# ============================================================
# lib/geo.ts (new): street lookup and address search via OpenStreetMap Nominatim
# ============================================================
geo_code = r"""import 'server-only';

const UA='PaveLedger/2 (paveledger@gmail.com)';
const EU='at,be,bg,hr,cy,cz,dk,ee,fi,fr,de,gr,hu,ie,it,lv,lt,lu,mt,nl,pl,pt,ro,sk,si,es,se';
export const COUNTRY_CODES:Record<string,string>={USA:'us',CAN:'ca',SRB:'rs',EU:EU,Europe:EU};

async function nominatim(path:string,params:URLSearchParams,timeoutMs:number){
 const ctl=new AbortController();
 const timer=setTimeout(()=>ctl.abort(),timeoutMs);
 try{return await fetch('https://nominatim.openstreetmap.org/'+path+'?'+params.toString(),{headers:{'User-Agent':UA,'Accept-Language':'en'},cache:'no-store',signal:ctl.signal})}
 finally{clearTimeout(timer)}
}

// Nearest mapped street for a GPS fix. Returns null if the lookup fails.
export async function reverseStreet(lat:number,lng:number):Promise<string|null>{
 try{
  const p=new URLSearchParams({lat:String(lat),lon:String(lng),format:'jsonv2',zoom:'17',addressdetails:'1'});
  const r=await nominatim('reverse',p,4000);
  if(!r.ok)return null;
  const d:any=await r.json();
  const road=d?.address?.road||d?.address?.pedestrian||d?.address?.residential||d?.name;
  return road?String(road).slice(0,150):null;
 }catch{return null}
}

// Address or street to coordinates. Returns null when nothing matches; throws when the service is unavailable.
export async function forwardGeocode(q:string,opts:{country?:string,nearLat?:number,nearLng?:number}={}):Promise<{lat:number,lng:number,label:string}|null>{
 const p=new URLSearchParams({q,format:'jsonv2',limit:'1'});
 const cc=opts.country?COUNTRY_CODES[opts.country]:undefined;
 if(cc)p.set('countrycodes',cc);
 if(typeof opts.nearLat==='number'&&typeof opts.nearLng==='number'){
  const d=0.3;
  p.set('viewbox',[opts.nearLng-d,opts.nearLat+d,opts.nearLng+d,opts.nearLat-d].join(','));
  p.set('bounded','0');
 }
 const r=await nominatim('search',p,6000);
 if(!r.ok)throw new Error('unavailable');
 const rows:any[]=await r.json();
 if(!rows.length)return null;
 const lat=Number(rows[0].lat),lng=Number(rows[0].lon);
 if(!Number.isFinite(lat)||!Number.isFinite(lng))return null;
 return {lat,lng,label:String(rows[0].display_name||'')};
}
"""
write_file('lib/geo.ts', geo_code, "OpenStreetMap lookups")

# ============================================================
# app/api/geocode/route.ts (rewrite): Admin, Team lead, Analyst; optional country; area bias
# ============================================================
geocode_route = r"""import {context,failure} from '@/lib/context';
import {AppError} from '@/lib/actions';
import {forwardGeocode} from '@/lib/geo';
export const runtime='nodejs';export const dynamic='force-dynamic';

export async function GET(req:Request){try{
 const c=await context(req);
 if(!['Admin','Team lead','Analyst'].includes(c.member.role))throw new AppError('Not permitted to look up addresses.',403);
 const url=new URL(req.url);
 const q=(url.searchParams.get('q')||'').trim();
 if(q.length<3||q.length>300)throw new AppError('Enter a fuller address.');
 const country=url.searchParams.get('country')||undefined;
 const rawLat=url.searchParams.get('nearLat'),rawLng=url.searchParams.get('nearLng');
 const nl=Number(rawLat),ng=Number(rawLng);
 const hasNear=rawLat!==null&&rawLng!==null&&Number.isFinite(nl)&&Number.isFinite(ng);
 let hit;
 try{hit=await forwardGeocode(q,{country,nearLat:hasNear?nl:undefined,nearLng:hasNear?ng:undefined})}
 catch{throw new AppError('Address lookup is unavailable right now. You can enter coordinates or click the map instead.',503)}
 if(!hit)throw new AppError('No match found for that address. Try adding the city, or enter coordinates manually.',404);
 return Response.json(hit,{headers:{'Cache-Control':'private, no-store'}});
}catch(e){return failure(e)}}
"""
write_file('app/api/geocode/route.ts', geocode_route, "address lookup")

# ============================================================
# app/api/evidence-urls/route.ts (new): signed URLs for all of a ticket's images in one call
# ============================================================
urls_route = r"""import {context,failure} from '@/lib/context';
import {adminClient,workspaceId} from '@/lib/store';
import {canSee} from '@/lib/domain';
import {AppError} from '@/lib/actions';
export const runtime='nodejs';export const dynamic='force-dynamic';
const bucket='paveledger-evidence';

export async function GET(req:Request){try{
 const c=await context(req);
 const url=new URL(req.url);
 const t=c.state.tickets.find(x=>x.id===url.searchParams.get('ticket'));
 if(!t||!canSee(t,c.member))throw new AppError('Case unavailable.',403);
 const list=(t.evidence||[]).filter(e=>!(c.member.role==='Contractor'&&e.visibility!=='shared'));
 if(!list.length)return Response.json({urls:{}},{headers:{'Cache-Control':'private, no-store'}});
 const byPath:Record<string,string>={};
 for(const e of list)byPath[`${workspaceId}/${t.id}/${e.id}`]=e.id;
 const {data,error}=await adminClient().storage.from(bucket).createSignedUrls(Object.keys(byPath),300);
 if(error||!data)throw new AppError('Evidence could not be retrieved.',503);
 const urls:Record<string,string>={};
 for(const row of data){if(row.path&&row.signedUrl&&byPath[row.path])urls[byPath[row.path]]=row.signedUrl}
 return Response.json({urls},{headers:{'Cache-Control':'private, no-store'}});
}catch(e){return failure(e)}}
"""
write_file('app/api/evidence-urls/route.ts', urls_route, "thumbnail URLs")

# ============================================================
# app/api/auto-close/route.ts (new): daily sweep, protected by CRON_SECRET
# ============================================================
cron_route = r"""import {adminClient,saveWorkspace,workspaceId} from '@/lib/store';
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
  return Response.json({closed});
 }catch{return Response.json({error:'Sweep failed'},{status:503})}
}
"""
write_file('app/api/auto-close/route.ts', cron_route, "auto-close sweep")

# vercel.json: register the daily cron
vp = pathlib.Path('vercel.json')
cron_entry = {"path": "/api/auto-close", "schedule": "0 9 * * *"}
if vp.exists():
    try:
        cfg = json.loads(vp.read_text())
    except Exception:
        cfg = None
        print("SKIP: vercel.json is not valid JSON; add the cron manually")
    if cfg is not None:
        crons = cfg.setdefault('crons', [])
        if any(cr.get('path') == '/api/auto-close' for cr in crons):
            print("SKIP: vercel.json already has the auto-close cron")
        else:
            crons.append(cron_entry)
            vp.write_text(json.dumps(cfg, indent=2) + "\n")
            print("OK: vercel.json: added daily auto-close cron (09:00 UTC)")
else:
    vp.write_text(json.dumps({"crons": [cron_entry]}, indent=2) + "\n")
    print("OK: created vercel.json with the daily auto-close cron")

# ============================================================
# app/api/detect/route.ts (rewrite): detections, clear passes, street lookup
# ============================================================
detect_route = r"""import {randomUUID,createHash} from 'node:crypto';
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
  if(m.id===t.analyst||((m.teams||[]).includes(t.team)&&['Team lead','Head Analyst','Reviewer','Analyst'].includes(m.role)))recipients.add(m.id);
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
"""
write_file('app/api/detect/route.ts', detect_route, "vehicle endpoint")

# ============================================================
# version + changelog
# ============================================================
version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")
pkg = pathlib.Path('package.json')
new_pkg, n = re.subn(r'"version":\s*"[^"]*"', f'"version": "{VERSION}"', pkg.read_text(), count=1)
if n == 1:
    pkg.write_text(new_pkg)
    print(f"OK: package.json version set to {VERSION}")
changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Vehicle re-check: when the original vehicle finds the location clear at least 12 hours later, the ticket moves to pending closure, the assigned team is notified, and it auto-closes and archives after 7 days (daily sweep; any manual stage change or a new detection cancels it)
- New vehicle tickets resolve the street name from the GPS fix; the vehicle no longer has to send it
- Vehicle detections inside an open ticket's 20 m radius are matched by location only
- Contract coverage now uses the scope area when a contract has one, otherwise road name (abbreviation tolerant)
- Address lookup allows Admin, Team lead and Analyst, is country-optional, and biases toward the workspace area
- Added a batch thumbnail-URL endpoint for ticket images
- Added Serbia and EU region codes for address lookup
"""
if changelog_path.exists():
    existing_cl = changelog_path.read_text()
    if f"## {VERSION}" not in existing_cl:
        changelog_path.write_text(entry + "\n" + existing_cl)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Run the frontend script (phase11b) next, then build once.")
print("Backend-only builds will not pass: the frontend script finishes the wiring.")
