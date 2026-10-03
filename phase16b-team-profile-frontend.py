import pathlib, re
from datetime import date

VERSION = "2.6.3"
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

replace_once(WP,
    '''{editingTeam===team?<form className="form" onSubmit={async e=>{e.preventDefault();const f=new FormData(e.currentTarget);if(await mutate({action:'teamUpdate',oldName:team,newName:String(f.get('newName')||'').trim()}))setEditingTeam(null)}}><label>Team name<input name="newName" defaultValue={team} required/></label><div className="button-row"><button className="primary" disabled={busy}>Save</button><button type="button" className="secondary" onClick={()=>setEditingTeam(null)}>Cancel</button></div></form>:<><h2>{team}</h2><p>{count} active user{count===1?'':'s'}</p>{role==='Admin'&&<div className="button-row"><button className="secondary" onClick={()=>setEditingTeam(team)}>Edit team</button><button className="secondary" onClick={()=>setManagingTeam(team)}>Manage users</button><button className="secondary" onClick={()=>{if(confirm('Delete team "'+team+'"? This cannot be undone.'))mutate({action:'teamDelete',name:team})}}>Delete team</button></div>}</>}''',
    '''{editingTeam===team?<form className="form" onSubmit={async e=>{e.preventDefault();const fd=new FormData(e.currentTarget);const newName=String(fd.get('newName')||'').trim();const email=String(fd.get('teamEmail')||'');const phone=String(fd.get('teamPhone')||'');const file=fd.get('teamLogo') as File;const payload:any={action:'teamUpdate',oldName:team,newName,email,phone};if(file&&file.size>0){if(file.size>500_000){toast.error('Team logo must be under 500 KB');return}const dataUrl=await new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result));reader.onerror=reject;reader.readAsDataURL(file)});payload.logo=dataUrl}if(await mutate(payload))setEditingTeam(null)}}><label>Team name<input name="newName" defaultValue={team} required/></label><label>Team email<input name="teamEmail" type="email" defaultValue={data.teamProfiles?.[team]?.email||''}/></label><label>Team phone<input name="teamPhone" type="tel" defaultValue={data.teamProfiles?.[team]?.phone||''}/></label><label>Team logo (under 500 KB)<input name="teamLogo" type="file" accept="image/png,image/jpeg,image/webp"/></label><div className="button-row"><button className="primary" disabled={busy}>Save</button><button type="button" className="secondary" onClick={()=>setEditingTeam(null)}>Cancel</button></div></form>:<>{data.teamProfiles?.[team]?.logo&&<img src={data.teamProfiles[team].logo} alt="" style={{width:40,height:40,borderRadius:8,objectFit:'cover',marginBottom:8}}/>}<h2>{team}</h2><p>{count} active user{count===1?'':'s'}</p>{(data.teamProfiles?.[team]?.email||data.teamProfiles?.[team]?.phone)&&<p className="footnote">{data.teamProfiles?.[team]?.email}{data.teamProfiles?.[team]?.email&&data.teamProfiles?.[team]?.phone?' \u00b7 ':''}{data.teamProfiles?.[team]?.phone}</p>}{role==='Admin'&&<div className="button-row"><button className="secondary" onClick={()=>setEditingTeam(team)}>Edit team</button><button className="secondary" onClick={()=>setManagingTeam(team)}>Manage users</button><button className="secondary" onClick={()=>{if(confirm('Delete team "'+team+'"? This cannot be undone.'))mutate({action:'teamDelete',name:team})}}>Delete team</button></div>}</>}''',
    "workspace.tsx: Edit team form gets logo/email/phone, card displays them")

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
- Team cards now show the team logo and contact email/phone when set, and the Edit team form lets Admin set all three
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Now run:")
print("  npm run build")
