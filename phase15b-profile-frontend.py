import pathlib, re
from datetime import date

VERSION = "2.6.1"
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

WP = 'app/workspace.tsx'

# ---------- 1. Import DropdownMenu components ----------
replace_once(WP,
    "import {Checkbox} from '@/components/ui/checkbox';",
    "import {Checkbox} from '@/components/ui/checkbox';\nimport {DropdownMenu,DropdownMenuTrigger,DropdownMenuContent,DropdownMenuLabel,DropdownMenuItem,DropdownMenuSeparator} from '@/components/ui/dropdown-menu';",
    "workspace.tsx: import DropdownMenu components")

# ---------- 2. Replace the bare Sign out button with a user dropdown ----------
replace_once(WP,
    '<button className="text-button" onClick={async()=>{localStorage.removeItem(\'paveledger-login-at\');const {error}=await browserClient().auth.signOut();if(error)toast.error("Could not sign out. Please retry.")}}>Sign out</button>',
    '''<DropdownMenu><DropdownMenuTrigger asChild><button className="text-button">{data?.viewer.profileImage?<img src={data.viewer.profileImage} alt="" style={{width:20,height:20,borderRadius:'50%',objectFit:'cover',marginRight:6,verticalAlign:'middle'}}/>:null}{data?.viewer.name||'Account'}</button></DropdownMenuTrigger><DropdownMenuContent align="end">{data?.viewer.status&&<DropdownMenuLabel>{data.viewer.status}</DropdownMenuLabel>}<DropdownMenuItem onClick={()=>setProfileOpen(true)}>Edit profile</DropdownMenuItem><DropdownMenuSeparator/><DropdownMenuItem onClick={async()=>{localStorage.removeItem('paveledger-login-at');const {error}=await browserClient().auth.signOut();if(error)toast.error("Could not sign out. Please retry.")}}>Sign out</DropdownMenuItem></DropdownMenuContent></DropdownMenu>''',
    "workspace.tsx: topbar shows user name/photo/status with a dropdown menu")

# ---------- 3. Extend the My profile dialog: status, phone, photo, email change ----------
replace_once(WP,
    '''<Dialog open={profileOpen} onOpenChange={setProfileOpen}><DialogContent style={{maxHeight:'85vh',overflowY:'auto'}}><DialogHeader><DialogTitle>My profile</DialogTitle><DialogDescription>Update your display name or password. Email cannot be changed here.</DialogDescription></DialogHeader><form className="form" onSubmit={async e=>{e.preventDefault();const f=new FormData(e.currentTarget);const name=String(f.get('name')||'').trim();const pw=String(f.get('password')||'');const pw2=String(f.get('password2')||'');if(name&&name!==data?.viewer.name){await mutate({action:'selfProfile',name})}if(pw){if(pw!==pw2){toast.error('Passwords do not match');return}if(pw.length<8){toast.error('Password must be at least 8 characters');return}const {error}=await browserClient().auth.updateUser({password:pw});if(error)toast.error(error.message);else toast.success('Password updated')}setProfileOpen(false)}}><label>Display name<input name="name" defaultValue={data?.viewer.name} required/></label><label>Email<input value={data?.viewer.email||''} disabled/></label><label>New password (leave blank to keep current)<input name="password" type="password" minLength={8}/></label><label>Confirm new password<input name="password2" type="password" minLength={8}/></label><button className="primary" disabled={busy}>Save changes</button></form></DialogContent></Dialog>''',
    '''<Dialog open={profileOpen} onOpenChange={setProfileOpen}><DialogContent style={{maxHeight:'85vh',overflowY:'auto'}}><DialogHeader><DialogTitle>My profile</DialogTitle><DialogDescription>Update your profile, status, and password.</DialogDescription></DialogHeader><form className="form" onSubmit={async e=>{e.preventDefault();const fd=new FormData(e.currentTarget);const name=String(fd.get('name')||'').trim();const status=String(fd.get('status')||'');const phone=String(fd.get('phone')||'');const pw=String(fd.get('password')||'');const pw2=String(fd.get('password2')||'');const file=fd.get('photo') as File;const payload:any={action:'selfProfile',name,status,phone};if(file&&file.size>0){if(file.size>500_000){toast.error('Profile photo must be under 500 KB');return}const dataUrl=await new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result));reader.onerror=reject;reader.readAsDataURL(file)});payload.photoData=dataUrl}await mutate(payload);if(pw){if(pw!==pw2){toast.error('Passwords do not match');return}if(pw.length<8){toast.error('Password must be at least 8 characters');return}const {error}=await browserClient().auth.updateUser({password:pw});if(error)toast.error(error.message);else toast.success('Password updated')}setProfileOpen(false)}}><label>Display name<input name="name" defaultValue={data?.viewer.name} required/></label><label>Status<input name="status" list="statusPresets" defaultValue={data?.viewer.status||''} placeholder="e.g. In office" maxLength={100}/><datalist id="statusPresets"><option value="In office"/><option value="Work from home"/><option value="On vacation"/><option value="Out sick"/><option value="Do not disturb"/></datalist></label><label>Phone number<input name="phone" type="tel" defaultValue={data?.viewer.phone||''}/></label><label>Profile photo (under 500 KB)<input name="photo" type="file" accept="image/png,image/jpeg,image/webp"/></label><label>New password (leave blank to keep current)<input name="password" type="password" minLength={8}/></label><label>Confirm new password<input name="password2" type="password" minLength={8}/></label><button className="primary" disabled={busy}>Save changes</button></form><div className="form"><h3>Change email</h3><p className="footnote">Current: {data?.viewer.email}. Changing this sends a confirmation link to the new address.</p><form onSubmit={async e=>{e.preventDefault();const fd=new FormData(e.currentTarget);const newEmail=String(fd.get('newEmail')||'').trim();if(!newEmail)return;const {error}=await browserClient().auth.updateUser({email:newEmail});if(error)toast.error(error.message);else toast.success('Confirmation email sent. Your email updates once confirmed.')}}><label>New email<input name="newEmail" type="email" required/></label><button className="secondary" disabled={busy}>Update email</button></form></div></DialogContent></Dialog>''',
    "workspace.tsx: extend My profile dialog with status/phone/photo/email")

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
- The topbar now shows the signed-in user's name/photo/status with a dropdown (Edit profile, Sign out) instead of a bare Sign out button
- My profile now includes a status message (with presets: In office, Work from home, On vacation, Out sick, Do not disturb), phone number, profile photo, and self-service email change (sends a confirmation link)
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Now run:")
print("  npm run build")
