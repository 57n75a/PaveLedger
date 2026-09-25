import {z} from 'zod';
import {context,project,failure} from '@/lib/context';
import {saveWorkspace} from '@/lib/store';
import {applyAction,AppError} from '@/lib/actions';
export const dynamic='force-dynamic';export const runtime='nodejs';
export async function GET(req:Request){try{const c=await context(req);return Response.json({...project(c.state,c.member,c.actual.role==='Admin'),revision:c.row.revision},{headers:{'Cache-Control':'private, no-store'}})}catch(e){return failure(e)}}
export async function POST(req:Request){try{
 const origin=req.headers.get('origin');if(origin&&origin!==new URL(req.url).origin)throw new AppError('Origin mismatch',403);
 if(Number(req.headers.get('content-length'))>32768)throw new AppError('Request too large',413);
 const raw=await req.text();if(new TextEncoder().encode(raw).length>32768)throw new AppError('Request too large',413);
 let body:Record<string,unknown>;try{body=z.record(z.unknown()).parse(JSON.parse(raw));}catch{throw new AppError('Invalid request object.');}
 const c=await context(req);if(body.revision!==c.row.revision)throw new AppError('Workspace changed. Refresh and review before saving.',409);
 applyAction(c.state,c.member,c.actual,body,new Date().toISOString(),c.row.owner);
 if(!await saveWorkspace(c.state,c.row.revision))throw new AppError('A simultaneous update occurred. Refresh and retry.',409);
 return Response.json({...project(c.state,c.member,c.actual.role==='Admin'),revision:c.row.revision+1},{headers:{'Cache-Control':'private, no-store'}});
 }catch(e){return failure(e instanceof z.ZodError?new AppError('Check the form: '+e.issues.map(i=>i.path.join('.')+' '+i.message).join('; ')):e)}}
