import 'server-only';

const UA='PaveLedger/2 (paveledger@gmail.com)';
const EU='at,be,bg,hr,cy,cz,dk,ee,fi,fr,de,gr,hu,ie,it,lv,lt,lu,mt,nl,pl,pt,ro,sk,si,es,se';
export const COUNTRY_CODES:Record<string,string>={USA:'us',CAN:'ca',SRB:'rs',EU:EU,Europe:EU};

async function nominatim(path:string,params:URLSearchParams,timeoutMs:number){
 const ctl=new AbortController();
 const timer=setTimeout(()=>ctl.abort(),timeoutMs);
 try{return await fetch('https://nominatim.openstreetmap.org/'+path+'?'+params.toString(),{headers:{'User-Agent':UA,'Accept-Language':'en'},cache:'no-store',signal:ctl.signal})}
 finally{clearTimeout(timer)}
}

// Nearest mapped street for a GPS fix. Returns null if the lookup fails.
export async function reverseStreet(lat:number,lng:number):Promise<string|null>{
 try{
  const p=new URLSearchParams({lat:String(lat),lon:String(lng),format:'jsonv2',zoom:'17',addressdetails:'1'});
  const r=await nominatim('reverse',p,4000);
  if(!r.ok)return null;
  const d:any=await r.json();
  const road=d?.address?.road||d?.address?.pedestrian||d?.address?.residential||d?.name;
  return road?String(road).slice(0,150):null;
 }catch{return null}
}

// Address or street to coordinates. Returns null when nothing matches; throws when the service is unavailable.
export async function forwardGeocode(q:string,opts:{country?:string,nearLat?:number,nearLng?:number}={}):Promise<{lat:number,lng:number,label:string}|null>{
 const p=new URLSearchParams({q,format:'jsonv2',limit:'1'});
 const cc=opts.country?COUNTRY_CODES[opts.country]:undefined;
 if(cc)p.set('countrycodes',cc);
 if(typeof opts.nearLat==='number'&&typeof opts.nearLng==='number'){
  const d=0.3;
  p.set('viewbox',[opts.nearLng-d,opts.nearLat+d,opts.nearLng+d,opts.nearLat-d].join(','));
  p.set('bounded','0');
 }
 const r=await nominatim('search',p,6000);
 if(!r.ok)throw new Error('unavailable');
 const rows:any[]=await r.json();
 if(!rows.length)return null;
 const lat=Number(rows[0].lat),lng=Number(rows[0].lon);
 if(!Number.isFinite(lat)||!Number.isFinite(lng))return null;
 return {lat,lng,label:String(rows[0].display_name||'')};
}
