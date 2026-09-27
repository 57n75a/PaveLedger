import pathlib
from datetime import date

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

VERSION = "2.1.1"
TODAY = date.today().isoformat()

# ---------- lib/domain.ts: extend contracts with notes + documents ----------

replace_once('lib/domain.ts',
    "contracts:{id:string,contractor:string,road:string,scope:string,start:string,end:string,poc:string,email:string}[]",
    "contracts:{id:string,contractor:string,road:string,scope:string,start:string,end:string,poc:string,email:string,notes?:string,documents?:{id:string,name:string,mime:string,bytes:number,uploadedAt:string,uploadedBy:string}[]}[]",
    "domain.ts: extend contracts with notes and documents")

# ---------- lib/actions.ts: contractUpdate action ----------

replace_once('lib/actions.ts',
    "event='Contract registered: '+id;\n }else if(action==='team'){",
    "event='Contract registered: '+id;\n }else if(action==='contractUpdate'){\n  requireRole(['Admin']);const contractId=short.parse(body.contractId);const existing=s.contracts.find(x=>x.id===contractId);if(!existing)throw new AppError('Contract not found.');\n  const v=z.object({contractor:short,road:short,scope:z.string().trim().min(10).max(2000),start:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),end:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),poc:short,email:z.string().trim().email().max(250),notes:z.string().max(4000).optional().transform(x=>x?.trim()||'')}).parse(body);\n  if(v.end<v.start||[v.start,v.end].some(x=>!Number.isFinite(Date.parse(x))||new Date(x).toISOString().slice(0,10)!==x))throw new AppError('Enter valid warranty start and end dates.');\n  Object.assign(existing,v);\n  const linkIds=Array.isArray(body.linkTicketIds)?body.linkTicketIds as string[]:[];\n  for(const tid of linkIds){const lt=s.tickets.find(x=>x.id===tid);if(lt&&lt.road===existing.road){lt.contractor=existing.contractor;lt.contractId=existing.id;if(lt.warranty==='Needs review')lt.warranty='Candidate match';lt.updated=now;}}\n  event='Contract updated: '+existing.id;\n }else if(action==='team'){",
    "actions.ts: add contractUpdate action with incident linking")

# ---------- new file: app/api/contract-document/route.ts ----------

route_path = pathlib.Path('app/api/contract-document/route.ts')
route_path.parent.mkdir(parents=True, exist_ok=True)

route_code = """import {createHash,randomUUID} from 'node:crypto';
import {context,failure} from '@/lib/context';
import {adminClient,saveWorkspace,workspaceId} from '@/lib/store';
import {AppError} from '@/lib/actions';
export const runtime='nodejs';export const dynamic='force-dynamic';
const bucket='paveledger-evidence';
const key=(contract:string,id:string)=>`${workspaceId}/contracts/${contract}/${id}`;

export async function GET(req:Request){try{
 const c=await context(req);
 if(!['Admin','Team lead','Director','Auditor'].includes(c.member.role))throw new AppError('Not permitted.',403);
 const url=new URL(req.url),contract=c.state.contracts.find(x=>x.id===url.searchParams.get('contract'));
 if(!contract)throw new AppError('Contract unavailable.',404);
 const doc=contract.documents?.find(d=>d.id===url.searchParams.get('id'));
 if(!doc)throw new AppError('Document unavailable.',404);
 const {data,error}=await adminClient().storage.from(bucket).createSignedUrl(key(contract.id,doc.id),60);
 if(error||!data)throw new AppError('Document could not be retrieved.',503);
 return Response.json({url:data.signedUrl},{headers:{'Cache-Control':'private, no-store'}});
}catch(e){return failure(e)}}

export async function POST(req:Request){try{
 const origin=req.headers.get('origin');if(origin&&origin!==new URL(req.url).origin)throw new AppError('Origin mismatch',403);
 if(Number(req.headers.get('content-length'))>10_300_000)throw new AppError('Use a file smaller than 10 MB.',413);
 const c=await context(req);
 if(c.member.role!=='Admin')throw new AppError('Only an administrator can upload contract documents.',403);
 const form=await req.formData(),contract=c.state.contracts.find(x=>x.id===form.get('contract'));
 if(!contract)throw new AppError('Contract not found.',404);
 if(Number(form.get('revision'))!==c.row.revision)throw new AppError('Workspace changed; refresh before uploading.',409);
 const file=form.get('file');if(!(file instanceof File)||file.size<12||file.size>10_000_000)throw new AppError('Choose a file up to 10 MB.');
 const bytes=Buffer.from(await file.arrayBuffer());
 const mime=file.type||'application/octet-stream';
 const id=randomUUID(),now=new Date().toISOString();
 const {error}=await adminClient().storage.from(bucket).upload(key(contract.id,id),bytes,{contentType:mime,upsert:false});
 if(error)throw new AppError('Upload failed. Check the private evidence bucket setup.',503);
 try{
  contract.documents??=[];
  contract.documents.push({id,name:file.name.slice(0,150),mime,bytes:file.size,uploadedAt:now,uploadedBy:c.actual.id});
  c.state.events.unshift({at:now,actor:c.actual.name,action:'Contract document uploaded '+contract.id+' '+id});
  if(!await saveWorkspace(c.state,c.row.revision))throw new AppError('Workspace changed while uploading; refresh and retry.',409);
 }catch(err){await adminClient().storage.from(bucket).remove([key(contract.id,id)]);throw err;}
 return Response.json({id},{headers:{'Cache-Control':'private, no-store'}});
}catch(e){return failure(e)}}
"""

if route_path.exists():
    print(f"SKIP: {route_path} already exists — not overwriting.")
else:
    route_path.write_text(route_code)
    print(f"OK: created {route_path}")

# ---------- version + changelog ----------
version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

replace_once('package.json', '"version": "2.1.0",', f'"version": "{VERSION}",', "package.json: bump version field")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Added contractUpdate action: Admin can edit an existing contract's details and notes
- Added contract document storage (reuses the private evidence bucket under a contracts/ path) with a new /api/contract-document endpoint
- Editing a contract can now link existing incidents on the same road directly to it
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" in existing:
        print(f"SKIP: CHANGELOG.md already has an entry for {VERSION}")
    else:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Now run:")
print("  git diff")
print("  npm run build")
