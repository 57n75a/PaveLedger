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

VERSION = "2.1.3"
TODAY = date.today().isoformat()

# ---------- 1. nav array: split into two items ----------
replace_once('app/workspace.tsx',
    "const nav=[{name:'Overview',icon:LayoutDashboard},{name:'Investigations',icon:ListChecks},{name:'Analytics',icon:BarChart3},{name:'Contracts',icon:ShieldCheck},{name:'Teams & access',icon:Users},{name:'Notifications',icon:Bell},...(['Admin','Team lead','Director'].includes(role||'')?[{name:'Archive',icon:FileText}]:[])];",
    "const nav=[{name:'Overview',icon:LayoutDashboard},{name:'Investigations',icon:ListChecks},{name:'Analytics',icon:BarChart3},{name:'Contracts',icon:ShieldCheck},{name:'Teams',icon:Users},{name:'Roles',icon:ShieldCheck},{name:'Notifications',icon:Bell},...(['Admin','Team lead','Director'].includes(role||'')?[{name:'Archive',icon:FileText}]:[])];",
    "workspace.tsx: nav array splits Teams and Roles")

# ---------- 2. Split the combined view into two separate views ----------
OLD_BLOCK = '''{view==='Teams & access'&&<section className="panel"><div className="section-head"><div><h2>Teams and role permissions</h2><p>{['Admin','Team lead','Director'].includes(role||'')?'Bind verified accounts, set roles and suspend access.':'Membership shown within your permitted scope.'}</p></div>{role==='Admin'&&<div className="button-row"><button className="secondary" onClick={()=>setTeamOpen(true)}>Create team</button><button className="primary" onClick={()=>setMemberOpen(true)}>Add member</button></div>}</div><div className="team-grid">{data.teams.map(team=><div className="panel-mini" key={team}><h3>{team}</h3><small>{data.members.filter(m=>m.team===team&&isActive(m)).length} active members</small></div>)}{!data.teams.length&&<p className="muted">No teams created yet.</p>}</div><Table><TableHeader><TableRow><TableHead>Member</TableHead><TableHead>Role</TableHead><TableHead>Scope</TableHead><TableHead>Access</TableHead><TableHead>Manage</TableHead></TableRow></TableHeader><TableBody>{data.members.map(m=><TableRow key={m.id}><TableCell><strong>{m.name}</strong><small className="block muted">{m.email}</small></TableCell><TableCell>{m.role}</TableCell><TableCell>{m.team||m.contractor||'Organization'}</TableCell><TableCell>{{Admin:'Manage organization and all cases','Team lead':'Assign and manage team cases',Analyst:'Investigate assigned cases','Head Analyst':'Oversees team analysts and escalates cases',Reviewer:'Independently verify team repairs',Contractor:'Update assigned repairs',Auditor:'Read permitted records',Vehicle:'Reports detected road defects',Director:'Receives escalated cases across teams'}[m.role]} · {isActive(m)?'Active':'Suspended'}</TableCell><TableCell>{['Admin','Team lead','Director'].includes(role||'')&&<button className="secondary" onClick={()=>setEditingMember(m)}>Edit access</button>}</TableCell></TableRow>)}</TableBody></Table><p className="footnote">Server permissions apply to all reads and updates. Role preview is an owner-admin demonstration feature. New memberships also require a verified sign-in account provisioned by your administrator.</p></section>}'''

NEW_BLOCKS = '''{view==='Teams'&&<section className="panel"><div className="section-head"><div><h2>Teams</h2><p>Organize investigators by geography or responsibility.</p></div>{role==='Admin'&&<button className="primary" onClick={()=>setTeamOpen(true)}>Create team</button>}</div><div className="team-grid">{data.teams.map(team=><div className="panel-mini" key={team}><h3>{team}</h3><small>{data.members.filter(m=>m.team===team&&isActive(m)).length} active members</small></div>)}{!data.teams.length&&<p className="muted">No teams created yet.</p>}</div></section>}
 {view==='Roles'&&<section className="panel"><div className="section-head"><div><h2>Roles and permissions</h2><p>{['Admin','Team lead','Director'].includes(role||'')?'Bind verified accounts, set roles and suspend access.':'Membership shown within your permitted scope.'}</p></div>{role==='Admin'&&<button className="primary" onClick={()=>setMemberOpen(true)}>Add member</button>}</div><Table><TableHeader><TableRow><TableHead>Member</TableHead><TableHead>Role</TableHead><TableHead>Scope</TableHead><TableHead>Access</TableHead><TableHead>Manage</TableHead></TableRow></TableHeader><TableBody>{data.members.map(m=><TableRow key={m.id}><TableCell><strong>{m.name}</strong><small className="block muted">{m.email}</small></TableCell><TableCell>{m.role}</TableCell><TableCell>{m.team||m.contractor||'Organization'}</TableCell><TableCell>{{Admin:'Manage organization and all cases','Team lead':'Assign and manage team cases',Analyst:'Investigate assigned cases','Head Analyst':'Oversees team analysts and escalates cases',Reviewer:'Independently verify team repairs',Contractor:'Update assigned repairs',Auditor:'Read permitted records',Vehicle:'Reports detected road defects',Director:'Receives escalated cases across teams'}[m.role]} · {isActive(m)?'Active':'Suspended'}</TableCell><TableCell>{['Admin','Team lead','Director'].includes(role||'')&&<button className="secondary" onClick={()=>setEditingMember(m)}>Edit access</button>}</TableCell></TableRow>)}</TableBody></Table><p className="footnote">Server permissions apply to all reads and updates. Role preview is an owner-admin demonstration feature. New memberships also require a verified sign-in account provisioned by your administrator.</p></section>}'''

replace_once('app/workspace.tsx', OLD_BLOCK, NEW_BLOCKS, "workspace.tsx: split combined view into Teams and Roles views")

# ---------- version + changelog ----------
version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

replace_once('package.json', '"version": "2.1.2",', f'"version": "{VERSION}",', "package.json: bump version field")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Split "Teams & access" into two separate sidebar sections: Teams (team list, create team) and Roles (member table, edit access)
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
