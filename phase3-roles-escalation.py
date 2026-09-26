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

VERSION = "2.0.2"
TODAY = date.today().isoformat()

# ============================================================
# lib/domain.ts
# ============================================================

replace_once('lib/domain.ts',
    "export type Role = 'Admin'|'Team lead'|'Analyst'|'Reviewer'|'Contractor'|'Auditor'|'Vehicle';",
    "export type Role = 'Admin'|'Team lead'|'Analyst'|'Head Analyst'|'Reviewer'|'Contractor'|'Auditor'|'Vehicle'|'Director';",
    "domain.ts: add Head Analyst and Director to Role type")

replace_once('lib/domain.ts',
    "export const roles:Role[]=['Admin','Team lead','Analyst','Reviewer','Contractor','Auditor','Vehicle'];",
    "export const roles:Role[]=['Admin','Team lead','Analyst','Head Analyst','Reviewer','Contractor','Auditor','Vehicle','Director'];",
    "domain.ts: add Head Analyst and Director to roles array")

replace_once('lib/domain.ts',
    "lane?:string;contractId?:string;reportedBy?:string;duplicateOf?:string;",
    "lane?:string;contractId?:string;reportedBy?:string;escalatedTo?:string;duplicateOf?:string;",
    "domain.ts: add escalatedTo to Ticket type")

replace_once('lib/domain.ts',
    "export function canSee(t:Ticket,m:Member){if(!isActive(m))return false;return m.role==='Admin'||m.role==='Auditor'||(['Team lead','Reviewer'].includes(m.role)&&t.team===m.team)||(m.role==='Analyst'&&t.analyst===m.id)||(m.role==='Contractor'&&!!m.contractor&&t.contractor===m.contractor&&['Notice prepared','Acknowledged','Repair in progress','Awaiting verification','Verified closed','Reopened','On hold'].includes(t.status));}",
    "export function canSee(t:Ticket,m:Member){if(!isActive(m))return false;return m.role==='Admin'||m.role==='Auditor'||m.role==='Director'||(['Team lead','Reviewer','Head Analyst'].includes(m.role)&&t.team===m.team)||(m.role==='Analyst'&&t.analyst===m.id)||(m.role==='Contractor'&&!!m.contractor&&t.contractor===m.contractor&&['Notice prepared','Acknowledged','Repair in progress','Awaiting verification','Verified closed','Reopened','On hold'].includes(t.status));}",
    "domain.ts: Director sees all, Head Analyst sees team like Team lead")

replace_once('lib/domain.ts',
    "export function permitted(m:Member,t:Ticket,next:string){if(!canSee(t,m)||m.role==='Auditor'||!nextStages(t).includes(next))return false;",
    "export function permitted(m:Member,t:Ticket,next:string){if(!canSee(t,m)||['Auditor','Director'].includes(m.role)||!nextStages(t).includes(next))return false;",
    "domain.ts: Director cannot transition tickets directly (oversight role)")

# ============================================================
# lib/actions.ts
# ============================================================

replace_once('lib/actions.ts',
    "if(['Team lead','Analyst','Reviewer'].includes(v.role)&&!s.teams.includes(v.team))throw new AppError('Choose an existing team.');",
    "if(['Team lead','Analyst','Reviewer','Head Analyst'].includes(v.role)&&!s.teams.includes(v.team))throw new AppError('Choose an existing team.');",
    "actions.ts: Head Analyst requires a team")

replace_once('lib/actions.ts',
    "const clean={...v,team:['Team lead','Analyst','Reviewer','Admin'].includes(v.role)?v.team:'',contractor:v.role==='Contractor'?v.contractor:'',vehicleTag:v.role==='Vehicle'?v.vehicleTag:'',demo:false};",
    "const clean={...v,team:['Team lead','Analyst','Reviewer','Admin','Head Analyst'].includes(v.role)?v.team:'',contractor:v.role==='Contractor'?v.contractor:'',vehicleTag:v.role==='Vehicle'?v.vehicleTag:'',demo:false};",
    "actions.ts: keep team assignment for Head Analyst")

