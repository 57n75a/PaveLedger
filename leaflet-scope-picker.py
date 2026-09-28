import pathlib, re, subprocess, sys
from datetime import date

VERSION = "2.2.2"
TODAY = date.today().isoformat()

def replace_once(path, old, new, label):
    p = pathlib.Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        print(f"SKIP ({count} matches, expected 1): {label} in {path}")
        return False
    p.write_text(text.replace(old, new, 1))
    print(f"OK: {label}")
    return True

# ============================================================
# 0. Preflight: does a Content-Security-Policy exist that could block map tiles / the Google embed?
# ============================================================
print("== Preflight: checking for a Content-Security-Policy ==")
csp_found = False
for name in ['next.config.ts', 'next.config.mjs', 'next.config.js', 'vercel.json', 'middleware.ts', 'proxy.ts']:
    p = pathlib.Path(name)
    if not p.exists():
        continue
    text = p.read_text()
    if re.search(r'content-security-policy', text, re.I):
        csp_found = True
        print(f"  WARNING: {name} sets a Content-Security-Policy. Relevant lines:")
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(r'(security-policy|img-src|frame-src|connect-src|default-src)', line, re.I):
                print(f"    {name}:{i}: {line.strip()[:240]}")
if csp_found:
    print("  -> If img-src or frame-src are restricted, allow https://tile.openstreetmap.org in img-src")
    print("     and https://www.google.com in frame-src, otherwise the maps will appear blank.")
else:
    print("  OK: no Content-Security-Policy found in the usual config files.")

# ============================================================
# 1. Install Leaflet (pinned to the stable 1.9 line)
# ============================================================
print("\n== Installing Leaflet (free, open-source, no API key) ==")
for cmd in (['npm', 'install', 'leaflet@1.9.4'], ['npm', 'install', '-D', '@types/leaflet@1.9']):
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        print(f"ERROR: '{' '.join(cmd)}' failed (exit {rc}). No source files were changed.")
        print("Check that Node 22 is active (nvm use 22), then re-run this script.")
        sys.exit(1)

# ============================================================
# 2. New file: app/api/geocode/route.ts (server-side address lookup, Admin only)
# ============================================================
route_code = """import {context,failure} from '@/lib/context';
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
"""
rp = pathlib.Path('app/api/geocode/route.ts')
rp.parent.mkdir(parents=True, exist_ok=True)
if rp.exists():
    print(f"SKIP: {rp} already exists")
else:
    rp.write_text(route_code, encoding='utf-8')
    print(f"OK: created {rp}")

