import {context,failure} from '@/lib/context';
import {AppError} from '@/lib/actions';
export const runtime='nodejs';export const dynamic='force-dynamic';
const EUROPE='al,ad,at,by,be,ba,bg,hr,cy,cz,dk,ee,fi,fr,de,gr,hu,is,ie,it,xk,lv,li,lt,lu,mt,md,mc,me,nl,mk,no,pl,pt,ro,sm,rs,sk,si,es,se,ch,ua,gb,va';
const CODES:Record<string,string>={USA:'us',CAN:'ca',Europe:EUROPE};
export async function GET(req:Request){try{
 const c=await context(req);
 if(c.member.role!=='Admin')throw new AppError('Only an administrator can look up contract addresses.',403);
 const url=new URL(req.url);
 const q=(url.searchParams.get('q')||'').trim();
 if(q.length<3||q.length>300)throw new AppError('Enter a fuller address.');
 const countrycodes=CODES[url.searchParams.get('country')||'']||'';
 const params=new URLSearchParams({q,format:'jsonv2',limit:'1'});
 if(countrycodes)params.set('countrycodes',countrycodes);
 const r=await fetch('https://nominatim.openstreetmap.org/search?'+params.toString(),{headers:{'User-Agent':'PaveLedger/2 (paveledger@gmail.com)','Accept-Language':'en'},cache:'no-store'});
 if(!r.ok)throw new AppError('Address lookup is unavailable right now. You can click the map to set the location instead.',503);
 const rows:any[]=await r.json();
 if(!rows.length)throw new AppError('No match found for that address in the selected region. Try adding the city, or click the map to set the location.',404);
 const lat=Number(rows[0].lat),lng=Number(rows[0].lon);
 if(!Number.isFinite(lat)||!Number.isFinite(lng))throw new AppError('Address lookup returned an unusable result.',502);
 return Response.json({lat,lng,label:String(rows[0].display_name||'')},{headers:{'Cache-Control':'private, no-store'}});
}catch(e){return failure(e)}}
