import pathlib, re
from datetime import date

VERSION = "2.5.1"
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

# ---------- lib/domain.ts: branding on State ----------
replace_once('lib/domain.ts',
    "export type State={tickets:Ticket[],members:Member[],teams:string[],rolePermissions?:Record<string,string[]>,",
    "export type State={tickets:Ticket[],members:Member[],teams:string[],rolePermissions?:Record<string,string[]>,branding?:{logoData?:string,logoMime?:string,slogan?:string},",
    "domain.ts: State gets branding")

# ---------- lib/actions.ts: branding action (Admin only) ----------
replace_once('lib/actions.ts',
    "if(action==='selfProfile'){",
    "if(action==='branding'){requireRole(['Admin']);const slogan=typeof body.slogan==='string'?body.slogan.trim().slice(0,200):undefined;const logoData=typeof body.logoData==='string'?body.logoData:undefined;if(logoData&&logoData.length>700_000)throw new AppError('Logo image is too large. Use an image under 500 KB.');s.branding={...(s.branding||{}),...(slogan!==undefined?{slogan}:{}),...(logoData?{logoData,logoMime:typeof body.logoMime==='string'?body.logoMime:'image/png'}:{})};event='Branding updated';return}if(action==='selfProfile'){",
    "actions.ts: add branding action (Admin-only)")

# ---------- lib/context.ts: expose branding to the client ----------
replace_once('lib/context.ts',
    "return {...s,tickets,members,rolePermissions:s.rolePermissions||{},teams:",
    "return {...s,tickets,members,rolePermissions:s.rolePermissions||{},branding:s.branding||{},teams:",
    "context.ts: expose branding in the client payload")

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
- Added editable branding: Admin can replace the sidebar logo (stored inline, under 500 KB) and change the workspace slogan
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nRun the frontend script next, then build once.")
