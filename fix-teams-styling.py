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

VERSION = "2.1.4"
TODAY = date.today().isoformat()

replace_once('app/workspace.tsx',
    '''<div className="team-grid">{data.teams.map(team=><div className="panel-mini" key={team}><h3>{team}</h3><small>{data.members.filter(m=>m.team===team&&isActive(m)).length} active members</small></div>)}{!data.teams.length&&<p className="muted">No teams created yet.</p>}</div>''',
    '''<div className="team-grid" style={{display:'grid',gridTemplateColumns:'repeat(auto-fill, minmax(220px, 1fr))',gap:16}}>{data.teams.map(team=>{const count=data.members.filter(m=>m.team===team&&isActive(m)).length;return <div key={team} style={{border:'1px solid #e5e7eb',borderRadius:12,padding:'16px 18px',background:'#f8f9fb',display:'flex',flexDirection:'column',gap:6}}><strong style={{fontSize:15}}>{team}</strong><span style={{fontSize:13,color:'#6b7280'}}>{count} active member{count===1?'':'s'}</span></div>})}{!data.teams.length&&<p className="muted">No teams created yet.</p>}</div>''',
    "workspace.tsx: Teams page as a proper card grid")

version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

replace_once('package.json', '"version": "2.1.3",', f'"version": "{VERSION}",', "package.json: bump version field")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Reformatted the Teams page into a clean card grid (previously plain unstyled text)
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
