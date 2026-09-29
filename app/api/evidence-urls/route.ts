import {context,failure} from '@/lib/context';
import {adminClient,workspaceId} from '@/lib/store';
import {canSee} from '@/lib/domain';
import {AppError} from '@/lib/actions';
export const runtime='nodejs';export const dynamic='force-dynamic';
const bucket='paveledger-evidence';

export async function GET(req:Request){try{
 const c=await context(req);
 const url=new URL(req.url);
 const t=c.state.tickets.find(x=>x.id===url.searchParams.get('ticket'));
 if(!t||!canSee(t,c.member))throw new AppError('Case unavailable.',403);
 const list=(t.evidence||[]).filter(e=>!(c.member.role==='Contractor'&&e.visibility!=='shared'));
 if(!list.length)return Response.json({urls:{}},{headers:{'Cache-Control':'private, no-store'}});
 const byPath:Record<string,string>={};
 for(const e of list)byPath[`${workspaceId}/${t.id}/${e.id}`]=e.id;
 const {data,error}=await adminClient().storage.from(bucket).createSignedUrls(Object.keys(byPath),300);
 if(error||!data)throw new AppError('Evidence could not be retrieved.',503);
 const urls:Record<string,string>={};
 for(const row of data){if(row.path&&row.signedUrl&&byPath[row.path])urls[byPath[row.path]]=row.signedUrl}
 return Response.json({urls},{headers:{'Cache-Control':'private, no-store'}});
}catch(e){return failure(e)}}
