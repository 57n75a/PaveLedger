import pathlib, re
from datetime import date

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

VERSION = "2.3.1"
TODAY = date.today().isoformat()

# ---------- 1. Import useRef (needed for road -> coordinates autofill) ----------
replace_once('app/workspace.tsx',
    "import React,{useEffect,useState} from 'react';",
    "import React,{useEffect,useState,useRef} from 'react';",
    "workspace.tsx: import useRef")

# ---------- 2. Detail hero: always the map, drop the photo/logo hero entirely ----------
replace_once('app/workspace.tsx',
    "const [photoUrl,setPhotoUrl]=useState<string|null>(null);\nuseEffect(()=>{let active=true;const first=(t.evidence||[])[0];if(!first){setPhotoUrl(null);return}authorizedFetch('/api/evidence?ticket='+encodeURIComponent(t.id)+'&id='+encodeURIComponent(first.id)+(persona==='owner'?'':'&persona='+encodeURIComponent(persona))).then(r=>r.json()).then(d=>{if(active)setPhotoUrl(d.url||null)}).catch(()=>{if(active)setPhotoUrl(null)});return()=>{active=false}},[t.id,t.evidence,persona]);\nconst [contractorPick,setContractorPick]=useState('none');",
    "const [contractorPick,setContractorPick]=useState('none');",
    "workspace.tsx: Detail drops the photo-hero state (map is now unconditional)")

replace_once('app/workspace.tsx',
    '''<div className="evidence">{photoUrl?<img src={photoUrl} alt="Reported photograph" style={{width:'100%',maxHeight:280,objectFit:'cover'}}/>:<iframe title="Ticket location" src={`https://www.google.com/maps?q=${t.lat},${t.lng}&z=16&output=embed`} style={{width:'100%',height:280,border:0}} loading="lazy"/>}{!photoUrl&&<span>Showing reported location \u2014 no photograph uploaded yet</span>}</div>''',
    '''<div className="evidence"><iframe title="Ticket location" src={`https://www.google.com/maps?q=${t.lat},${t.lng}&z=16&output=embed`} style={{width:'100%',height:280,border:0}} loading="lazy"/><span>Map centered on the reported location \u2014 photos are below under Uploaded case evidence</span></div>''',
    "workspace.tsx: Detail hero is always the location map")

# ---------- 3. HeroTicket (Overview): always the map, drop photo fetch ----------
replace_once('app/workspace.tsx',
    '''function HeroTicket({ticket,persona,onOpen}:{ticket:Ticket|undefined,persona:string,onOpen:()=>void}){
 const [url,setUrl]=useState<string|null>(null);
 useEffect(()=>{let active=true;const first=(ticket?.evidence||[])[0];if(!ticket||!first){setUrl(null);return}authorizedFetch('/api/evidence?ticket='+encodeURIComponent(ticket.id)+'&id='+encodeURIComponent(first.id)+(persona==='owner'?'':'&persona='+encodeURIComponent(persona))).then(r=>r.json()).then(d=>{if(active)setUrl(d.url||null)}).catch(()=>{if(active)setUrl(null)});return()=>{active=false}},[ticket?.id,persona]);
 if(!ticket)return <section className="feature-card"><div className="image-wrap"><img src="/logo.png" alt="PaveLedger" style={{objectFit:'contain',padding:24,background:'#f4f6f8'}}/><span className="image-label">NO ACTIVE CASES</span></div><div className="feature-content"><p className="eyebrow">ALL CLEAR</p><h2>Nothing needs attention right now.</h2><p>New tickets will appear here as they come in.</p></div></section>;
 return <section className="feature-card"><div className="image-wrap">{url?<img src={url} alt="Top priority case photograph" style={{objectFit:'cover',width:'100%',height:'100%'}}/>:<iframe title="Top priority case location" src={`https://www.google.com/maps?q=${ticket.lat},${ticket.lng}&z=16&output=embed`} style={{width:'100%',height:'100%',border:0}} loading="lazy"/>}<span className="image-label">TOP PRIORITY CASE</span></div>''',
    '''function HeroTicket({ticket,onOpen}:{ticket:Ticket|undefined,onOpen:()=>void}){
 if(!ticket)return <section className="feature-card"><div className="image-wrap"><img src="/logo.png" alt="PaveLedger" style={{objectFit:'contain',padding:24,background:'#f4f6f8'}}/><span className="image-label">NO ACTIVE CASES</span></div><div className="feature-content"><p className="eyebrow">ALL CLEAR</p><h2>Nothing needs attention right now.</h2><p>New tickets will appear here as they come in.</p></div></section>;
 return <section className="feature-card"><div className="image-wrap"><iframe title="Top priority case location" src={`https://www.google.com/maps?q=${ticket.lat},${ticket.lng}&z=16&output=embed`} style={{width:'100%',height:'100%',border:0}} loading="lazy"/><span className="image-label">TOP PRIORITY CASE</span></div>''',
    "workspace.tsx: HeroTicket is always the location map")

