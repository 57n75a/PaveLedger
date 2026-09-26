import { z } from 'zod';
import {canSee,permitted,isActive,closed,eligibleVerification,roles,type State,type Member,type Ticket,type Status} from './domain.ts';
export class AppError extends Error {status:number;constructor(message:string,status=400){super(message);this.status=status}}
const short=z.string().trim().min(1).max(150),noteField=z.string().trim().min(10).max(2000);
export function applyAction(s:State,m:Member,actual:Member,body:Record<string,unknown>,now:string,ownerId:string){
 const actor=actual.name+(m.id!==actual.id?` previewing ${m.name}`:'');
 const action=z.string().parse(body.action);const note=typeof body.note==='string'?body.note.trim().slice(0,2000):'';
 const requireRole=(allowed:string[])=>{if(!isActive(m)||!allowed.includes(m.role))throw new AppError('This action is not permitted for your role.',403)};
 let event=action;
 if(action==='create'){
  requireRole(['Admin','Team lead','Analyst']);const v=z.object({road:short,title:short,lat:z.coerce.number().min(-90).max(90),lng:z.coerce.number().min(-180).max(180),accuracy:z.coerce.number().positive().max(1000),lane:short,note:noteField}).parse(body);
  if(s.tickets.length>=500)throw new AppError('Pilot workspace limit of 500 cases reached. Export and plan the relational migration; do not discard the audit record.');
  if(m.role!=='Admin'&&!s.teams.includes(m.team))throw new AppError('Assign the member to a valid team first.');
  const id=`PL-${now.slice(0,4)}-${crypto.randomUUID().slice(0,8).toUpperCase()}`;
  const t:Ticket={...v,id,severity:['Urgent','Standard','Low'].includes(String(body.severity))?String(body.severity):'Standard',status:'Detected',team:m.team||s.teams[0]||'',analyst:m.role==='Analyst'?m.id:'',contractor:'',warranty:'Needs review',source:'Manual report',confidence:0,created:now,updated:now,due:new Date(Date.parse(now)+86400000).toISOString(),reopened:0,observations:1,evidence:[],history:[{at:now,actor,action:'Detected',note:v.note,visibility:'internal'}]};s.tickets.unshift(t);event='Created '+id;
 }else if(action==='contract'){
  requireRole(['Admin']);const v=z.object({contractor:short,road:short,scope:z.string().trim().min(10).max(2000),start:z.string().regex(/^\d{4}-\d{2}-\d{2}$/),end:z.string().regex(/^\d{4}-\d{2}-\d{2}$/),poc:short,email:z.string().trim().email().max(250)}).parse(body);
  if(v.end<v.start||[v.start,v.end].some(x=>!Number.isFinite(Date.parse(x))||new Date(x).toISOString().slice(0,10)!==x))throw new AppError('Enter valid warranty start and end dates.');
  const id='CT-'+crypto.randomUUID().slice(0,8).toUpperCase();s.contracts.push({...v,id});event='Contract registered: '+id;
 }else if(action==='team'){
  requireRole(['Admin']);const name=short.parse(body.name);if(s.teams.some(x=>x.toLowerCase()===name.toLowerCase()))throw new AppError('A team with that name already exists.');s.teams.push(name);event='Team created: '+name;
 }else if(action==='member'||action==='memberUpdate'){
  requireRole(['Admin']);if(actual.id!==m.id)throw new AppError('Return to your own administrator identity before changing access.',403);
  const v=z.object({name:short,email:z.string().trim().email().max(250).transform(x=>x.toLowerCase()),role:z.enum(roles as [typeof roles[number],...typeof roles[number][]]),team:z.string().max(150),contractor:z.string().max(150),vehicleTag:z.string().max(150).optional().transform(x=>x?.trim()||''),authUserId:z.string().uuid(),active:z.boolean()}).parse(body);
  const existing=action==='memberUpdate'?s.members.find(x=>x.id===body.memberId):undefined;if(action==='memberUpdate'&&!existing)throw new AppError('Member not found.');
  if(s.members.some(x=>x.id!==existing?.id&&(x.email.toLowerCase()===v.email||x.authUserId===v.authUserId)))throw new AppError('Email or authentication user ID already has a membership.');
  if(['Team lead','Analyst','Reviewer','Head Analyst'].includes(v.role)&&!s.teams.includes(v.team))throw new AppError('Choose an existing team.');
  if(v.role==='Contractor'&&!s.contracts.some(x=>x.contractor===v.contractor))throw new AppError('Choose an existing contractor firm.');
  if(v.role==='Vehicle'&&!v.vehicleTag.trim())throw new AppError('Enter a vehicle tag (e.g. Truck-07).');
  if(existing&&(existing.id===actual.id||existing.id===ownerId)&&(v.role!==existing.role||v.active!==isActive(existing)||v.authUserId!==(existing.authUserId||existing.id)))throw new AppError('Your own access and the designated owner identity cannot be demoted, suspended or rebound here.');
  if(existing?.role==='Admin'&&(v.role!=='Admin'||!v.active)&&s.members.filter(x=>x.role==='Admin'&&isActive(x)).length<=1)throw new AppError('Keep at least one active administrator.');
  if(existing&&(!v.active||v.role!=='Analyst'||v.team!==existing.team)&&s.tickets.some(t=>t.analyst===existing.id&&!closed(t)))throw new AppError('Reassign this member’s open investigations before changing their access or team.');
  if(existing&&existing.authUserId&&existing.authUserId!==v.authUserId)throw new AppError('An existing account binding cannot be replaced. Create a new membership and suspend the old one.');
  const clean={...v,team:['Team lead','Analyst','Reviewer','Admin','Head Analyst'].includes(v.role)?v.team:'',contractor:v.role==='Contractor'?v.contractor:'',vehicleTag:v.role==='Vehicle'?v.vehicleTag:'',demo:false};
  if(existing)Object.assign(existing,clean);else s.members.push({id:crypto.randomUUID(),...clean});
  event=`Membership ${existing?'updated':'created'}: ${v.name}; role ${v.role}; active ${v.active}`;
 }else{
  const t=s.tickets.find(x=>x.id===body.id);if(!t||!canSee(t,m))throw new AppError('Ticket not accessible.',403);
  let visibility:'internal'|'shared'=m.role==='Contractor'||body.visibility==='shared'?'shared':'internal';
  if(action==='assign'){
   requireRole(['Admin','Team lead']);if(closed(t))throw new AppError('Reopen a closed case before reassignment.');const team=short.parse(body.team);if(!s.teams.includes(team)||(m.role==='Team lead'&&team!==m.team))throw new AppError('Choose an accessible team.');
   const a=body.analyst?s.members.find(x=>x.id===body.analyst&&x.role==='Analyst'&&x.team===team&&isActive(x)):null;if(body.analyst&&!a)throw new AppError('Choose an active analyst in this team.');
   t.team=team;t.analyst=a?.id||'';if(['Detected','Team assigned','Analyst assigned'].includes(t.status))t.status=a?'Analyst assigned':'Team assigned';if(a)s.notifications.unshift({id:crypto.randomUUID(),recipient:a.id,ticket:t.id,text:`Assigned to you: ${t.road}`,at:now});event='Assignment updated';
  }else if(action==='transition'){
   const next=short.parse(body.status);if(!permitted(m,t,next))throw new AppError('This stage change is not permitted for your role or the current stage.',403);noteField.parse(note);
   if(next==='Team assigned'&&!s.teams.includes(t.team))throw new AppError('Assign an existing team first.');
   if(next==='Analyst assigned'&&!s.members.some(x=>x.id===t.analyst&&x.role==='Analyst'&&x.team===t.team&&isActive(x)))throw new AppError('Assign an active analyst in this team first.');
   if(next==='Notice prepared'){
    const contract=s.contracts.find(x=>x.id===body.contract);const observed=t.created.slice(0,10);
    if(!contract||contract.road!==t.road||contract.start>observed||contract.end<observed||body.scopeConfirmed!==true)throw new AppError('Select a contract covering the recorded observation date and road, then confirm its location, work scope and notice terms.');
    t.contractor=contract.contractor;t.contractId=contract.id;t.warranty='Scope reviewed';visibility='shared';
   }
   if(next==='Duplicate'){const parent=s.tickets.find(x=>x.id===body.duplicateOf);if(!parent||!canSee(parent,m)||parent.id===t.id||['Duplicate','Rejected'].includes(parent.status))throw new AppError('Select an accessible primary case that is not itself a duplicate or rejected.');t.duplicateOf=parent.id;}
   if(next==='On hold')t.holdFrom=t.status;
   if(t.status==='On hold'&&next===t.holdFrom)delete t.holdFrom;
   if(next==='Awaiting verification'&&t.status!=='On hold'){t.completedAt=now;t.completedBy=actual.id;visibility='shared';}
   if(next==='Verified closed'){
    const e=t.evidence?.find(x=>x.id===body.evidenceId);if(!e||!eligibleVerification(t,e)||body.verification!=='clear-pass')throw new AppError('Choose clear, location-matched verification evidence captured after completion; confirm the same lane is visibly repaired.');
    if(t.analyst===actual.id||t.completedBy===actual.id)throw new AppError('Closure requires a reviewer independent of the assigned analyst and the completion claimant.',403);
    t.verification=`Clear repeat pass ${e.id} reviewed by ${actual.name} at ${now}. ${note}`;t.closedAt=now;t.closedBy=actual.id;visibility='shared';
   }
   if(next==='Reopened'){t.reopened++;t.due=new Date(Date.parse(now)+86400000).toISOString();visibility='shared';}
   t.status=next as Status;event=t.status;if(t.analyst)s.notifications.unshift({id:crypto.randomUUID(),recipient:t.analyst,ticket:t.id,text:`Status changed: ${t.road} is now ${next}`,at:now});
  }else if(action==='priority'){
   if(!isActive(m)||m.role==='Auditor')throw new AppError('This action is not permitted for your role.',403);
   const sev=z.enum(['Urgent','Standard','Low']).parse(body.severity);t.severity=sev;event='Priority set to '+sev;
  }else if(action==='note'){requireRole(['Admin','Team lead','Analyst','Reviewer','Contractor']);noteField.parse(note);event='Note added';}else if(action==='escalate'){const targetRole=m.role==='Head Analyst'?'Team lead':m.role==='Team lead'?'Director':null;if(!targetRole)throw new AppError('Your role cannot escalate tickets.',403);t.escalatedTo=targetRole;t.updated=now;const recipients=s.members.filter(x=>isActive(x)&&x.role===targetRole&&(targetRole!=='Team lead'||x.team===t.team));recipients.forEach(r=>s.notifications.unshift({id:crypto.randomUUID(),recipient:r.id,ticket:t.id,text:`Escalated to ${targetRole}: ${t.road}`,at:now}));event='Escalated to '+targetRole;}
  else throw new AppError('Unknown action.');
  t.updated=now;t.history.push({at:now,actor,action:event,note:note||'Assignment recorded',visibility});event+=' '+t.id;
 }
 s.events.unshift({at:now,actor,action:event});
 if(JSON.stringify(s).length>8_000_000)throw new AppError('Pilot workspace size limit reached. Export and migrate to the normalized production model.');
}
