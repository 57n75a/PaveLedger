import type {Member} from './domain.ts';

// Outgoing email through Resend (https://resend.com). Nothing is sent unless RESEND_API_KEY is set,
// so the app keeps working without it and callers can fall back to another route.
export type MailMessage={to:string,subject:string,text:string,replyTo?:string};
export type MailResult={ok:true}|{ok:false,reason:'not-configured'|'rejected'|'unavailable',detail?:string};
type MailEnv={RESEND_API_KEY?:string,MAIL_FROM?:string};
type Fetcher=(url:string,init:{method:string,headers:Record<string,string>,body:string,signal?:AbortSignal})=>Promise<{ok:boolean,status:number,text():Promise<string>}>;

// Resend's testing sender. It can only deliver to the address the Resend account was created with.
export const TEST_SENDER='PaveLedger <onboarding@resend.dev>';

export async function sendMail(msg:MailMessage,env:MailEnv=process.env as MailEnv,doFetch:Fetcher=fetch as unknown as Fetcher):Promise<MailResult>{
 const key=env.RESEND_API_KEY?.trim();
 if(!key)return {ok:false,reason:'not-configured'};
 const from=env.MAIL_FROM?.trim()||TEST_SENDER;
 try{
  const r=await doFetch('https://api.resend.com/emails',{
   method:'POST',
   headers:{Authorization:'Bearer '+key,'Content-Type':'application/json'},
   body:JSON.stringify({from,to:[msg.to],subject:msg.subject,text:msg.text,...(msg.replyTo?{reply_to:msg.replyTo}:{})}),
   signal:AbortSignal.timeout(8000),
  });
  if(r.ok)return {ok:true};
  const detail=(await r.text().catch(()=>'')).slice(0,300);
  return {ok:false,reason:[401,403,422].includes(r.status)?'rejected':'unavailable',detail};
 }catch(e){return {ok:false,reason:'unavailable',detail:(e as Error).message}}
}

const oneLine=(s:string)=>s.replace(/[\r\n]+/g,' ').trim();

// Build the message sent to support from the help form. Header fields never contain line breaks.
export function supportMessage(member:Member,form:{name:string,email:string,message:string},to:string):MailMessage{
 return {
  to,
  subject:'PaveLedger support: '+oneLine(form.name).slice(0,80),
  text:form.message.trim()+'\n\n---\nFrom: '+oneLine(form.name)+' <'+oneLine(form.email)+'>\nSigned in as: '+oneLine(member.name)+' ('+member.role+', '+oneLine(member.email)+')',
  replyTo:oneLine(form.email),
 };
}

// Simple in-memory limiter: at most `max` messages per `windowMs` for each key. Best effort per server instance.
export function makeLimiter(max:number,windowMs:number){
 const hits=new Map<string,number[]>();
 return (key:string,now:number):boolean=>{
  const recent=(hits.get(key)||[]).filter(t=>now-t<windowMs);
  if(recent.length>=max){hits.set(key,recent);return false}
  recent.push(now);hits.set(key,recent);return true;
 };
}

// Contractor emails need a sender on a verified domain, so they are enabled only when both settings exist.
export const mailReady=(env:MailEnv=process.env as MailEnv):boolean=>Boolean(env.RESEND_API_KEY?.trim()&&env.MAIL_FROM?.trim());
