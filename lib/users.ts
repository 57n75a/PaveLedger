import {randomBytes} from 'node:crypto';
import {applyAction,AppError} from './actions.ts';
import type {State,Member} from './domain.ts';

// Operations on Supabase sign-in accounts, injected so the logic can be tested without a network.
export type LoginDeps={
 createLogin(email:string,password:string,mustChange:boolean):Promise<string>;
 inviteLogin(email:string,mustChange:boolean):Promise<string>;
 setPassword(authUserId:string,password:string):Promise<void>;
 deleteLogin(authUserId:string):Promise<void>;
};
export const tempPassword=()=>randomBytes(12).toString('base64url');
const needAdmin=(m:Member,actual:Member)=>{if(m.role!=='Admin'||actual.role!=='Admin'||actual.id!==m.id)throw new AppError('Only an administrator can manage sign-in accounts. Return to your own identity first.',403)};
const conflict=()=>new AppError('A simultaneous update occurred. Refresh and retry.',409);

// Create a membership together with its sign-in account.
// The membership is validated first (dry run) so a bad request never creates an orphan login,
// and the login is removed again if the membership cannot be saved.
export async function provisionMember(s:State,m:Member,actual:Member,body:Record<string,unknown>,now:string,ownerId:string,mode:'create'|'invite',deps:LoginDeps,save:()=>Promise<boolean>):Promise<{password?:string,authUserId:string}>{
 needAdmin(m,actual);
 const probe=structuredClone(s);
 applyAction(probe,m,actual,{...body,action:'member',authUserId:crypto.randomUUID()},now,ownerId);
 const added=probe.members[probe.members.length-1];
 const mustChange=added.role!=='Vehicle';
 const password=mode==='create'?tempPassword():undefined;
 const authUserId=mode==='create'?await deps.createLogin(added.email,password as string,mustChange):await deps.inviteLogin(added.email,mustChange);
 try{
  applyAction(s,m,actual,{...body,action:'member',authUserId},now,ownerId);
  if(!await save())throw conflict();
 }catch(e){
  try{await deps.deleteLogin(authUserId)}catch{/* best effort rollback */}
  throw e;
 }
 return {password,authUserId};
}

// Issue a new temporary password for another member. Not for yourself or the owner identity.
export async function resetMemberPassword(s:State,m:Member,actual:Member,memberId:string,now:string,ownerId:string,deps:LoginDeps,save:()=>Promise<boolean>):Promise<{password:string}>{
 needAdmin(m,actual);
 const t=s.members.find(x=>x.id===memberId);
 if(!t)throw new AppError('Member not found.',404);
 const loginId=t.authUserId;
 if(!loginId||t.demo)throw new AppError('This member has no linked sign-in account to reset.');
 if(t.id===actual.id||loginId===actual.authUserId||t.id===ownerId||loginId===ownerId)throw new AppError('Use Settings to change your own password. The owner password cannot be reset here.',403);
 s.events.unshift({at:now,actor:m.name,action:'Password reset issued for '+t.name});
 if(!await save())throw conflict();
 const password=tempPassword();
 await deps.setPassword(loginId,password);
 return {password};
}

// Delete a membership (same safeguards as the memberDelete action) and then its sign-in account.
export async function deleteMember(s:State,m:Member,actual:Member,memberId:string,now:string,ownerId:string,deps:LoginDeps,save:()=>Promise<boolean>):Promise<{loginRemoved:boolean}>{
 needAdmin(m,actual);
 const t=s.members.find(x=>x.id===memberId);
 const loginId=t&&!t.demo?t.authUserId:undefined;
 applyAction(s,m,actual,{action:'memberDelete',memberId},now,ownerId);
 if(!await save())throw conflict();
 let loginRemoved=!loginId;
 if(loginId){try{await deps.deleteLogin(loginId);loginRemoved=true}catch{loginRemoved=false}}
 return {loginRemoved};
}

// Keep a membership's stored email in step with the verified sign-in email (changed from the profile page).
// Returns true when the member was updated. Never creates a duplicate email.
export function syncMemberEmail(s:State,member:Member,authEmail:string,now:string):boolean{
 const email=authEmail.trim().toLowerCase();
 if(!email||member.email.trim().toLowerCase()===email)return false;
 if(s.members.some(x=>x.id!==member.id&&x.email.trim().toLowerCase()===email))return false;
 member.email=email;
 s.events.unshift({at:now,actor:'System',action:'Email updated for '+member.name+' after a sign-in email change'});
 return true;
}