replace_once('app/workspace.tsx',
    "<HeroTicket ticket={topTicket} persona={persona} onOpen={()=>topTicket&&setSelected(topTicket.id)}/>",
    "<HeroTicket ticket={topTicket} onOpen={()=>topTicket&&setSelected(topTicket.id)}/>",
    "workspace.tsx: HeroTicket call site drops persona prop")

# ---------- 4. EvidencePanel: real thumbnails instead of filename-only buttons ----------
replace_once('app/workspace.tsx',
    '''const [uploading,setUploading]=useState(false),[error,setError]=useState('');const suffix=persona==='owner'?'':'?persona='+encodeURIComponent(persona);
async function openFile(id:string){''',
    '''const [uploading,setUploading]=useState(false),[error,setError]=useState('');const suffix=persona==='owner'?'':'?persona='+encodeURIComponent(persona);
const [thumbs,setThumbs]=useState<Record<string,string>>({});
useEffect(()=>{let active=true;authorizedFetch('/api/evidence-urls?ticket='+encodeURIComponent(t.id)+(persona==='owner'?'':'&persona='+encodeURIComponent(persona))).then(r=>r.json()).then(d=>{if(active&&d.urls)setThumbs(d.urls)}).catch(()=>{});return()=>{active=false}},[t.id,(t.evidence||[]).length,persona]);
async function openFile(id:string){''',
    "workspace.tsx: EvidencePanel fetches thumbnail URLs")

replace_once('app/workspace.tsx',
    '''{(t.evidence||[]).map(e=><div className="evidence-row" key={e.id}><button className="text-button" onClick={()=>openFile(e.id)}>{e.name}</button><small>{e.purpose} \u00b7 {e.quality} \u00b7 {e.lane} \u00b7 \u00b1{e.accuracy} m</small><small>{new Date(e.capturedAt).toLocaleString()}</small></div>)}''',
    '''{(t.evidence||[]).map(e=><div className="evidence-row" key={e.id} style={{display:'flex',alignItems:'center',gap:12}}><button onClick={()=>openFile(e.id)} title="Open full image" style={{padding:0,border:'1px solid #e5e7eb',borderRadius:6,cursor:'pointer',background:'none',flexShrink:0}}>{thumbs[e.id]?<img src={thumbs[e.id]} alt={e.name} style={{width:64,height:64,objectFit:'cover',borderRadius:5,display:'block'}}/>:<div style={{width:64,height:64,borderRadius:5,background:'#f0f1f3'}}/>}</button><div><button className="text-button" onClick={()=>openFile(e.id)}>{e.name}</button><small className="block muted">{e.purpose} \u00b7 {e.quality} \u00b7 {e.lane} \u00b7 \u00b1{e.accuracy} m</small><small className="block muted">{new Date(e.capturedAt).toLocaleString()}</small></div></div>)}''',
    "workspace.tsx: evidence rows show clickable thumbnails")