replace_once('lib/actions.ts',
    "}else if(action==='note'){requireRole(['Admin','Team lead','Analyst','Reviewer','Contractor']);noteField.parse(note);event='Note added';}",
    "}else if(action==='note'){requireRole(['Admin','Team lead','Analyst','Reviewer','Contractor']);noteField.parse(note);event='Note added';}else if(action==='escalate'){const targetRole=m.role==='Head Analyst'?'Team lead':m.role==='Team lead'?'Director':null;if(!targetRole)throw new AppError('Your role cannot escalate tickets.',403);t.escalatedTo=targetRole;t.updated=now;const recipients=s.members.filter(x=>isActive(x)&&x.role===targetRole&&(targetRole!=='Team lead'||x.team===t.team));recipients.forEach(r=>s.notifications.unshift({id:crypto.randomUUID(),recipient:r.id,ticket:t.id,text:`Escalated to ${targetRole}: ${t.road}`,at:now}));event='Escalated to '+targetRole;}",
    "actions.ts: add escalate action")

# ============================================================
# app/workspace.tsx
# ============================================================

replace_once('app/workspace.tsx',
    "{Admin:'Manage organization and all cases','Team lead':'Assign and manage team cases',Analyst:'Investigate assigned cases',Reviewer:'Independently verify team repairs',Contractor:'Update assigned repairs',Auditor:'Read permitted records',Vehicle:'Reports detected road defects'}[m.role]",
    "{Admin:'Manage organization and all cases','Team lead':'Assign and manage team cases',Analyst:'Investigate assigned cases','Head Analyst':'Oversees team analysts and escalates cases',Reviewer:'Independently verify team repairs',Contractor:'Update assigned repairs',Auditor:'Read permitted records',Vehicle:'Reports detected road defects',Director:'Receives escalated cases across teams'}[m.role]",
    "workspace.tsx: role descriptions for Head Analyst and Director")

replace_once('app/workspace.tsx',
    '''<button disabled={busy||!['Admin','Team lead'].includes(data.viewer.role)} className="primary" onClick={()=>mutate({action:'assign',id:t.id,team,analyst:analyst==='none'?'':analyst,note:'Assignment updated by '+data.viewer.name})}>Save assignment</button></div></TabsContent>''',
    '''<button disabled={busy||!['Admin','Team lead'].includes(data.viewer.role)} className="primary" onClick={()=>mutate({action:'assign',id:t.id,team,analyst:analyst==='none'?'':analyst,note:'Assignment updated by '+data.viewer.name})}>Save assignment</button>{['Head Analyst','Team lead'].includes(data.viewer.role)&&<button disabled={busy} className="secondary" onClick={()=>mutate({action:'escalate',id:t.id})}>Escalate to {data.viewer.role==='Head Analyst'?'Team lead':'Director'}</button>}{t.escalatedTo&&<p className="muted">Currently escalated to {t.escalatedTo}.</p>}</div></TabsContent>''',
    "workspace.tsx: escalate button and status in Assignment tab")

# ============================================================
# Version + changelog
# ============================================================

version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")
else:
    print("SKIP: lib/version.ts not found — run the versioning setup script first.")

replace_once('package.json', '"version": "2.0.1",', f'"version": "{VERSION}",', "package.json: bump version field")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Added Head Analyst and Director roles
- Added escalation workflow: Head Analyst -> Team lead -> Director, with notifications
- Director has organization-wide read access but does not perform ticket transitions directly
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" in existing:
        print(f"SKIP: CHANGELOG.md already has an entry for {VERSION}")
    else:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")
else:
    changelog_path.write_text(f"# Changelog\n\n{entry}")
    print(f"OK: created CHANGELOG.md with {VERSION} entry")

print("\nDone. Now run:")
print("  git diff")
print("  npm run build")
