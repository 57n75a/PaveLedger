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

VERSION = "2.1.8"
TODAY = date.today().isoformat()

# ---------- 1. MemberForm: add phone field ----------
replace_once('app/workspace.tsx',
    '''<label>Sign-in email<input required type="email" name="email" defaultValue={initial?.email}/></label>''',
    '''<label>Sign-in email<input required type="email" name="email" defaultValue={initial?.email}/></label><label>Phone number<input name="phone" type="tel" defaultValue={initial?.phone||''} placeholder="e.g. +1 555 123 4567"/></label>''',
    "workspace.tsx: MemberForm phone field")

# ---------- 2. Contract create dialog: phone/address/country ----------
replace_once('app/workspace.tsx',
    '''{['contractor','road','scope','poc','email'].map(x=><label key={x}>{({contractor:'Contractor firm',road:'Road name',scope:'Work scope and location limits',poc:'Point of contact',email:'Contact email'} as Record<string,string>)[x]}<input name={x} required type={x==='email'?'email':'text'}/></label>)}<div className="two-cols"><label>Warranty begins<input name="start" type="date" required/></label><label>Warranty ends<input name="end" type="date" required/></label></div>''',
    '''{['contractor','phone','road','scope','poc','email'].map(x=><label key={x}>{({contractor:'Contractor firm',phone:'Phone number',road:'Road name',scope:'Work scope and location limits',poc:'Point of contact',email:'Contact email'} as Record<string,string>)[x]}<input name={x} required={x!=='phone'} type={x==='email'?'email':x==='phone'?'tel':'text'}/></label>)}<label>Address<input name="address" placeholder="Street, city"/></label><label>Country or region<select name="addressCountry" defaultValue="USA"><option value="USA">USA</option><option value="CAN">Canada</option><option value="Europe">Europe</option></select></label><div className="two-cols"><label>Warranty begins<input name="start" type="date" required/></label><label>Warranty ends<input name="end" type="date" required/></label></div>''',
    "workspace.tsx: contract create dialog phone/address/country")

# ---------- 3. Contract edit dialog: phone/address/country ----------
replace_once('app/workspace.tsx',
    '''{['contractor','road','scope','poc','email'].map(x=><label key={x}>{({contractor:'Contractor firm',road:'Road name',scope:'Work scope and location limits',poc:'Point of contact',email:'Contact email'} as Record<string,string>)[x]}<input name={x} required defaultValue={(editingContract as any)[x]} type={x==='email'?'email':'text'}/></label>)}<div className="two-cols"><label>Warranty begins<input name="start" type="date" required defaultValue={editingContract.start}/></label><label>Warranty ends<input name="end" type="date" required defaultValue={editingContract.end}/></label></div>''',
    '''{['contractor','phone','road','scope','poc','email'].map(x=><label key={x}>{({contractor:'Contractor firm',phone:'Phone number',road:'Road name',scope:'Work scope and location limits',poc:'Point of contact',email:'Contact email'} as Record<string,string>)[x]}<input name={x} required={x!=='phone'} defaultValue={(editingContract as any)[x]||''} type={x==='email'?'email':x==='phone'?'tel':'text'}/></label>)}<label>Address<input name="address" defaultValue={editingContract.address||''} placeholder="Street, city"/></label><label>Country or region<select name="addressCountry" defaultValue={editingContract.addressCountry||'USA'}><option value="USA">USA</option><option value="CAN">Canada</option><option value="Europe">Europe</option></select></label><div className="two-cols"><label>Warranty begins<input name="start" type="date" required defaultValue={editingContract.start}/></label><label>Warranty ends<input name="end" type="date" required defaultValue={editingContract.end}/></label></div>''',
    "workspace.tsx: contract edit dialog phone/address/country")

# ---------- 4. Ticket Detail hero: Google Maps embed fallback when no photo ----------
replace_once('app/workspace.tsx',
    '''<div className="evidence"><img src={photoUrl||'/logo.png'} alt={photoUrl?'Reported photograph':'PaveLedger logo — no photograph uploaded yet'} style={photoUrl?{width:'100%',maxHeight:280,objectFit:'cover'}:{width:'100%',maxHeight:280,objectFit:'contain',background:'#f4f6f8',padding:24}}/>{!photoUrl&&<span>No photograph uploaded yet</span>}</div>''',
    '''<div className="evidence">{photoUrl?<img src={photoUrl} alt="Reported photograph" style={{width:'100%',maxHeight:280,objectFit:'cover'}}/>:<iframe title="Ticket location" src={`https://www.google.com/maps?q=${t.lat},${t.lng}&z=16&output=embed`} style={{width:'100%',height:280,border:0}} loading="lazy"/>}{!photoUrl&&<span>Showing reported location \u2014 no photograph uploaded yet</span>}</div>''',
    "workspace.tsx: Detail hero falls back to Maps embed instead of logo")

# ---------- 5. Overview HeroTicket: same Maps embed fallback ----------
replace_once('app/workspace.tsx',
    '''return <section className="feature-card"><div className="image-wrap"><img src={url||'/logo.png'} alt={url?'Top priority case photograph':'PaveLedger logo'} style={url?{objectFit:'cover'}:{objectFit:'contain',padding:24,background:'#f4f6f8'}}/><span className="image-label">TOP PRIORITY CASE</span></div>''',
    '''return <section className="feature-card"><div className="image-wrap">{url?<img src={url} alt="Top priority case photograph" style={{objectFit:'cover',width:'100%',height:'100%'}}/>:<iframe title="Top priority case location" src={`https://www.google.com/maps?q=${ticket.lat},${ticket.lng}&z=16&output=embed`} style={{width:'100%',height:'100%',border:0}} loading="lazy"/>}<span className="image-label">TOP PRIORITY CASE</span></div>''',
    "workspace.tsx: HeroTicket falls back to Maps embed instead of logo")

# ---------- version + changelog ----------
version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

replace_once('package.json', '"version": "2.1.7",', f'"version": "{VERSION}",', "package.json: bump version field")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Added phone number field to the member form, and phone/address/country fields to contract create and edit forms
- New tickets now default to a live Google Maps embed of the reported location (free, no API key) instead of the logo, until a photo is uploaded
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
