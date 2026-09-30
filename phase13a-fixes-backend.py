import pathlib, re
from datetime import date

VERSION = "2.4.2"
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

def replace_all(path, old, new, label, expected_min=1):
    p = pathlib.Path(path)
    text = p.read_text()
    count = text.count(old)
    if count < expected_min:
        print(f"SKIP ({count} matches, expected at least {expected_min}): {label} in {path}")
        return False
    p.write_text(text.replace(old, new))
    print(f"OK: {label} ({count} occurrence(s))")
    return True

A = 'lib/actions.ts'

# ---------- 1. Scope is now optional (was blocking contract creation when relying on the map radius) ----------
replace_all(A,
    "scope:z.string().trim().min(10).max(2000)",
    "scope:z.string().trim().max(2000).optional().transform(x=>x?.trim()||'')",
    "actions.ts: scope is optional in contract create + contractUpdate schemas",
    expected_min=2)

# ---------- 2. Only Admin can create or modify a Vehicle account ----------
replace_once(A,
    "requireRole(['Admin','Team lead','Director']);if(actual.id!==m.id)throw new AppError('Return to your own identity before changing access.',403);",
    "requireRole(['Admin','Team lead','Director']);if(actual.id!==m.id)throw new AppError('Return to your own identity before changing access.',403);\n  if(String(body.role)==='Vehicle'&&m.role!=='Admin')throw new AppError('Only an administrator can create or modify Vehicle accounts.',403);",
    "actions.ts: Vehicle accounts restricted to Admin")

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
- Fixed: contract scope field was requiring 10+ characters even when a map radius already defined coverage; it's now optional
- Only an Admin can create or modify a Vehicle account (Team lead/Director can still manage other roles)
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nRun the frontend script next, then build once.")
