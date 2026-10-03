import pathlib, re
from datetime import date

VERSION = "2.6.2"
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

# ---------- lib/domain.ts: State gets teamProfiles ----------
replace_once('lib/domain.ts',
    "export type State={tickets:Ticket[],members:Member[],teams:string[],rolePermissions?:Record<string,string[]>,branding?:{logoData?:string,logoMime?:string,slogan?:string},",
    "export type State={tickets:Ticket[],members:Member[],teams:string[],teamProfiles?:Record<string,{logo?:string,email?:string,phone?:string}>,rolePermissions?:Record<string,string[]>,branding?:{logoData?:string,logoMime?:string,slogan?:string},",
    "domain.ts: State gets teamProfiles")

# ---------- lib/actions.ts: teamUpdate also saves logo/email/phone, carried across a rename ----------
replace_once('lib/actions.ts',
    "s.teams=s.teams.map(x=>x===oldName?newName:x);s.members.forEach(m=>{if(m.teams?.includes(oldName))m.teams=m.teams.map(x=>x===oldName?newName:x)});s.tickets.forEach(t=>{if(t.team===oldName)t.team=newName});event='Team renamed: '+oldName+' -> '+newName;",
    "s.teams=s.teams.map(x=>x===oldName?newName:x);s.members.forEach(m=>{if(m.teams?.includes(oldName))m.teams=m.teams.map(x=>x===oldName?newName:x)});s.tickets.forEach(t=>{if(t.team===oldName)t.team=newName});const existingProfile=s.teamProfiles?.[oldName]||{};const profileEmail=typeof body.email==='string'?body.email.trim():existingProfile.email;const profilePhone=typeof body.phone==='string'?body.phone.trim():existingProfile.phone;const profileLogo=typeof body.logo==='string'&&body.logo?body.logo:existingProfile.logo;if(profileLogo&&profileLogo.length>700_000)throw new AppError('Team logo is too large. Use an image under 500 KB.');s.teamProfiles=s.teamProfiles||{};if(oldName!==newName)delete s.teamProfiles[oldName];s.teamProfiles[newName]={...(profileEmail?{email:profileEmail}:{}),...(profilePhone?{phone:profilePhone}:{}),...(profileLogo?{logo:profileLogo}:{})};event='Team updated: '+oldName+(oldName!==newName?' -> '+newName:'');",
    "actions.ts: teamUpdate saves profile fields")

# ---------- lib/actions.ts: teamDelete cleans up the profile too ----------
replace_once('lib/actions.ts',
    "s.teams=s.teams.filter(x=>x!==name);event='Team deleted: '+name;",
    "s.teams=s.teams.filter(x=>x!==name);if(s.teamProfiles)delete s.teamProfiles[name];event='Team deleted: '+name;",
    "actions.ts: teamDelete removes the stored profile")

# ---------- lib/context.ts: expose teamProfiles ----------
replace_once('lib/context.ts',
    "return {...s,tickets,members,rolePermissions:s.rolePermissions||{},branding:s.branding||{},teams:",
    "return {...s,tickets,members,rolePermissions:s.rolePermissions||{},branding:s.branding||{},teamProfiles:s.teamProfiles||{},teams:",
    "context.ts: expose teamProfiles in the client payload")

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
- Teams can now have a logo, contact email, and phone number, set via Edit team; carried over correctly if the team is renamed, cleaned up if deleted
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nRun the frontend script next, then build once.")
