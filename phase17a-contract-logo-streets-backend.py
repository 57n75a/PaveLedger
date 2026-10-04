import pathlib, re
from datetime import date

VERSION = "2.7.0"
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

D = 'lib/domain.ts'
A = 'lib/actions.ts'

# ---------- 1. Contract type: logo + additionalRoads ----------
replace_once(D,
    "contracts:{id:string,contractor:string,road:string,scope:string,start:string,end:string,poc:string,email:string,notes?:string,phone?:string,address?:string,addressCountry?:string,scopeLat?:number|null,scopeLng?:number|null,scopeRadius?:number|null,documents?:{id:string,name:string,mime:string,bytes:number,uploadedAt:string,uploadedBy:string}[]}[]",
    "contracts:{id:string,contractor:string,road:string,scope:string,start:string,end:string,poc:string,email:string,notes?:string,phone?:string,address?:string,addressCountry?:string,logo?:string,additionalRoads?:string[],scopeLat?:number|null,scopeLng?:number|null,scopeRadius?:number|null,documents?:{id:string,name:string,mime:string,bytes:number,uploadedAt:string,uploadedBy:string}[]}[]",
    "domain.ts: Contract gets logo and additionalRoads")

# ---------- 2. contractCovers also checks additionalRoads ----------
replace_once(D,
    "export function contractCovers(c:{road:string,scopeLat?:number|null,scopeLng?:number|null,scopeRadius?:number|null},t:{road:string,lat:number,lng:number}){if(typeof c.scopeLat==='number'&&typeof c.scopeLng==='number'&&typeof c.scopeRadius==='number')return distanceMeters({lat:c.scopeLat,lng:c.scopeLng},t)<=c.scopeRadius;return normRoad(c.road)===normRoad(t.road)}",
    "export function contractCovers(c:{road:string,additionalRoads?:string[],scopeLat?:number|null,scopeLng?:number|null,scopeRadius?:number|null},t:{road:string,lat:number,lng:number}){if(typeof c.scopeLat==='number'&&typeof c.scopeLng==='number'&&typeof c.scopeRadius==='number')return distanceMeters({lat:c.scopeLat,lng:c.scopeLng},t)<=c.scopeRadius;if(normRoad(c.road)===normRoad(t.road))return true;return (c.additionalRoads||[]).some(r=>normRoad(r)===normRoad(t.road))}",
    "domain.ts: contractCovers checks additionalRoads too")

# ---------- 3. 'contract' create: schema + logo handling ----------
replace_once(A,
    "const v=z.object({contractor:short,road:short,scope:z.string().trim().max(2000).optional().transform(x=>x?.trim()||''),start:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),end:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),poc:short,email:z.string().trim().email().max(250),scopeLat:optCoord(-90,90),scopeLng:optCoord(-180,180),scopeRadius:optCoord(50,50000),phone:z.string().max(40).optional().transform(x=>x?.trim()||''),address:z.string().max(300).optional().transform(x=>x?.trim()||''),addressCountry:z.string().max(50).optional().transform(x=>x?.trim()||'')}).parse(body);",
    "const v=z.object({contractor:short,road:short,scope:z.string().trim().max(2000).optional().transform(x=>x?.trim()||''),start:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),end:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),poc:short,email:z.string().trim().email().max(250),scopeLat:optCoord(-90,90),scopeLng:optCoord(-180,180),scopeRadius:optCoord(50,50000),phone:z.string().max(40).optional().transform(x=>x?.trim()||''),address:z.string().max(300).optional().transform(x=>x?.trim()||''),addressCountry:z.string().max(50).optional().transform(x=>x?.trim()||''),additionalRoads:z.string().max(1000).optional().transform(x=>(x||'').split(/[\\n,]/).map(s=>s.trim()).filter(Boolean))}).parse(body);",
    "actions.ts: contract create schema accepts additionalRoads")

replace_once(A,
    "const id='CT-'+crypto.randomUUID().slice(0,8).toUpperCase();s.contracts.push({...v,id});event='Contract registered: '+id;",
    "const id='CT-'+crypto.randomUUID().slice(0,8).toUpperCase();const newLogo=typeof body.logo==='string'&&body.logo?body.logo:undefined;if(newLogo&&newLogo.length>700_000)throw new AppError('Logo is too large. Use an image under 500 KB.');s.contracts.push({...v,id,...(newLogo?{logo:newLogo}:{})});event='Contract registered: '+id;",
    "actions.ts: contract create saves logo")

# ---------- 4. 'contractUpdate': schema + logo handling ----------
replace_once(A,
    "const v=z.object({contractor:short,road:short,scope:z.string().trim().max(2000).optional().transform(x=>x?.trim()||''),start:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),end:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),poc:short,email:z.string().trim().email().max(250),notes:z.string().max(4000).optional().transform(x=>x?.trim()||''),scopeLat:optCoord(-90,90),scopeLng:optCoord(-180,180),scopeRadius:optCoord(50,50000),phone:z.string().max(40).optional().transform(x=>x?.trim()||''),address:z.string().max(300).optional().transform(x=>x?.trim()||''),addressCountry:z.string().max(50).optional().transform(x=>x?.trim()||'')}).parse(body);",
    "const v=z.object({contractor:short,road:short,scope:z.string().trim().max(2000).optional().transform(x=>x?.trim()||''),start:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),end:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),poc:short,email:z.string().trim().email().max(250),notes:z.string().max(4000).optional().transform(x=>x?.trim()||''),scopeLat:optCoord(-90,90),scopeLng:optCoord(-180,180),scopeRadius:optCoord(50,50000),phone:z.string().max(40).optional().transform(x=>x?.trim()||''),address:z.string().max(300).optional().transform(x=>x?.trim()||''),addressCountry:z.string().max(50).optional().transform(x=>x?.trim()||''),additionalRoads:z.string().max(1000).optional().transform(x=>(x||'').split(/[\\n,]/).map(s=>s.trim()).filter(Boolean))}).parse(body);",
    "actions.ts: contractUpdate schema accepts additionalRoads")

replace_once(A,
    "if(v.end<v.start||[v.start,v.end].some(x=>!Number.isFinite(Date.parse(x))||new Date(x).toISOString().slice(0,10)!==x))throw new AppError('Enter valid warranty start and end dates.');\n  Object.assign(existing,v);\n  const linkIds=",
    "if(v.end<v.start||[v.start,v.end].some(x=>!Number.isFinite(Date.parse(x))||new Date(x).toISOString().slice(0,10)!==x))throw new AppError('Enter valid warranty start and end dates.');\n  const updatedLogo=typeof body.logo==='string'&&body.logo?body.logo:undefined;\n  if(updatedLogo&&updatedLogo.length>700_000)throw new AppError('Logo is too large. Use an image under 500 KB.');\n  Object.assign(existing,v,updatedLogo?{logo:updatedLogo}:{});\n  const linkIds=",
    "actions.ts: contractUpdate saves logo")

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
- Contracts can now have a company logo (inline, under 500 KB) and additional streets covered beyond the primary road
- contractCovers now matches a ticket's road against any additional street listed, not just the primary one
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nRun the frontend script next, then build once.")
