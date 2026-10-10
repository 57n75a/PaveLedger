import {z} from 'zod';
import {context,project,failure} from '@/lib/context';
import {saveWorkspace} from '@/lib/store';
import {applyAction,AppError} from '@/lib/actions';
import {sendMail,mailReady} from '@/lib/mail';
import {runOutbox} from '@/lib/outbox';
import {MAX_IMAGE_BODY,bodyTooLarge} from '@/lib/limits';
export const dynamic='force-dynamic';export const runtime='nodejs';
export async function GET(req:Request){try{const c=await context(req);return Response.json({...project(c.state,c.member,c.actual.role==='Admin'),revision:c.row.revision},{headers:{'Cache-Control':'private, no-store'}})}catch(e){return failure(e)}}
export async function POST(req:Request){try{
 const origin=req.headers.get('origin');if(origin&&origin!==new URL(req.url).origin)throw new AppError('Origin mismatch',403);
 if(Number(req.headers.get('content-length'))>MAX_IMAGE_BODY)throw new AppError('Request too large',413);
 const raw=await req.text();const size=new TextEncoder().encode(raw).length;if(size>MAX_IMAGE_BODY)throw new AppError('Request too large',413);
 let body:Record<string,unknown>;try{body=z.record(z.unknown()).parse(JSON.parse(raw));}catch{throw new AppError('Invalid request object.');}
 if(bodyTooLarge(size,body.action))throw new AppError('Request too large',413);
 const c=await context(req);if(body.revision!==c.row.revision)throw new AppError('Workspace changed. Refresh and review before saving.',409);
 applyAction(c.state,c.member,c.actual,body,new Date().toISOString(),c.row.owner);
 if(!await saveWorkspace(c.state,c.row.revision))throw new AppError('A simultaneous update occurred. Refresh and retry.',409);
 let revision=c.row.revision+1;
 if(mailReady()&&(c.state.outbox||[]).some(i=>i.status==='queued'||i.status==='sending')){try{await runOutbox(c.state,new Date().toISOString(),{max:3,appUrl:new URL(req.url).origin,send:m=>sendMail(m),save:async()=>{const ok=await saveWorkspace(c.state,revision);if(ok)revision+=1;return ok}})}catch(e){console.error('Notice delivery failed',e)}}
 return Response.json({...project(c.state,c.member,c.actual.role==='Admin'),revision},{headers:{'Cache-Control':'private, no-store'}});
 }catch(e){return failure(e instanceof z.ZodError?new AppError('Check the form: '+e.issues.map(i=>i.path.join('.')+' '+i.message).join('; ')):e)}}
