import 'server-only';
import {authenticatedUser,readWorkspace} from './store';
import {canSee,isActive,type State,type Member} from './domain';
import {AppError} from './actions';
export async function context(req:Request){
 const user=await authenticatedUser(req),row=await readWorkspace(user),state=row.data;
 const actual=state.members.find(m=>!m.demo&&isActive(m)&&(m.authUserId===user.userId||m.id===user.userId));
 if(!actual)throw new AppError('Your verified account has no active membership. Ask the administrator to bind your Supabase user ID.',403);
 const preview=new URL(req.url).searchParams.get('persona');
 const member=actual.role==='Admin'&&preview?state.members.find(m=>m.id===preview&&isActive(m)):actual;
 if(!member)throw new AppError('Preview member unavailable.',404);
 return {row,state,member,actual,user};
}
export function project(s:State,m:Member,admin:boolean){
 const tickets=s.tickets.filter(t=>canSee(t,m)).map(t=>m.role==='Contractor'?{...t,note:'',analyst:'',history:t.history.filter(h=>h.visibility==='shared'),evidence:(t.evidence||[]).filter(e=>e.visibility==='shared')}:t);
 const ids=new Set(tickets.map(t=>t.id));
 const members=s.members.filter(x=>m.role==='Admin'||m.role==='Auditor'||(['Team lead','Reviewer'].includes(m.role)&&x.team===m.team)||x.id===m.id).map(x=>({...x,email:m.role==='Admin'?x.email:'',authUserId:m.role==='Admin'?x.authUserId:undefined}));
 return {...s,tickets,members,teams:['Admin','Auditor'].includes(m.role)?s.teams:m.team?[m.team]:[],contracts:s.contracts.filter(c=>['Admin','Auditor'].includes(m.role)||tickets.some(t=>t.road===c.road)&&(m.role!=='Contractor'||c.contractor===m.contractor)),notifications:s.notifications.filter(n=>(m.role==='Admin'||n.recipient===m.id)&&ids.has(n.ticket)),events:['Admin','Auditor'].includes(m.role)?s.events:[],viewer:{...m,authUserId:undefined},canPreview:admin,personas:admin?s.members.filter(isActive).map(x=>({id:x.id,name:x.name,role:x.role})):[]};
}
export function failure(e:unknown){let status=503,message='The operation could not be completed. Your unsaved input is retained; retry or contact your administrator.';if(e instanceof AppError){status=e.status;message=e.message;}else if(e instanceof Error&&/^\d{3}:/.test(e.message)){status=Number(e.message.slice(0,3));message=e.message.slice(4);}return Response.json({error:message},{status,headers:{'Cache-Control':'private, no-store'}})}
