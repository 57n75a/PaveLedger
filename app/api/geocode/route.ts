import {context,failure} from '@/lib/context';
import {AppError} from '@/lib/actions';
import {forwardGeocode} from '@/lib/geo';
export const runtime='nodejs';export const dynamic='force-dynamic';

export async function GET(req:Request){try{
 const c=await context(req);
 if(!['Admin','Team lead','Analyst'].includes(c.member.role))throw new AppError('Not permitted to look up addresses.',403);
 const url=new URL(req.url);
 const q=(url.searchParams.get('q')||'').trim();
 if(q.length<3||q.length>300)throw new AppError('Enter a fuller address.');
 const country=url.searchParams.get('country')||undefined;
 const rawLat=url.searchParams.get('nearLat'),rawLng=url.searchParams.get('nearLng');
 const nl=Number(rawLat),ng=Number(rawLng);
 const hasNear=rawLat!==null&&rawLng!==null&&Number.isFinite(nl)&&Number.isFinite(ng);
 let hit;
 try{hit=await forwardGeocode(q,{country,nearLat:hasNear?nl:undefined,nearLng:hasNear?ng:undefined})}
 catch{throw new AppError('Address lookup is unavailable right now. You can enter coordinates or click the map instead.',503)}
 if(!hit)throw new AppError('No match found for that address. Try adding the city, or enter coordinates manually.',404);
 return Response.json(hit,{headers:{'Cache-Control':'private, no-store'}});
}catch(e){return failure(e)}}
