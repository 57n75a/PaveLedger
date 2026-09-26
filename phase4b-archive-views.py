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

VERSION = "2.0.5"
TODAY = date.today().isoformat()

# ---------- app/workspace.tsx ----------

replace_once('app/workspace.tsx',
    "const tickets=data?.tickets||[],active=tickets.filter(t=>!['Verified closed','Rejected','Duplicate'].includes(t.status)),urgent=active.filter(t=>t.severity==='Urgent'),reopened=tickets.filter(t=>t.reopened>0),waiting=tickets.filter(t=>t.status==='Awaiting verification');",
    "const allTickets=data?.tickets||[],tickets=allTickets.filter(t=>!t.archived),archivedTickets=allTickets.filter(t=>t.archived),active=tickets.filter(t=>!['Verified closed','Rejected','Duplicate'].includes(t.status)),urgent=active.filter(t=>t.severity==='Urgent'),reopened=tickets.filter(t=>t.reopened>0),waiting=tickets.filter(t=>t.status==='Awaiting verification');",
    "workspace.tsx: exclude archived tickets from all main lists, add archivedTickets")

replace_once('app/workspace.tsx',
    "const nav=[{name:'Overview',icon:LayoutDashboard},{name:'Investigations',icon:ListChecks},{name:'Analytics',icon:BarChart3},{name:'Contracts',icon:ShieldCheck},{name:'Teams & access',icon:Users},{name:'Notifications',icon:Bell}];",
    "const nav=[{name:'Overview',icon:LayoutDashboard},{name:'Investigations',icon:ListChecks},{name:'Analytics',icon:BarChart3},{name:'Contracts',icon:ShieldCheck},{name:'Teams & access',icon:Users},{name:'Notifications',icon:Bell},...(['Admin','Team lead','Director'].includes(role||'')?[{name:'Archive',icon:FileText}]:[])];",
    "workspace.tsx: add Archive nav item for Admin/Team lead/Director only")

replace_once('app/workspace.tsx',
    "{n.name==='Investigations'&&<b className=\"nav-count\">{active.length}</b>}",
    "{n.name==='Investigations'&&<b className=\"nav-count\">{active.length}</b>}{n.name==='Archive'&&<b className=\"nav-count\">{archivedTickets.length}</b>}",
    "workspace.tsx: show archived count badge in sidebar")

replace_once('app/workspace.tsx',
    '''{view==='Notifications'&&<section className="panel"><div className="section-head"><div><h2>Your notifications</h2><p>Assignment alerts for your current role</p></div></div>{!data.notifications.length?<div className="empty"><Bell size={30}/><h3>No assignment alerts yet</h3><p>Assign a ticket to an analyst to create an in-app notification.</p></div>:data.notifications.map(n=><button className="queue-row" key={n.id} onClick={()=>setSelected(n.ticket)}><Bell size={20}/><div className="queue-title"><strong>{n.text}</strong><small>{n.ticket}</small></div><small>{new Date(n.at).toLocaleString()}</small></button>)}</section>}''',
    '''{view==='Notifications'&&<section className="panel"><div className="section-head"><div><h2>Your notifications</h2><p>Assignment alerts for your current role</p></div></div>{!data.notifications.length?<div className="empty"><Bell size={30}/><h3>No assignment alerts yet</h3><p>Assign a ticket to an analyst to create an in-app notification.</p></div>:data.notifications.map(n=><button className="queue-row" key={n.id} onClick={()=>setSelected(n.ticket)}><Bell size={20}/><div className="queue-title"><strong>{n.text}</strong><small>{n.ticket}</small></div><small>{new Date(n.at).toLocaleString()}</small></button>)}</section>}
 {view==='Archive'&&<section className="panel"><div className="section-head"><div><h2>Archived investigations</h2><p>Hidden from the main dashboard. Visible to Admin, Team lead, and Director.</p></div></div><TicketTable tickets={archivedTickets} onSelect={setSelected} onPriority={(id,severity)=>mutate({action:'priority',id,severity})} canEditPriority={false} busy={busy}/>{!archivedTickets.length&&<div className="empty">No archived investigations.</div>}</section>}''',
    "workspace.tsx: add Archive view")

# ---------- version + changelog ----------

version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

replace_once('package.json', '"version": "2.0.4",', f'"version": "{VERSION}",', "package.json: bump version field")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Archived tickets are now hidden from Overview, Investigations, and Analytics
- Added a dedicated Archive section in the sidebar, visible only to Admin, Team lead, and Director
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