# ============================================================
# 3. New file: components/scope-locator.tsx (client-only map + radius picker)
# ============================================================
component_code = """'use client';
import {useEffect,useRef,useState} from 'react';
import 'leaflet/dist/leaflet.css';
import {authorizedFetch} from '@/lib/supabase-browser';
import {toast} from 'sonner';

type Scope={lat:number,lng:number,radius:number}|null;
const DEFAULT_RADIUS=500;
const fmt=(m:number)=>m>=1000?(m/1000).toFixed(1)+' km':Math.round(m)+' m';

export default function ScopeLocator({initialLat,initialLng,initialRadius}:{initialLat?:number,initialLng?:number,initialRadius?:number}){
 const box=useRef<HTMLDivElement>(null);
 const lib=useRef<any>(null),map=useRef<any>(null),marker=useRef<any>(null),circle=useRef<any>(null),observer=useRef<ResizeObserver|null>(null);
 const [ready,setReady]=useState(false),[busy,setBusy]=useState(false);
 const [scope,setScope]=useState<Scope>(typeof initialLat==='number'&&typeof initialLng==='number'?{lat:initialLat,lng:initialLng,radius:typeof initialRadius==='number'&&initialRadius>0?initialRadius:DEFAULT_RADIUS}:null);
 const latest=useRef<Scope>(scope);
 latest.current=scope;

 // Create the map once, on the client only.
 useEffect(()=>{
  let dead=false;
  (async()=>{
   const mod:any=await import('leaflet');
   const L:any=mod.default||mod;
   if(dead||!box.current)return;
   lib.current=L;
   const start=latest.current;
   const m=L.map(box.current,{scrollWheelZoom:false}).setView(start?[start.lat,start.lng]:[39.5,-40],start?14:2);
   L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}).addTo(m);
   m.on('click',(e:any)=>setScope({lat:e.latlng.lat,lng:e.latlng.lng,radius:latest.current?.radius||DEFAULT_RADIUS}));
   map.current=m;
   observer.current=new ResizeObserver(()=>m.invalidateSize());
   observer.current.observe(box.current);
   setTimeout(()=>{if(map.current)map.current.invalidateSize()},300);
   setReady(true);
  })();
  return()=>{
   dead=true;
   observer.current?.disconnect();observer.current=null;
   if(map.current){map.current.remove();map.current=null}
   marker.current=null;circle.current=null;lib.current=null;
  };
 },[]);

 // Draw or update the pin and radius circle whenever the scope changes.
 useEffect(()=>{
  const L=lib.current,m=map.current;
  if(!ready||!L||!m)return;
  if(!scope){
   if(marker.current){m.removeLayer(marker.current);marker.current=null}
   if(circle.current){m.removeLayer(circle.current);circle.current=null}
   return;
  }
  const pos:[number,number]=[scope.lat,scope.lng];
  if(!circle.current){circle.current=L.circle(pos,{radius:scope.radius,color:'#c32643',weight:2,fillOpacity:0.12}).addTo(m)}
  else{circle.current.setLatLng(pos);circle.current.setRadius(scope.radius)}
  if(!marker.current){
   marker.current=L.marker(pos,{draggable:true,icon:L.divIcon({className:'',html:'<div style="width:18px;height:18px;border-radius:50%;background:#c32643;border:3px solid #fff;box-shadow:0 0 0 1px #c32643"></div>',iconSize:[18,18],iconAnchor:[9,9]})}).addTo(m);
   marker.current.on('dragend',()=>{const p=marker.current.getLatLng();setScope({lat:p.lat,lng:p.lng,radius:latest.current?.radius||DEFAULT_RADIUS})});
  }else marker.current.setLatLng(pos);
  m.fitBounds(circle.current.getBounds(),{padding:[20,20],maxZoom:17});
 },[scope,ready]);

 async function locate(btn:HTMLButtonElement){
  const form=btn.form;
  if(!form)return;
  const fd=new FormData(form);
  const q=String(fd.get('address')||'').trim();
  const country=String(fd.get('addressCountry')||'USA');
  if(!q){toast.error('Enter an address first');return}
  setBusy(true);
  try{
   const r=await authorizedFetch('/api/geocode?q='+encodeURIComponent(q)+'&country='+encodeURIComponent(country));
   const d=await r.json();
   if(!r.ok)throw new Error(d.error);
   setScope({lat:d.lat,lng:d.lng,radius:latest.current?.radius||DEFAULT_RADIUS});
   toast.success('Address located');
  }catch(e){toast.error((e as Error).message)}
  finally{setBusy(false)}
 }

 return <div className="form">
  <p className="footnote">Coverage area (optional): locate the address, then drag the pin or click the map to fine-tune, and set the radius this contract covers.</p>
  <button type="button" className="secondary" disabled={busy} onClick={e=>locate(e.currentTarget)}>{busy?'Locating...':'Locate address on map'}</button>
  <div ref={box} style={{height:260,width:'100%',borderRadius:8,overflow:'hidden',border:'1px solid #e5e7eb',isolation:'isolate'}}/>
  {scope?<>
   <label>Scope radius: {fmt(scope.radius)}<input type="range" min={100} max={10000} step={50} value={Math.min(10000,Math.max(100,scope.radius))} onChange={e=>setScope({...scope,radius:Number(e.target.value)})}/></label>
   <input type="hidden" name="scopeLat" value={scope.lat.toFixed(6)}/>
   <input type="hidden" name="scopeLng" value={scope.lng.toFixed(6)}/>
   <input type="hidden" name="scopeRadius" value={Math.round(scope.radius)}/>
   <button type="button" className="text-button" onClick={()=>setScope(null)}>Clear scope area</button>
  </>:<p className="footnote">No scope area set.</p>}
 </div>;
}
"""
cp = pathlib.Path('components/scope-locator.tsx')
if cp.exists():
    print(f"SKIP: {cp} already exists")
else:
    cp.write_text(component_code, encoding='utf-8')
    print(f"OK: created {cp}")

# ============================================================
# 4. lib/domain.ts: allow null for cleared scope values
# ============================================================
replace_once('lib/domain.ts',
    "scopeLat?:number,scopeLng?:number,scopeRadius?:number,",
    "scopeLat?:number|null,scopeLng?:number|null,scopeRadius?:number|null,",
    "domain.ts: scope fields may be null (cleared)")

