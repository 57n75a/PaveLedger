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

VERSION = "2.1.6"
TODAY = date.today().isoformat()

# ---------- lib/actions.ts: teamDelete action ----------
replace_once('lib/actions.ts',
    "event='Team renamed: '+oldName+' -> '+newName;\n }else if(action==='member'||action==='memberUpdate'){",
    "event='Team renamed: '+oldName+' -> '+newName;\n }else if(action==='teamDelete'){\n  requireRole(['Admin']);const name=short.parse(body.name);if(!s.teams.includes(name))throw new AppError('Team not found.');if(s.members.some(x=>x.team===name&&isActive(x)))throw new AppError('Reassign or suspend all active members of this team before deleting it.');if(s.tickets.some(x=>x.team===name&&!closed(x)))throw new AppError('Reassign all open investigations for this team before deleting it.');s.teams=s.teams.filter(x=>x!==name);event='Team deleted: '+name;\n }else if(action==='member'||action==='memberUpdate'){",
    "actions.ts: add teamDelete action with safety checks")

# ---------- app/workspace.tsx: managingTeam state ----------
replace_once('app/workspace.tsx',
    "[editingContract,setEditingContract]=useState<any>(null),[editingTeam,setEditingTeam]=useState<string|null>(null);",
    "[editingContract,setEditingContract]=useState<any>(null),[editingTeam,setEditingTeam]=useState<string|null>(null),[managingTeam,setManagingTeam]=useState<string|null>(null);",
    "workspace.tsx: add managingTeam state")

# ---------- app/workspace.tsx: team card gets Manage members + Delete buttons ----------
replace_once('app/workspace.tsx',
    '''{role==='Admin'&&<button className="secondary" onClick={()=>setEditingTeam(team)}>Rename team</button>}</>}</article>})}{!data.teams.length&&<p className="muted">No teams created yet.</p>}</div>''',
    '''{role==='Admin'&&<div className="button-row"><button className="secondary" onClick={()=>setEditingTeam(team)}>Rename team</button><button className="secondary" onClick={()=>setManagingTeam(team)}>Manage members</button><button className="secondary" onClick={()=>{if(confirm('Delete team "'+team+'"? This cannot be undone.'))mutate({action:'teamDelete',name:team})}}>Delete team</button></div>}</>}</article>})}{!data.teams.length&&<p className="muted">No teams created yet.</p>}</div>''',
    "workspace.tsx: add Manage members and Delete team buttons")

# ---------- app/workspace.tsx: AddToTeamPicker helper component ----------
replace_once('app/workspace.tsx',
    "function TicketTable(",
    '''function AddToTeamPicker({team,data,mutate,busy}:{team:string,data:any,mutate:(b:any)=>Promise<boolean>,busy:boolean}){
 const [pick,setPick]=useState('none');
 const eligible=data.members.filter((m:Member)=>m.team!==team&&['Team lead','Analyst','Reviewer','Head Analyst'].includes(m.role));
 return <div className="two-cols"><Pick label="Member" value={pick} onChange={setPick} items={[{value:'none',label:'Choose a member'},...eligible.map((m:Member)=>({value:m.id,label:m.name+' \u00b7 '+m.role}))]}/><button className="primary" disabled={busy||pick==='none'} onClick={async()=>{const m=data.members.find((x:Member)=>x.id===pick);if(!m)return;if(await mutate({action:'memberUpdate',memberId:m.id,name:m.name,email:m.email,role:m.role,team,contractor:m.contractor||'',vehicleTag:m.vehicleTag||'',authUserId:m.authUserId,active:m.active!==false}))setPick('none')}}>Add to team</button></div>;
}
function TicketTable(''',
    "workspace.tsx: add AddToTeamPicker component")

# ---------- app/workspace.tsx: Manage members Dialog ----------
replace_once('app/workspace.tsx',
    '<Dialog open={teamOpen} onOpenChange={setTeamOpen}>',
    '''<Dialog open={!!managingTeam} onOpenChange={v=>!v&&setManagingTeam(null)}><DialogContent><DialogHeader><DialogTitle>Manage {managingTeam}</DialogTitle><DialogDescription>Add or remove members from this team.</DialogDescription></DialogHeader>{managingTeam&&data&&<div className="form"><h3>Current members</h3>{data.members.filter((m:Member)=>m.team===managingTeam).map((m:Member)=><div className="queue-row" key={m.id}><div className="queue-title"><strong>{m.name}</strong><small>{m.role}</small></div><button className="secondary" disabled={busy} onClick={()=>mutate({action:'memberUpdate',memberId:m.id,name:m.name,email:m.email,role:m.role,team:'',contractor:m.contractor||'',vehicleTag:m.vehicleTag||'',authUserId:m.authUserId,active:m.active!==false})}>Remove</button></div>)}{!data.members.filter((m:Member)=>m.team===managingTeam).length&&<p className="muted">No members in this team yet.</p>}<h3>Add a member</h3><AddToTeamPicker team={managingTeam} data={data} mutate={mutate} busy={busy}/></div>}</DialogContent></Dialog>
<Dialog open={teamOpen} onOpenChange={setTeamOpen}>''',
    "workspace.tsx: add team member-management Dialog")

# ---------- version + changelog ----------
version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

replace_once('package.json', '"version": "2.1.5",', f'"version": "{VERSION}",', "package.json: bump version field")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Admin can now delete a team directly from the Teams page (blocked if it still has active members or open investigations)
- Admin can now add or remove members from a team directly from the Teams page, without going through Roles
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
