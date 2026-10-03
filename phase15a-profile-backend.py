import pathlib, re
from datetime import date

VERSION = "2.6.0"
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

# ---------- lib/domain.ts: Member gets status and profileImage ----------
replace_once('lib/domain.ts',
    "vehicleTag?:string;notifyPrefs?:Record<string,boolean>;phone?:string;active?:boolean;authUserId?:string;demo?:boolean};",
    "vehicleTag?:string;notifyPrefs?:Record<string,boolean>;phone?:string;status?:string;profileImage?:string;active?:boolean;authUserId?:string;demo?:boolean};",
    "domain.ts: Member gets status and profileImage")

# ---------- lib/actions.ts: selfProfile accepts status, phone, photoData ----------
replace_once('lib/actions.ts',
    "if(action==='selfProfile'){const name=short.parse(body.name);actual.name=name;s.events.unshift({at:now,actor,action:'Profile name updated: '+name});return}",
    "if(action==='selfProfile'){const name=short.parse(body.name);actual.name=name;if(typeof body.status==='string')actual.status=body.status.trim().slice(0,100);if(typeof body.phone==='string')actual.phone=body.phone.trim().slice(0,40);if(typeof body.photoData==='string'&&body.photoData){if(body.photoData.length>700_000)throw new AppError('Profile photo is too large. Use an image under 500 KB.');actual.profileImage=body.photoData;}s.events.unshift({at:now,actor,action:'Profile name updated: '+name});return}",
    "actions.ts: selfProfile accepts status, phone, photoData")

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
- Added self-service status message, phone number, and profile photo (stored inline, under 500 KB) to the self-profile action
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nRun the frontend script next, then build once.")
