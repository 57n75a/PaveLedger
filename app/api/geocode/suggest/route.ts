import {context,failure} from '@/lib/context';
import {AppError} from '@/lib/actions';
import {suggestAddresses} from '@/lib/geo';
import {instance} from '@/lib/instance';
export const runtime='nodejs';export const dynamic='force-dynamic';

// Address suggestions while typing, limited to this deployment's country.
export async function GET(req:Request){try{
 const c=await context(req);
 if(!['Admin','Head Analyst','Analyst'].includes(c.member.role))throw new AppError('Not permitted to look up addresses.',403);
 const url=new URL(req.url);
 const q=(url.searchParams.get('q')||'').trim();
 if(q.length<3)return Response.json([],{headers:{'Cache-Control':'private, no-store'}});
 if(q.length>200)throw new AppError('Enter a fuller address.');
 const nl=Number(url.searchParams.get('nearLat')),ng=Number(url.searchParams.get('nearLng'));
 const near=url.searchParams.has('nearLat')&&Number.isFinite(nl)&&Number.isFinite(ng);
 let rows;
 try{rows=await suggestAddresses(q,{country:instance.geocodeCountry,bbox:instance.bbox,lang:url.searchParams.get('lang')||undefined,nearLat:near?nl:undefined,nearLng:near?ng:undefined})}
 catch{throw new AppError('Address lookup is unavailable right now. You can enter coordinates or click the map instead.',503)}
 return Response.json(rows,{headers:{'Cache-Control':'private, no-store'}});
}catch(e){return failure(e)}}
