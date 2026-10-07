import {z} from 'zod';
import {context,project,failure} from '@/lib/context';
import {saveWorkspace,adminClient} from '@/lib/store';
import {AppError} from '@/lib/actions';
import {provisionMember,resetMemberPassword,deleteMember,type LoginDeps} from '@/lib/users';
export const dynamic='force-dynamic';export const runtime='nodejs';

const taken=(msg:string)=>/already (been )?registered|already exists|duplicate/i.test(msg);
const EXISTS='A sign-in with this email already exists. Choose "Link an existing sign-in" and paste its user ID from Supabase, Authentication, Users.';

function loginDeps(origin:string):LoginDeps{
 const admin=()=>adminClient().auth.admin;
 return {
  async createLogin(email,password,mustChange){
   const {data,error}=await admin().createUser({email,password,email_confirm:true,user_metadata:{must_change_password:mustChange}});
   if(error||!data.user)throw new AppError(error&&taken(error.message)?EXISTS:'Could not create the sign-in. Check the email address and try again.',error&&taken(error.message)?409:503);
   return data.user.id;
  },
  async inviteLogin(email,mustChange){
   const {data,error}=await admin().inviteUserByEmail(email,{redirectTo:origin,data:{must_change_password:mustChange}});
   if(error||!data.user)throw new AppError(error&&taken(error.message)?EXISTS:'The invitation email could not be sent. Check the email settings in Supabase, or create the sign-in with a temporary password instead.',error&&taken(error.message)?409:503);
   return data.user.id;
  },
  async setPassword(authUserId,password){
   const current=await admin().getUserById(authUserId);
   const meta={...(current.data.user?.user_metadata||{}),must_change_password:true};
   const {error}=await admin().updateUserById(authUserId,{password,user_metadata:meta});
   if(error)throw new AppError('Could not reset the password. Try again.',503);
  },
  async deleteLogin(authUserId){
   const {error}=await admin().deleteUser(authUserId);
   if(error)throw new Error(error.message);
  },
 };
}

export async function POST(req:Request){try{
 const origin=req.headers.get('origin');if(origin&&origin!==new URL(req.url).origin)throw new AppError('Origin mismatch',403);
 if(Number(req.headers.get('content-length'))>8192)throw new AppError('Request too large',413);
 const raw=await req.text();if(new TextEncoder().encode(raw).length>8192)throw new AppError('Request too large',413);
 let body:Record<string,unknown>;try{body=z.record(z.unknown()).parse(JSON.parse(raw));}catch{throw new AppError('Invalid request object.');}
 const mode=z.enum(['create','invite','resetPassword','delete']).parse(body.mode);
 const c=await context(req);
 if(body.revision!==c.row.revision)throw new AppError('Workspace changed. Refresh and review before saving.',409);
 const now=new Date().toISOString(),deps=loginDeps(new URL(req.url).origin),save=()=>saveWorkspace(c.state,c.row.revision);
 const headers={'Cache-Control':'private, no-store'};
 if(mode==='resetPassword'){
  const r=await resetMemberPassword(c.state,c.member,c.actual,String(body.memberId||''),now,c.row.owner,deps,save);
  return Response.json({...project(c.state,c.member,c.actual.role==='Admin'),revision:c.row.revision+1,password:r.password},{headers});
 }
 let extra:Record<string,unknown>={};
 if(mode==='delete'){const r=await deleteMember(c.state,c.member,c.actual,String(body.memberId||''),now,c.row.owner,deps,save);extra={loginRemoved:r.loginRemoved}}
 else{const r=await provisionMember(c.state,c.member,c.actual,body,now,c.row.owner,mode,deps,save);if(r.password)extra={password:r.password}}
 return Response.json({...project(c.state,c.member,c.actual.role==='Admin'),revision:c.row.revision+1,...extra},{headers});
}catch(e){return failure(e instanceof z.ZodError?new AppError('Check the form: '+e.issues.map(i=>i.path.join('.')+' '+i.message).join('; ')):e)}}