# ============================================================
# 5. lib/actions.ts: accept and validate scope coordinates
# ============================================================
replace_once('lib/actions.ts',
    "const short=z.string().trim().min(1).max(150),noteField=z.string().trim().min(10).max(2000);",
    "const short=z.string().trim().min(1).max(150),noteField=z.string().trim().min(10).max(2000);\nconst optCoord=(min:number,max:number)=>z.preprocess(x=>x===''||x==null?null:Number(x),z.number().min(min).max(max).nullable());",
    "actions.ts: optCoord helper")

replace_once('lib/actions.ts',
    "poc:short,email:z.string().trim().email().max(250),phone:",
    "poc:short,email:z.string().trim().email().max(250),scopeLat:optCoord(-90,90),scopeLng:optCoord(-180,180),scopeRadius:optCoord(50,50000),phone:",
    "actions.ts: contract create accepts scope area")

replace_once('lib/actions.ts',
    "notes:z.string().max(4000).optional().transform(x=>x?.trim()||''),phone:",
    "notes:z.string().max(4000).optional().transform(x=>x?.trim()||''),scopeLat:optCoord(-90,90),scopeLng:optCoord(-180,180),scopeRadius:optCoord(50,50000),phone:",
    "actions.ts: contract update accepts scope area")

# ============================================================
# 6. app/workspace.tsx: dynamic import, forms, and contract card display
# ============================================================
replace_once('app/workspace.tsx',
    "import {APP_VERSION} from '@/lib/version';",
    "import {APP_VERSION} from '@/lib/version';\nimport dynamic from 'next/dynamic';\nconst ScopeLocator=dynamic(()=>import('@/components/scope-locator'),{ssr:false,loading:()=><p className=\"muted\">Loading map...</p>});",
    "workspace.tsx: load ScopeLocator client-side only")

replace_once('app/workspace.tsx',
    '''<option value="Europe">Europe</option></select></label><div className="two-cols"><label>Warranty begins<input name="start" type="date" required/>''',
    '''<option value="Europe">Europe</option></select></label><ScopeLocator/><div className="two-cols"><label>Warranty begins<input name="start" type="date" required/>''',
    "workspace.tsx: scope picker in contract create dialog")

replace_once('app/workspace.tsx',
    '''<option value="Europe">Europe</option></select></label><div className="two-cols"><label>Warranty begins<input name="start" type="date" required defaultValue={editingContract.start}/>''',
    '''<option value="Europe">Europe</option></select></label><ScopeLocator key={editingContract.id} initialLat={editingContract.scopeLat??undefined} initialLng={editingContract.scopeLng??undefined} initialRadius={editingContract.scopeRadius??undefined}/><div className="two-cols"><label>Warranty begins<input name="start" type="date" required defaultValue={editingContract.start}/>''',
    "workspace.tsx: scope picker in contract edit dialog")

replace_once('app/workspace.tsx',
    '''<div><dt>Contact email</dt><dd>{c.email}</dd></div></dl>''',
    '''<div><dt>Contact email</dt><dd>{c.email}</dd></div><div><dt>Phone</dt><dd>{c.phone||'Not provided'}</dd></div>{c.address&&<div><dt>Address</dt><dd>{c.address}{c.addressCountry?' ('+c.addressCountry+')':''}</dd></div>}</dl>{typeof c.scopeLat==='number'&&typeof c.scopeLng==='number'&&<p className="footnote">Scope area: {c.scopeRadius||500} m radius \\u00b7 <a href={'https://www.google.com/maps?q='+c.scopeLat+','+c.scopeLng} target="_blank" rel="noopener noreferrer">Open in Google Maps</a></p>}''',
    "workspace.tsx: contract cards show phone, address, and scope area")

# ============================================================
# 7. Version + changelog
# ============================================================
version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

pkg = pathlib.Path('package.json')
new_pkg, n = re.subn(r'"version":\s*"[^"]*"', f'"version": "{VERSION}"', pkg.read_text(), count=1)
if n == 1:
    pkg.write_text(new_pkg)
    print(f"OK: package.json version set to {VERSION}")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Contracts can now define a scope area: locate the address on a map, drag the pin, and set a coverage radius (Leaflet + OpenStreetMap, no API key)
- Added a server-side address lookup limited to the selected region (USA, Canada, Europe), Admin only
- Contract cards now show phone, address, and scope area with an Open in Google Maps link
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Now run:")
print("  npm run build")
