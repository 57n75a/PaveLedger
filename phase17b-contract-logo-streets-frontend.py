import pathlib, re
from datetime import date

VERSION = "2.7.1"
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

WP = 'app/workspace.tsx'

# ---------- 1. Create dialog: new onSubmit (extracts logo file) ----------
replace_once(WP,
    '''<form className="form" onSubmit={async e=>{e.preventDefault();if(await mutate({action:'contract',...Object.fromEntries(new FormData(e.currentTarget))}))setContractOpen(false)}}>''',
    '''<form className="form" onSubmit={async e=>{e.preventDefault();const fd=new FormData(e.currentTarget);const file=fd.get('logo') as File;fd.delete('logo');const payload:any={action:'contract',...Object.fromEntries(fd)};if(file&&file.size>0){if(file.size>500_000){toast.error('Logo must be under 500 KB');return}payload.logo=await new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result));reader.onerror=reject;reader.readAsDataURL(file)})}if(await mutate(payload))setContractOpen(false)}}>''',
    "workspace.tsx: contract create dialog extracts logo file")

# ---------- 2. Create dialog: add additionalRoads + logo fields, after the country select ----------
replace_once(WP,
    '''<option value="EU">EU</option></select></label><ScopeLocator/>''',
    '''<option value="EU">EU</option></select></label><label>Additional streets covered (optional, one per line)<textarea name="additionalRoads" placeholder="e.g. Oak Avenue&#10;Maple Street"/></label><label>Company logo (optional, under 500 KB)<input name="logo" type="file" accept="image/png,image/jpeg,image/webp"/></label><ScopeLocator/>''',
    "workspace.tsx: contract create dialog gets additionalRoads + logo fields")

# ---------- 3. Edit dialog: new onSubmit (extracts logo file) ----------
replace_once(WP,
    '''onSubmit={async e=>{e.preventDefault();const fd=new FormData(e.currentTarget);const f=Object.fromEntries(fd);const linkTicketIds=data.tickets.filter((t:Ticket)=>t.road===editingContract.road).map((t:Ticket)=>t.id).filter((id:string)=>fd.has('link_'+id));if(await mutate({action:'contractUpdate',contractId:editingContract.id,...f,linkTicketIds}))setEditingContract(null)}}''',
    '''onSubmit={async e=>{e.preventDefault();const fd=new FormData(e.currentTarget);const file=fd.get('logo') as File;fd.delete('logo');const f=Object.fromEntries(fd);const linkTicketIds=data.tickets.filter((t:Ticket)=>t.road===editingContract.road).map((t:Ticket)=>t.id).filter((id:string)=>fd.has('link_'+id));const payload:any={action:'contractUpdate',contractId:editingContract.id,...f,linkTicketIds};if(file&&file.size>0){if(file.size>500_000){toast.error('Logo must be under 500 KB');return}payload.logo=await new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result));reader.onerror=reject;reader.readAsDataURL(file)})}if(await mutate(payload))setEditingContract(null)}}''',
    "workspace.tsx: contract edit dialog extracts logo file")

# ---------- 4. Edit dialog: add additionalRoads + logo fields, after the country select ----------
replace_once(WP,
    '''<option value="EU">EU</option></select></label><ScopeLocator key={editingContract.id}''',
    '''<option value="EU">EU</option></select></label><label>Additional streets covered (optional, one per line)<textarea name="additionalRoads" defaultValue={(editingContract.additionalRoads||[]).join('\\n')} placeholder="e.g. Oak Avenue&#10;Maple Street"/></label><label>Company logo (optional, under 500 KB)<input name="logo" type="file" accept="image/png,image/jpeg,image/webp"/></label><ScopeLocator key={editingContract.id}''',
    "workspace.tsx: contract edit dialog gets additionalRoads + logo fields")

# ---------- 5. Contract card: show logo and additional streets ----------
replace_once(WP,
    '''<small>{c.id}</small><h2>{c.contractor}</h2><h3>{c.road}</h3><p>{c.scope||'No work-scope description provided.'}</p>''',
    '''<small>{c.id}</small>{c.logo&&<img src={c.logo} alt="" style={{width:40,height:40,borderRadius:8,objectFit:'cover',margin:'8px 0'}}/>}<h2>{c.contractor}</h2><h3>{c.road}</h3>{!!c.additionalRoads?.length&&<p className="footnote">Also covers: {c.additionalRoads.join(', ')}</p>}<p>{c.scope||'No work-scope description provided.'}</p>''',
    "workspace.tsx: contract card shows logo and additional streets")

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
- Contract create/edit forms now have a company logo upload and an "additional streets covered" field
- Contract cards display the logo and any additional streets
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Now run:")
print("  npm run build")
