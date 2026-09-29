import pathlib, re
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

VERSION = "2.3.2"
TODAY = date.today().isoformat()

# ---------- 1. Backend: only team members or Admin can add a stand-alone comment/note ----------
replace_once('lib/actions.ts',
    "}else if(action==='note'){requireRole(['Admin','Team lead','Analyst','Reviewer','Contractor']);noteField.parse(note);",
    "}else if(action==='note'){requireRole(['Admin','Team lead','Analyst','Head Analyst','Reviewer']);noteField.parse(note);",
    "actions.ts: note action restricted to team members and Admin (drops Contractor)")

# ---------- 2. Frontend: hide the 'Add note' button from roles that can no longer use it ----------
replace_once('app/workspace.tsx',
    '''<button disabled={busy} className="secondary" onClick={async()=>{if(await mutate({action:'note',id:t.id,note,visibility:shared?'shared':'internal'}))setNote('')}}>Add note</button>''',
    '''{['Admin','Team lead','Analyst','Head Analyst','Reviewer'].includes(data.viewer.role)&&<button disabled={busy} className="secondary" onClick={async()=>{if(await mutate({action:'note',id:t.id,note,visibility:shared?'shared':'internal'}))setNote('')}}>Add note</button>}''',
    "workspace.tsx: hide Add note button from Contractor")

# ---------- 3. Nav: rename Roles to Users and Roles ----------
replace_once('app/workspace.tsx',
    "{name:'Roles',icon:ShieldCheck}",
    "{name:'Users and Roles',icon:ShieldCheck}",
    "workspace.tsx: nav item renamed to Users and Roles")

replace_once('app/workspace.tsx',
    "{view==='Roles'&&<section",
    "{view==='Users and Roles'&&<section",
    "workspace.tsx: view conditional renamed to Users and Roles")

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
- Stand-alone comments on a ticket's activity are now restricted to team members and Admin (Contractor can still comment when moving a stage they're permitted to, since that comment is part of the transition itself)
- Renamed the "Roles" section to "Users and Roles"
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Now run:")
print("  npm run build")
