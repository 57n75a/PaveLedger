import {createHash,randomUUID} from 'node:crypto';
import {z} from 'zod';
import {context,failure} from '@/lib/context';
import {adminClient,saveWorkspace,workspaceId} from '@/lib/store';
import {canSee,closed,type Evidence} from '@/lib/domain';
import {AppError} from '@/lib/actions';
export const runtime='nodejs';export const dynamic='force-dynamic';
const bucket='paveledger-evidence';
const key=(ticket:string,id:string)=>`${workspaceId}/${ticket}/${id}`;
export async function GET(req:Request){try{const c=await context(req),url=new URL(req.url),t=c.state.tickets.find(t=>t.id===url.searchParams.get('ticket'));if(!t||!canSee(t,c.member))throw new AppError('Case unavailable.',403);const e=t.evidence?.find(e=>e.id===url.searchParams.get('id'));if(!e||c.member.role==='Contractor'&&e.visibility!=='shared')throw new AppError('Evidence unavailable.',403);const {data,error}=await adminClient().storage.from(bucket).createSignedUrl(key(t.id,e.id),60);if(error||!data)throw new AppError('Evidence could not be retrieved.',503);return Response.json({url:data.signedUrl},{headers:{'Cache-Control':'private, no-store'}})}catch(e){return failure(e)}}
export async function POST(req:Request){try{
 const origin=req.headers.get('origin');if(origin&&origin!==new URL(req.url).origin)throw new AppError('Origin mismatch',403);
 if(Number(req.headers.get('content-length'))>3_300_000)throw new AppError('Use an image smaller than 3 MB.',413);
 const c=await context(req),form=await req.formData(),t=c.state.tickets.find(t=>t.id===form.get('ticket'));
 if(!t||!canSee(t,c.member)||!['Admin','Team lead','Analyst','Reviewer','Contractor'].includes(c.member.role))throw new AppError('Upload not permitted.',403);
 if(closed(t))throw new AppError('Reopen the case before adding evidence.');
 if(Number(form.get('revision'))!==c.row.revision)throw new AppError('Workspace changed; refresh before uploading.',409);
 if(form.get('authorized')!=='true')throw new AppError('Confirm the image is authorized and redacted for this case.');
 const v=z.object({purpose:z.enum(['detection','repair','verification']),capturedAt:z.string().datetime(),lat:z.coerce.number().min(-90).max(90),lng:z.coerce.number().min(-180).max(180),accuracy:z.coerce.number().positive().max(1000),lane:z.string().trim().min(1).max(100),quality:z.enum(['clear','unclear'])}).parse(Object.fromEntries(form));
 if(c.member.role==='Contractor'&&v.purpose!=='repair')throw new AppError('Contractors may upload repair evidence only.',403);
 if(v.capturedAt>new Date().toISOString()||v.capturedAt<new Date(Date.parse(t.created)-30*86400000).toISOString())throw new AppError('Capture time must be no more than 30 days before case creation and not in the future.');
 const file=form.get('file');if(!(file instanceof File)||file.size<12||file.size>3_000_000)throw new AppError('Choose a JPEG, PNG or WebP file up to 3 MB.');
 if((t.evidence||[]).length>=40)throw new AppError('Pilot evidence limit of 40 files per case reached.');
 const bytes=Buffer.from(await file.arrayBuffer());let mime='';if(bytes[0]===255&&bytes[1]===216&&bytes[2]===255)mime='image/jpeg';else if(bytes.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])))mime='image/png';else if(bytes.subarray(0,4).toString()==='RIFF'&&bytes.subarray(8,12).toString()==='WEBP')mime='image/webp';if(!mime)throw new AppError('File contents are not a supported image.');
 const sha256=createHash('sha256').update(bytes).digest('hex');if(t.evidence?.some(e=>e.sha256===sha256))throw new AppError('This exact image is already attached.');
 const visibility=c.member.role==='Contractor'||form.get('shared')==='on'?'shared':'internal';
 const id=randomUUID(),now=new Date().toISOString(),e:Evidence={...v,id,name:file.name.slice(0,150),mime,bytes:file.size,sha256,uploadedAt:now,uploadedBy:c.actual.id,visibility};
 const {error}=await adminClient().storage.from(bucket).upload(key(t.id,id),bytes,{contentType:mime,upsert:false});if(error)throw new AppError('Upload failed. Check the private evidence bucket setup.',503);
 try{t.evidence??=[];t.evidence.push(e);t.observations++;t.updated=now;t.history.push({at:now,actor:c.actual.name,action:'Evidence uploaded',note:`${v.purpose}: ${id}; SHA-256 ${sha256}`,visibility});c.state.events.unshift({at:now,actor:c.actual.name,action:'Evidence uploaded '+t.id+' '+id});if(!await saveWorkspace(c.state,c.row.revision))throw new AppError('Workspace changed while uploading; refresh and retry.',409);}catch(error){await adminClient().storage.from(bucket).remove([key(t.id,id)]);throw error;}
 return Response.json({id},{headers:{'Cache-Control':'private, no-store'}});
 }catch(e){return failure(e instanceof z.ZodError?new AppError('Check image metadata, location and capture date.'):e)}}
