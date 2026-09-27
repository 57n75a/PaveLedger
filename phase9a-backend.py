import pathlib
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

VERSION = "2.1.7"
TODAY = date.today().isoformat()

# ---------- lib/domain.ts ----------

replace_once('lib/domain.ts',
    "vehicleTag?:string;notifyPrefs?:Record<string,boolean>;active?:boolean;authUserId?:string;demo?:boolean};",
    "vehicleTag?:string;notifyPrefs?:Record<string,boolean>;phone?:string;active?:boolean;authUserId?:string;demo?:boolean};",
    "domain.ts: add phone to Member type")

replace_once('lib/domain.ts',
    "contracts:{id:string,contractor:string,road:string,scope:string,start:string,end:string,poc:string,email:string,notes?:string,documents?:{id:string,name:string,mime:string,bytes:number,uploadedAt:string,uploadedBy:string}[]}[]",
    "contracts:{id:string,contractor:string,road:string,scope:string,start:string,end:string,poc:string,email:string,notes?:string,phone?:string,address?:string,addressCountry?:string,scopeLat?:number,scopeLng?:number,scopeRadius?:number,documents?:{id:string,name:string,mime:string,bytes:number,uploadedAt:string,uploadedBy:string}[]}[]",
    "domain.ts: add phone/address/addressCountry and future radius fields to Contract")

# ---------- lib/actions.ts ----------

# member/memberUpdate schema: add phone
replace_once('lib/actions.ts',
    "const v=z.object({name:short,email:z.string().trim().email().max(250).transform(x=>x.toLowerCase()),role:z.enum(roles as [typeof roles[number],...typeof roles[number][]]),team:z.string().max(150),contractor:z.string().max(150),vehicleTag:z.string().max(150).optional().transform(x=>x?.trim()||''),authUserId:z.string().uuid(),active:z.boolean()}).parse(body);",
    "const v=z.object({name:short,email:z.string().trim().email().max(250).transform(x=>x.toLowerCase()),role:z.enum(roles as [typeof roles[number],...typeof roles[number][]]),team:z.string().max(150),contractor:z.string().max(150),vehicleTag:z.string().max(150).optional().transform(x=>x?.trim()||''),phone:z.string().max(40).optional().transform(x=>x?.trim()||''),authUserId:z.string().uuid(),active:z.boolean()}).parse(body);",
    "actions.ts: member schema accepts phone")

# contract create schema: add phone/address/addressCountry
replace_once('lib/actions.ts',
    "const v=z.object({contractor:short,road:short,scope:z.string().trim().min(10).max(2000),start:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),end:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),poc:short,email:z.string().trim().email().max(250)}).parse(body);",
    "const v=z.object({contractor:short,road:short,scope:z.string().trim().min(10).max(2000),start:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),end:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),poc:short,email:z.string().trim().email().max(250),phone:z.string().max(40).optional().transform(x=>x?.trim()||''),address:z.string().max(300).optional().transform(x=>x?.trim()||''),addressCountry:z.string().max(50).optional().transform(x=>x?.trim()||'')}).parse(body);",
    "actions.ts: contract create schema accepts phone/address/addressCountry")

# contractUpdate schema: add phone/address/addressCountry
replace_once('lib/actions.ts',
    "const v=z.object({contractor:short,road:short,scope:z.string().trim().min(10).max(2000),start:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),end:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),poc:short,email:z.string().trim().email().max(250),notes:z.string().max(4000).optional().transform(x=>x?.trim()||'')}).parse(body);",
    "const v=z.object({contractor:short,road:short,scope:z.string().trim().min(10).max(2000),start:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),end:z.string().regex(/^\\d{4}-\\d{2}-\\d{2}$/),poc:short,email:z.string().trim().email().max(250),notes:z.string().max(4000).optional().transform(x=>x?.trim()||''),phone:z.string().max(40).optional().transform(x=>x?.trim()||''),address:z.string().max(300).optional().transform(x=>x?.trim()||''),addressCountry:z.string().max(50).optional().transform(x=>x?.trim()||'')}).parse(body);",
    "actions.ts: contractUpdate schema accepts phone/address/addressCountry")

# ---------- version + changelog ----------
version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

replace_once('package.json', '"version": "2.1.6",', f'"version": "{VERSION}",', "package.json: bump version field")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Added phone number field for members and contracts
- Added address and country/region fields for contracts
- Schema prepared for a future interactive scope-radius picker (Leaflet, free/no API key)
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" in existing:
        print(f"SKIP: CHANGELOG.md already has an entry for {VERSION}")
    else:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Now run:")
print("  git diff")
print("  npm run build")
