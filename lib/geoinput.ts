// Helpers for entering locations the way people copy them from Google Maps. Pure functions, no dependencies.
const num=(s:string)=>Number(s);
const round=(n:number)=>Math.round(n*1e6)/1e6;
const done=(lat:number,lng:number)=>Number.isFinite(lat)&&Number.isFinite(lng)&&Math.abs(lat)<=90&&Math.abs(lng)<=180?{lat:round(lat),lng:round(lng)}:null;

// Accepts: "43.360500, -80.314000" (Google Maps), "43.3605 -80.314", degrees/minutes/seconds such as 43°21'37.8"N 80°18'50.4"W,
// decimals with N/S/E/W letters, and Google Maps links (@lat,lng, !3d..!4d.., ?q=lat,lng). Latitude comes first unless letters say otherwise.
export function parseCoordinates(input:string):{lat:number,lng:number}|null{
 const text=(input||'').trim();
 if(!text)return null;
 if(/^https?:\/\//i.test(text)||/google\.[a-z.]+\/maps|maps\.app\.goo\.gl|goo\.gl\/maps/i.test(text)){
  let decoded=text;try{decoded=decodeURIComponent(text)}catch{/* keep the raw text */}
  const m=decoded.match(/!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)/)
   ||decoded.match(/@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)/)
   ||decoded.match(/[?&](?:q|ll|query|center|destination)=(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)/);
  return m?done(num(m[1]),num(m[2])):null;
 }
 const dms=[...text.matchAll(/(\d{1,3})\s*[°º]\s*(\d{1,2})\s*['′’]\s*(\d{1,2}(?:\.\d+)?)\s*(?:["″”]|'')?\s*([NSEW])/gi)];
 if(dms.length===2){
  const val=(g:RegExpMatchArray)=>{const v=num(g[1])+num(g[2])/60+num(g[3])/3600;return /[SW]/i.test(g[4])?-v:v};
  const ha=dms[0][4].toUpperCase(),hb=dms[1][4].toUpperCase();
  if('NS'.includes(ha)&&'EW'.includes(hb))return done(val(dms[0]),val(dms[1]));
  if('EW'.includes(ha)&&'NS'.includes(hb))return done(val(dms[1]),val(dms[0]));
  return null;
 }
 const hemi=[...text.matchAll(/(?:([NSEW])\s*(\d{1,3}(?:\.\d+)?)\s*°?|(\d{1,3}(?:\.\d+)?)\s*°?\s*([NSEW]))/gi)];
 if(hemi.length===2){
  const read=(g:RegExpMatchArray)=>{const letter=(g[1]||g[4]).toUpperCase();const v=num(g[2]||g[3]);return {letter,v:/[SW]/.test(letter)?-v:v}};
  const a=read(hemi[0]),b=read(hemi[1]);
  if('NS'.includes(a.letter)&&'EW'.includes(b.letter))return done(a.v,b.v);
  if('EW'.includes(a.letter)&&'NS'.includes(b.letter))return done(b.v,a.v);
  return null;
 }
 const plain=text.replace(/^[\s(\[]+|[\s)\]]+$/g,'').match(/^(-?\d+(?:\.\d+)?)\s*(?:,|;|\s)\s*(-?\d+(?:\.\d+)?)$/);
 return plain?done(num(plain[1]),num(plain[2])):null;
}

// "43.360500, -80.314000": the format Google Maps shows and accepts.
export const formatCoordinates=(lat:number,lng:number)=>lat.toFixed(6)+', '+lng.toFixed(6);
export const mapsLink=(lat:number,lng:number)=>'https://www.google.com/maps?q='+lat+','+lng;

// Best guess at the street name from a full address, to pre-fill the road field:
// "123 King Street East, Waterloo" -> "King Street East"; "Knez Mihailova 12, Beograd" -> "Knez Mihailova".
export function streetFromAddress(address:string):string{
 const parts=(address||'').split(',').map(p=>p.trim()).filter(Boolean);
 let seg=parts.find(p=>!/^(unit|suite|ste|apt|apartment|room|floor|#)\s*[\w-]+$/i.test(p))||'';
 if(!seg)return '';
 const lead=/^\d+[A-Za-z]?(?:\s*[-–/]\s*\d+[A-Za-z]?)?\s+/;
 const trail=/\s+\d+[A-Za-z]?(?:\s*[-–/]\s*\d+[A-Za-z]?)?$/;
 const stripped=lead.test(seg)?seg.replace(lead,''):seg.replace(trail,'');
 return (stripped||seg).trim();
}
