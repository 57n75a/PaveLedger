import {z} from 'zod';
import {context,failure} from '@/lib/context';
import {AppError} from '@/lib/actions';
import {sendMail,supportMessage,makeLimiter} from '@/lib/mail';
export const runtime='nodejs';export const dynamic='force-dynamic';

const limiter=makeLimiter(3,10*60_000);
const headers={'Cache-Control':'private, no-store'};

export async function POST(req:Request){try{
 const origin=req.headers.get('origin');if(origin&&origin!==new URL(req.url).origin)throw new AppError('Origin mismatch',403);
 if(Number(req.headers.get('content-length'))>16384)throw new AppError('Request too large',413);
 const raw=await req.text();if(new TextEncoder().encode(raw).length>16384)throw new AppError('Request too large',413);
 let form:{name:string,email:string,message:string};
 try{form=z.object({name:z.string().trim().min(1).max(120),email:z.string().trim().email().max(200),message:z.string().trim().min(5).max(4000)}).parse(JSON.parse(raw));}
 catch{throw new AppError('Enter your name, a valid email address, and a message of at least 5 characters.');}
 const c=await context(req);
 if(!limiter(c.actual.id,Date.now()))throw new AppError('Please wait a few minutes before sending another message.',429);
 const result=await sendMail(supportMessage(c.actual,form,process.env.SUPPORT_EMAIL?.trim()||'paveledger@gmail.com'));
 if(result.ok)return Response.json({sent:true},{headers});
 // Not configured: the browser falls back to opening the person's email app.
 if(result.reason==='not-configured')return Response.json({error:'Sending from the app is not set up yet.',fallback:true},{status:503,headers});
 console.error('Support email failed:',result.reason,result.detail||'');
 throw new AppError('Your message could not be sent right now. Please try again later, or email paveledger@gmail.com directly.',503);
}catch(e){return failure(e)}}
