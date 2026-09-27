import {createHash,randomUUID} from 'node:crypto';
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
