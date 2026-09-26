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

VERSION = "2.0.4"
TODAY = date.today().isoformat()

# ---------- lib/domain.ts: archived fields ----------

replace_once('lib/domain.ts',
    "lane?:string;contractId?:string;reportedBy?:string;escalatedTo?:string;duplicateOf?:string;",
    "lane?:string;contractId?:string;reportedBy?:string;escalatedTo?:string;archived?:boolean;archiveRequested?:boolean;duplicateOf?:string;",
    "domain.ts: add archived and archiveRequested to Ticket type")

# ---------- lib/actions.ts: archive/unarchive/requestArchive actions ----------

replace_once('lib/actions.ts',
    "event='Escalated to '+targetRole;}",
    "event='Escalated to '+targetRole;}else if(action==='archive'){requireRole(['Admin','Team lead','Director']);t.archived=true;t.archiveRequested=false;t.updated=now;event='Archived '+t.id;}else if(action==='unarchive'){requireRole(['Admin','Team lead','Director']);t.archived=false;t.updated=now;event='Unarchived '+t.id;}else if(action==='requestArchive'){requireRole(['Analyst','Head Analyst']);t.archiveRequested=true;t.updated=now;const recipients=s.members.filter(x=>isActive(x)&&['Team lead','Director','Admin'].includes(x.role)&&(x.role!=='Team lead'||x.team===t.team));recipients.forEach(r=>s.notifications.unshift({id:crypto.randomUUID(),recipient:r.id,ticket:t.id,text:`Archive requested: ${t.road}`,at:now}));event='Archive requested';}",
    "actions.ts: add archive, unarchive, requestArchive actions")

# ---------- app/workspace.tsx: archive controls on the ticket detail page ----------

replace_once('app/workspace.tsx',
    '<p className="footnote">{t.note}</p>',
    '<p className="footnote">{t.note}</p><div className="button-row">{t.archived?<><span className="muted">Archived</span>{[\'Admin\',\'Team lead\',\'Director\'].includes(data.viewer.role)&&<button className="secondary" disabled={busy} onClick={()=>mutate({action:\'unarchive\',id:t.id})}>Unarchive</button>}</>:<>{[\'Admin\',\'Team lead\',\'Director\'].includes(data.viewer.role)&&<button className="secondary" disabled={busy} onClick={()=>mutate({action:\'archive\',id:t.id})}>Archive case</button>}{[\'Analyst\',\'Head Analyst\'].includes(data.viewer.role)&&(t.archiveRequested?<span className="muted">Archive requested</span>:<button className="secondary" disabled={busy} onClick={()=>mutate({action:\'requestArchive\',id:t.id})}>Request archive</button>)}</>}</div>',
    "workspace.tsx: archive/unarchive/request-archive controls on ticket detail")

# ---------- version + changelog ----------

version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

replace_once('package.json', '"version": "2.0.3",', f'"version": "{VERSION}",', "package.json: bump version field")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Added archive as a flag (not a status): tickets are never deleted, only archived
- Admin, Team lead, and Director can archive/unarchive directly from the ticket page
- Analyst and Head Analyst can request archival, which notifies Team lead/Director/Admin
- Note: archived tickets still appear in the main dashboard for now -- hiding them and adding a dedicated Archive view is next
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
