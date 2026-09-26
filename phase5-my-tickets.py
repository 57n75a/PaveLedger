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

VERSION = "2.0.6"
TODAY = date.today().isoformat()

# ---------- app/workspace.tsx: derive "mine" ----------

replace_once('app/workspace.tsx',
    "const allTickets=data?.tickets||[],tickets=allTickets.filter(t=>!t.archived),archivedTickets=allTickets.filter(t=>t.archived),active=tickets.filter(t=>!['Verified closed','Rejected','Duplicate'].includes(t.status)),urgent=active.filter(t=>t.severity==='Urgent'),reopened=tickets.filter(t=>t.reopened>0),waiting=tickets.filter(t=>t.status==='Awaiting verification');",
    "const allTickets=data?.tickets||[],tickets=allTickets.filter(t=>!t.archived),archivedTickets=allTickets.filter(t=>t.archived),active=tickets.filter(t=>!['Verified closed','Rejected','Duplicate'].includes(t.status)),urgent=active.filter(t=>t.severity==='Urgent'),reopened=tickets.filter(t=>t.reopened>0),waiting=tickets.filter(t=>t.status==='Awaiting verification'),mine=tickets.filter(t=>t.analyst===data?.viewer.id||t.reportedBy===data?.viewer.id||t.completedBy===data?.viewer.id||t.closedBy===data?.viewer.id);",
    "workspace.tsx: derive 'mine' -- tickets personally tied to the viewer")

# ---------- app/workspace.tsx: add 'My tickets' section to Overview ----------

replace_once('app/workspace.tsx',
    '''<section className="panel lifecycle"><div className="section-head"><div><h2>Investigation stages</h2><p>Live counts within your role permissions</p></div><span className="muted">{tickets.length} total records</span></div><div className="stage-grid">{statuses.filter(s=>!['Rejected','Duplicate','On hold'].includes(s)).map(s=><button key={s} onClick={()=>{setFilter(s);setView('Investigations')}}><span style={{background:colors[s]}}/><strong>{tickets.filter(t=>t.status===s).length}</strong><small>{s}</small></button>)}</div></section></>}''',
    '''<section className="panel lifecycle"><div className="section-head"><div><h2>Investigation stages</h2><p>Live counts within your role permissions</p></div><span className="muted">{tickets.length} total records</span></div><div className="stage-grid">{statuses.filter(s=>!['Rejected','Duplicate','On hold'].includes(s)).map(s=><button key={s} onClick={()=>{setFilter(s);setView('Investigations')}}><span style={{background:colors[s]}}/><strong>{tickets.filter(t=>t.status===s).length}</strong><small>{s}</small></button>)}</div></section>
 <section className="panel lifecycle"><div className="section-head"><div><h2>My tickets</h2><p>Cases you are personally assigned to, reported, or have completed or closed</p></div><span className="muted">{mine.length} total</span></div><div className="stage-grid">{statuses.filter(s=>mine.some(t=>t.status===s)).map(s=><button key={s} onClick={()=>{setFilter(s);setView('Investigations')}}><span style={{background:colors[s]}}/><strong>{mine.filter(t=>t.status===s).length}</strong><small>{s}</small></button>)}{!mine.length&&<p className="muted">No personally assigned, reported, or completed cases yet.</p>}</div></section></>}''',
    "workspace.tsx: add My tickets section to Overview")

# ---------- version + changelog ----------

version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

replace_once('package.json', '"version": "2.0.5",', f'"version": "{VERSION}",', "package.json: bump version field")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Added a personal "My tickets" summary to the Overview page, showing status counts for cases you are personally assigned to, reported, or have completed/closed
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
