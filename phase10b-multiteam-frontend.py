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

VERSION = "2.2.0"
TODAY = date.today().isoformat()

# ---------- 1. MemberForm: state + onSave use teams array ----------
replace_once('app/workspace.tsx',
    '''const [role,setRole]=useState(initial?.role||'Analyst'),[team,setTeam]=useState(initial?.team||data.teams[0]||'none'),[firm,setFirm]=useState(initial?.contractor||'none'),[active,setActive]=useState(initial?.active!==false);return <form className="form" onSubmit={e=>{e.preventDefault();onSave({...Object.fromEntries(new FormData(e.currentTarget)),role,team:team==='none'?'':team,contractor:firm==='none'?'':firm,active})}}>''',
    '''const [role,setRole]=useState(initial?.role||'Analyst'),[teams,setTeams]=useState<string[]>(initial?.teams||[]),[firm,setFirm]=useState(initial?.contractor||'none'),[active,setActive]=useState(initial?.active!==false);return <form className="form" onSubmit={e=>{e.preventDefault();onSave({...Object.fromEntries(new FormData(e.currentTarget)),role,teams,contractor:firm==='none'?'':firm,active})}}>''',
    "workspace.tsx: MemberForm state/onSave use teams array")

# ---------- 2. MemberForm: Team Pick -> checkboxes (up to 3) ----------
replace_once('app/workspace.tsx',
    '''<Pick label="Team" value={team} onChange={setTeam} items={[{value:'none',label:'No team'},...data.teams.map(x=>({value:x,label:x}))]}/>''',
    '''<div className="form"><p className="footnote">Teams (choose up to 3)</p>{data.teams.map(t=><label className="check" key={t}><Checkbox checked={teams.includes(t)} disabled={!teams.includes(t)&&teams.length>=3} onCheckedChange={v=>setTeams(v?[...teams,t].slice(0,3):teams.filter(x=>x!==t))}/>{t}</label>)}</div>''',
    "workspace.tsx: MemberForm team checkboxes")

# ---------- 3. AddToTeamPicker: eligibility + payload use teams array ----------
replace_once('app/workspace.tsx',
    '''const eligible=data.members.filter((m:Member)=>m.team!==team&&['Team lead','Analyst','Reviewer','Head Analyst'].includes(m.role));
 return <div className="two-cols"><Pick label="Member" value={pick} onChange={setPick} items={[{value:'none',label:'Choose a member'},...eligible.map((m:Member)=>({value:m.id,label:m.name+' \u00b7 '+m.role}))]}/><button className="primary" disabled={busy||pick==='none'} onClick={async()=>{const m=data.members.find((x:Member)=>x.id===pick);if(!m)return;if(await mutate({action:'memberUpdate',memberId:m.id,name:m.name,email:m.email,role:m.role,team,contractor:m.contractor||'',vehicleTag:m.vehicleTag||'',authUserId:m.authUserId,active:m.active!==false}))setPick('none')}}>Add to team</button></div>;''',
    '''const eligible=data.members.filter((m:Member)=>!(m.teams||[]).includes(team)&&(m.teams||[]).length<3&&['Team lead','Analyst','Reviewer','Head Analyst'].includes(m.role));
 return <div className="two-cols"><Pick label="Member" value={pick} onChange={setPick} items={[{value:'none',label:'Choose a member'},...eligible.map((m:Member)=>({value:m.id,label:m.name+' \u00b7 '+m.role}))]}/><button className="primary" disabled={busy||pick==='none'} onClick={async()=>{const m=data.members.find((x:Member)=>x.id===pick);if(!m)return;if(await mutate({action:'memberUpdate',memberId:m.id,name:m.name,email:m.email,role:m.role,teams:[...(m.teams||[]),team].slice(0,3),contractor:m.contractor||'',vehicleTag:m.vehicleTag||'',authUserId:m.authUserId,active:m.active!==false}))setPick('none')}}>Add to team</button></div>;''',
    "workspace.tsx: AddToTeamPicker uses teams array")

# ---------- 4. Team management dialog: current members + Remove button ----------
replace_once('app/workspace.tsx',
    '''{data.members.filter((m:Member)=>m.team===managingTeam).map((m:Member)=><div className="queue-row" key={m.id}><div className="queue-title"><strong>{m.name}</strong><small>{m.role}</small></div><button className="secondary" disabled={busy} onClick={()=>mutate({action:'memberUpdate',memberId:m.id,name:m.name,email:m.email,role:m.role,team:'',contractor:m.contractor||'',vehicleTag:m.vehicleTag||'',authUserId:m.authUserId,active:m.active!==false})}>Remove</button></div>)}{!data.members.filter((m:Member)=>m.team===managingTeam).length&&<p className="muted">No members in this team yet.</p>}''',
    '''{data.members.filter((m:Member)=>(m.teams||[]).includes(managingTeam)).map((m:Member)=><div className="queue-row" key={m.id}><div className="queue-title"><strong>{m.name}</strong><small>{m.role}</small></div><button className="secondary" disabled={busy} onClick={()=>mutate({action:'memberUpdate',memberId:m.id,name:m.name,email:m.email,role:m.role,teams:(m.teams||[]).filter((x:string)=>x!==managingTeam),contractor:m.contractor||'',vehicleTag:m.vehicleTag||'',authUserId:m.authUserId,active:m.active!==false})}>Remove</button></div>)}{!data.members.filter((m:Member)=>(m.teams||[]).includes(managingTeam)).length&&<p className="muted">No members in this team yet.</p>}''',
    "workspace.tsx: team management dialog uses teams array")

# ---------- 5. Teams card: member count uses teams array ----------
replace_once('app/workspace.tsx',
    "const count=data.members.filter(m=>m.team===team&&isActive(m)).length;",
    "const count=data.members.filter(m=>(m.teams||[]).includes(team)&&isActive(m)).length;",
    "workspace.tsx: Teams card count uses teams array")

# ---------- 6. Detail Assignment tab: analyst filter uses teams array ----------
replace_once('app/workspace.tsx',
    "data.members.filter(m=>m.role==='Analyst'&&m.team===team&&isActive(m)).map(m=>({value:m.id,label:m.name}))",
    "data.members.filter(m=>m.role==='Analyst'&&(m.teams||[]).includes(team)&&isActive(m)).map(m=>({value:m.id,label:m.name}))",
    "workspace.tsx: assignment analyst picker uses teams array")

# ---------- version + changelog ----------
version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

replace_once('package.json', '"version": "2.1.9",', f'"version": "{VERSION}",', "package.json: bump version field")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Add member form now shows team checkboxes (up to 3) instead of a single team dropdown
- Team management, assignment pickers, and Teams page member counts all updated for multi-team membership
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