# ---------- 5. Manual ticket creation: road -> lat/lng autofill ----------
replace_once('app/workspace.tsx',
    '''<label>Road<input required name="road" defaultValue="King Street East"/></label>''',
    '''<label>Road<input required name="road" ref={createRoadRef} onBlur={async()=>{const road=createRoadRef.current?.value.trim();if(!road||road.length<3)return;try{const r=await authorizedFetch('/api/geocode?q='+encodeURIComponent(road));const d=await r.json();if(r.ok&&createLatRef.current&&createLngRef.current){createLatRef.current.value=String(d.lat);createLngRef.current.value=String(d.lng)}}catch{}}} defaultValue="King Street East"/></label>''',
    "workspace.tsx: road field triggers geocode on blur")

replace_once('app/workspace.tsx',
    '''<label>Latitude<input required name="lat" type="number" step="any" min="-90" max="90" defaultValue="43.3605"/></label><label>Longitude<input required name="lng" type="number" step="any" min="-180" max="180" defaultValue="-80.314"/></label>''',
    '''<label>Latitude<input required name="lat" ref={createLatRef} type="number" step="any" min="-90" max="90" defaultValue="43.3605"/></label><label>Longitude<input required name="lng" ref={createLngRef} type="number" step="any" min="-180" max="180" defaultValue="-80.314"/></label>''',
    "workspace.tsx: lat/lng fields are ref-addressable for autofill")

replace_once('app/workspace.tsx',
    "[editingContract,setEditingContract]=useState<any>(null),[editingTeam,setEditingTeam]=useState<string|null>(null),[managingTeam,setManagingTeam]=useState<string|null>(null);",
    "[editingContract,setEditingContract]=useState<any>(null),[editingTeam,setEditingTeam]=useState<string|null>(null),[managingTeam,setManagingTeam]=useState<string|null>(null);\nconst createRoadRef=useRef<HTMLInputElement>(null),createLatRef=useRef<HTMLInputElement>(null),createLngRef=useRef<HTMLInputElement>(null);",
    "workspace.tsx: refs for the manual-create road/lat/lng fields")

# ---------- 6. Country list: USA, Canada, Serbia, EU (both contract dialogs) ----------
OLD_COUNTRIES = '''<select name="addressCountry" defaultValue="USA"><option value="USA">USA</option><option value="CAN">Canada</option><option value="Europe">Europe</option></select>'''
NEW_COUNTRIES = '''<select name="addressCountry" defaultValue="USA"><option value="USA">USA</option><option value="CAN">Canada</option><option value="SRB">Serbia</option><option value="EU">EU</option></select>'''
replace_once('app/workspace.tsx', OLD_COUNTRIES, NEW_COUNTRIES, "workspace.tsx: contract create dialog country list")

OLD_COUNTRIES_EDIT = '''<select name="addressCountry" defaultValue={editingContract.addressCountry||'USA'}><option value="USA">USA</option><option value="CAN">Canada</option><option value="Europe">Europe</option></select>'''
NEW_COUNTRIES_EDIT = '''<select name="addressCountry" defaultValue={editingContract.addressCountry==='Europe'?'EU':(editingContract.addressCountry||'USA')}><option value="USA">USA</option><option value="CAN">Canada</option><option value="SRB">Serbia</option><option value="EU">EU</option></select>'''
replace_once('app/workspace.tsx', OLD_COUNTRIES_EDIT, NEW_COUNTRIES_EDIT, "workspace.tsx: contract edit dialog country list (maps old Europe value to EU)")

# ---------- version + changelog ----------
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
- Every ticket's hero is now a live map centered on its coordinates (Overview and the individual ticket page); reported photos appear as thumbnails below instead
- Evidence photos now show as real clickable thumbnails linking to the full image, instead of a filename-only button
- Manually creating a ticket now looks up latitude/longitude automatically once you finish typing the road
- Contract address country list is now USA, Canada, Serbia, EU
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Now run:")
print("  npm run build")
