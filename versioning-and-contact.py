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

VERSION = "2.0.1"
TODAY = date.today().isoformat()

# ---------- lib/version.ts (new file) ----------
version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    print("SKIP: lib/version.ts already exists — not overwriting.")
else:
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: created lib/version.ts with APP_VERSION={VERSION}")

# ---------- package.json: keep version in sync (best-effort) ----------
replace_once('package.json',
    '"version": "2.0.0",',
    f'"version": "{VERSION}",',
    "package.json: bump version field")

# ---------- CHANGELOG.md (new file) ----------
changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Added dashboard "Updated" timestamp row, editable priority dropdown, and a visible "Reopened xN" flag
- Ticket detail page now shows the reporter's actual first photo, falling back to the PaveLedger logo when none is uploaded yet
- Added automated dashcam detection: Vehicle role, radius-based dedupe, automatic contractor/warranty tagging, automatic least-loaded-analyst assignment
- Footer now shows the app version and a Contact form
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" in existing:
        print(f"SKIP: CHANGELOG.md already has an entry for {VERSION}")
    else:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to existing CHANGELOG.md")
else:
    changelog_path.write_text(f"# Changelog\n\n{entry}")
    print(f"OK: created CHANGELOG.md with {VERSION} entry")

# ---------- app/workspace.tsx: import APP_VERSION ----------
replace_once('app/workspace.tsx',
    "import {State,Member,Ticket,colors,statuses,transitions,permitted,nextStages,eligibleVerification,roles,isActive} from '@/lib/domain';",
    "import {State,Member,Ticket,colors,statuses,transitions,permitted,nextStages,eligibleVerification,roles,isActive} from '@/lib/domain';\nimport {APP_VERSION} from '@/lib/version';",
    "workspace.tsx: import APP_VERSION")

# ---------- app/workspace.tsx: add contactOpen state ----------
replace_once('app/workspace.tsx',
    "const [data,setData]=useState<Data|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[view,setView]=useState('Overview'),[persona,setPersona]=useState('owner'),[q,setQ]=useState(''),[filter,setFilter]=useState('all'),[selected,setSelected]=useState<string|null>(null),[create,setCreate]=useState(false),[memberOpen,setMemberOpen]=useState(false),[teamOpen,setTeamOpen]=useState(false),[editingMember,setEditingMember]=useState<Member|null>(null),[contractOpen,setContractOpen]=useState(false);",
    "const [data,setData]=useState<Data|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[view,setView]=useState('Overview'),[persona,setPersona]=useState('owner'),[q,setQ]=useState(''),[filter,setFilter]=useState('all'),[selected,setSelected]=useState<string|null>(null),[create,setCreate]=useState(false),[memberOpen,setMemberOpen]=useState(false),[teamOpen,setTeamOpen]=useState(false),[editingMember,setEditingMember]=useState<Member|null>(null),[contractOpen,setContractOpen]=useState(false),[contactOpen,setContactOpen]=useState(false);",
    "workspace.tsx: add contactOpen state")

# ---------- app/workspace.tsx: footer with version + contact button ----------
replace_once('app/workspace.tsx',
    '<footer className="app-footer"><span>PaveLedger · Road intelligence and repair accountability</span><a href="/concept">Concept, subscriptions & pilot <ArrowUpRight size={14}/></a></footer>',
    '<footer className="app-footer"><span>PaveLedger · Road intelligence and repair accountability · v{APP_VERSION}</span><div className="footer-links"><button className="text-button" onClick={()=>setContactOpen(true)}>Contact</button><a href="/concept">Concept, subscriptions & pilot <ArrowUpRight size={14}/></a></div></footer>',
    "workspace.tsx: footer shows version and Contact button")

# ---------- app/workspace.tsx: Contact dialog ----------
replace_once('app/workspace.tsx',
    '<Dialog open={teamOpen} onOpenChange={setTeamOpen}>',
    '''<Dialog open={contactOpen} onOpenChange={setContactOpen}><DialogContent><DialogHeader><DialogTitle>Contact PaveLedger</DialogTitle><DialogDescription>Send us a message. This opens your email app addressed to paveledger@gmail.com.</DialogDescription></DialogHeader><form className="form" onSubmit={e=>{e.preventDefault();const f=new FormData(e.currentTarget);const subject=encodeURIComponent('PaveLedger contact: '+f.get('name'));const body=encodeURIComponent(String(f.get('message'))+'\\n\\nFrom: '+f.get('name')+' ('+f.get('email')+')');window.location.href='mailto:paveledger@gmail.com?subject='+subject+'&body='+body;setContactOpen(false)}}><label>Your name<input name="name" required/></label><label>Your email<input name="email" type="email" required/></label><label>Message<textarea name="message" required placeholder="How can we help?"/></label><button className="primary">Send message</button></form></DialogContent></Dialog>
<Dialog open={teamOpen} onOpenChange={setTeamOpen}>''',
    "workspace.tsx: add Contact dialog")

print("\nDone. Now run:")
print("  git diff")
print("  npm run build")
