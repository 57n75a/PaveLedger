import 'server-only';

const UA='PaveLedger/2 (paveledger@gmail.com)';
const EU='at,be,bg,hr,cy,cz,dk,ee,fi,fr,de,gr,hu,ie,it,lv,lt,lu,mt,nl,pl,pt,ro,sk,si,es,se';
export const COUNTRY_CODES:Record<string,string>={USA:'us',CAN:'ca',SRB:'rs',EU:EU,Europe:EU};

let nextSlot=0;
const sleep=(ms:number)=>new Promise<void>(r=>setTimeout(r,ms));
// Nominatim policy: at most 1 request per second. Space requests out on this server instance;
// if the queue is already more than 8 seconds long, give up so callers fall back instead of hanging.
async function gate(){const now=Date.now();const start=Math.max(now,nextSlot);if(start-now>8000)throw new Error('busy');nextSlot=start+1100;if(start>now)await sleep(start-now)}

async function nominatim(path:string,params:URLSearchParams,timeoutMs:number){await gate();
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

// Address type-ahead limited to one country, from Photon (OpenStreetMap data, built for search-as-you-type).
// Results are cached briefly per query so typing does not repeat requests.
export type Suggestion={label:string,lat:number,lng:number,street:string,city:string};
const suggestCache=new Map<string,{at:number,rows:Suggestion[]}>();
export async function suggestAddresses(q:string,opts:{country:string,bbox:[number,number,number,number],lang?:string,nearLat?:number,nearLng?:number}):Promise<Suggestion[]>{
 const key=[opts.country,opts.lang||'',q.toLowerCase(),opts.nearLat?.toFixed(2)||'',opts.nearLng?.toFixed(2)||''].join('|');
 const hit=suggestCache.get(key);if(hit&&Date.now()-hit.at<10*60_000)return hit.rows;
 const p=new URLSearchParams({q,limit:'12',bbox:opts.bbox.join(',')});
 if(opts.lang&&['en','fr','de','it'].includes(opts.lang))p.set('lang',opts.lang);
 if(typeof opts.nearLat==='number'&&typeof opts.nearLng==='number'){p.set('lat',String(opts.nearLat));p.set('lon',String(opts.nearLng))}
 const ctl=new AbortController();const timer=setTimeout(()=>ctl.abort(),5000);
 let r:Response;
 try{r=await fetch('https://photon.komoot.io/api/?'+p.toString(),{headers:{'User-Agent':UA},cache:'no-store',signal:ctl.signal})}finally{clearTimeout(timer)}
 if(!r.ok)throw new Error('unavailable');
 const d:any=await r.json();
 const want=opts.country.toUpperCase();
 const rows:Suggestion[]=[];const seen=new Set<string>();
 for(const f of d?.features||[]){
  const pr=f?.properties||{};const [lng,lat]=f?.geometry?.coordinates||[];
  if(String(pr.countrycode||'').toUpperCase()!==want||!Number.isFinite(lat)||!Number.isFinite(lng))continue;
  const street=String(pr.street||(pr.osm_key==='highway'?pr.name:'')||'');
  const line1=pr.housenumber&&street?(want==='RS'?street+' '+pr.housenumber:pr.housenumber+' '+street):(pr.name&&pr.name!==street?[pr.name,street].filter(Boolean).join(', '):street||pr.name||'');
  const city=String(pr.city||pr.town||pr.village||pr.district||pr.county||'');
  const line2=[pr.postcode,city].filter(Boolean).join(' ');
  const label=[line1,line2,want==='CA'?pr.state:''].filter(Boolean).join(', ');
  if(!label||seen.has(label))continue;seen.add(label);
  rows.push({label:label.slice(0,200),lat,lng,street:street.slice(0,150),city:city.slice(0,100)});
  if(rows.length>=6)break;
 }
 if(suggestCache.size>500)suggestCache.clear();
 suggestCache.set(key,{at:Date.now(),rows});
 return rows;
}
