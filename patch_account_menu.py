#!/usr/bin/env python3
"""Account menu: Settings, Notifications, Theme, Help, FAQ, Logout (+ FAQ dialog).
Run from the repo root. Aborts without writing if any anchor is not found exactly once."""
import re, sys, json, datetime

WS = 'app/workspace.tsx'
VERSION = 'lib/version.ts'
CHANGELOG = 'CHANGELOG.md'

def die(msg):
    print('ABORT: ' + msg); sys.exit(1)

def read(p):
    try:
        return open(p, encoding='utf-8').read()
    except FileNotFoundError:
        die(p + ' not found (run from repo root)')

def swap(src, old, new, label):
    n = src.count(old)
    if n != 1:
        die(f'{label}: anchor found {n} times (expected 1)')
    return src.replace(old, new)

w = read(WS)

# 1. new state for the FAQ dialog
w = swap(w,
  "[importOpen,setImportOpen]=useState(false);",
  "[importOpen,setImportOpen]=useState(false),[faqOpen,setFaqOpen]=useState(false);",
  'faq state')

# 2. account menu: replace the single "Edit profile" item with the full set
w = swap(w,
  "<DropdownMenuItem onClick={()=>setProfileOpen(true)}>Edit profile</DropdownMenuItem>",
  "<DropdownMenuItem onClick={()=>setProfileOpen(true)}>Settings</DropdownMenuItem>"
  "<DropdownMenuItem onClick={()=>setNotifyOpen(true)}>Notifications</DropdownMenuItem>"
  "<DropdownMenuItem onClick={()=>setTheme(t=>t==='dark'?'light':'dark')}>Theme: switch to {theme==='dark'?'light':'dark'}</DropdownMenuItem>"
  "<DropdownMenuItem onClick={()=>setContactOpen(true)}>Help</DropdownMenuItem>"
  "<DropdownMenuItem onClick={()=>setFaqOpen(true)}>FAQ</DropdownMenuItem>",
  'account menu items')

# 3. Sign out -> Logout (clears stored session state, signs out, returns to the start page)
w = swap(w,
  """<DropdownMenuItem onClick={async()=>{localStorage.removeItem('paveledger-login-at');const {error}=await browserClient().auth.signOut();if(error)toast.error("Could not sign out. Please retry.")}}>Sign out</DropdownMenuItem>""",
  """<DropdownMenuItem onClick={async()=>{try{localStorage.removeItem('paveledger-login-at');sessionStorage.clear()}catch{}const {error}=await browserClient().auth.signOut();if(error){toast.error("Could not sign out. Please retry.");return}window.location.href='/'}}>Logout</DropdownMenuItem>""",
  'logout item')

# 4. retitle the profile dialog as Settings (it already has phone, email and password)
w = swap(w,
  "<DialogTitle>My profile</DialogTitle><DialogDescription>Update your profile, status, and password.</DialogDescription>",
  "<DialogTitle>Settings</DialogTitle><DialogDescription>Update your profile, phone, email, and password.</DialogDescription>",
  'settings dialog title')

# 5. FAQ dialog, inserted before the contact dialog
FAQ = [
 ("What is PaveLedger?", "A pilot workspace for tracking road defects such as potholes from first report to verified repair, with an activity record for every ticket."),
 ("How do I find my way around?", "Use the left sidebar: Overview, Tickets, Analytics, Contracts, Teams, Users and Roles, and Notifications. Admin, Team lead and Director also see Archive."),
 ("How do I create a ticket?", "Admin, Team lead and Analyst see a New ticket button at the top of the page. Enter the road, location and severity, then save."),
 ("What do the Tickets table columns mean?", "Contractor shows the contractor tagged to the ticket, or Unassigned until a contract covers it. Observations is how many times the defect has been reported or detected."),
 ("How do I search?", "Use the search box at the top. It searches tickets, contracts and evidence, and clicking a result opens the ticket."),
 ("How do I export tickets?", "Use the Export CSV and Export PDF buttons above the tickets table. The export follows the filters you have set."),
 ("What is the Archive?", "Archiving hides a ticket from the active lists without deleting it. Archived tickets stay in the Archive view for Admin, Team lead and Director."),
 ("What does escalate do?", "Escalating passes a ticket up the chain: Head Analyst to Team lead, then Team lead to Director. The button appears on the ticket if your role allows it."),
 ("How are contractors tagged to tickets?", "Each contract covers a street list and a map radius. A ticket inside a contract's scope is tagged to that contractor. Manage this under Contracts."),
 ("How do I add many contracts at once?", "Use the import option in Contracts. XLSX, CSV and XML files are supported, with column mapping. PDF import is not supported."),
 ("What are vehicle accounts?", "A Vehicle account is for a camera-equipped vehicle. It reports defects with GPS, the street is looked up automatically, and nearby duplicates are merged into one ticket."),
 ("What happens when a vehicle finds a defect has been fixed?", "The ticket becomes pending closure and is closed and archived automatically after 7 days."),
 ("What do the roles mean?", "Admin manages everything. Team lead runs a team. Analysts and Head Analysts work tickets. Reviewers, Auditors and Directors oversee. Contractors see their own work. Vehicle is for automated reporting."),
 ("Who can change what each role can do?", "Admins, under Users and Roles, Roles tab. Some safeguards are fixed and cannot be changed, such as granting Admin and closing tickets."),
 ("How do I change my password?", "Open the account menu at the top right, choose Settings, enter a new password twice, and save. It must be at least 8 characters."),
 ("How do I change my email address?", "Open Settings and use Change email. A confirmation link is sent to the new address, and your email updates once you confirm it."),
 ("How do I change my phone number or photo?", "Open Settings. You can update your display name, status, phone number and a profile photo under 500 KB."),
 ("How do I control which notifications I get?", "Open the account menu and choose Notifications. You can switch alerts on or off for assignments, status changes and manual edits."),
 ("How do I switch between light and dark mode?", "Use the sun or moon button at the top, or choose Theme in the account menu. The app remembers your choice on this device."),
 ("How do I contact support?", "Choose Help in the account menu, or Contact in the page footer. Fill in your name, email and message and it opens an email to paveledger@gmail.com."),
 ("How do I log out?", "Open the account menu and choose Logout. You are signed out and returned to the start page. You are also signed out automatically after 24 hours."),
 ("Why can I not see a menu item or button?", "What you see depends on your role. If you need access to something, ask an Admin to review your role."),
]
items = ''.join(
    '<details style={{marginBottom:10}}><summary style={{cursor:"pointer",fontWeight:600}}>{'
    + json.dumps(q) + '}</summary><p className="muted" style={{margin:"6px 0 0"}}>{'
    + json.dumps(a) + '}</p></details>'
    for q, a in FAQ)
faq_dialog = ("<Dialog open={faqOpen} onOpenChange={setFaqOpen}><DialogContent style={{maxHeight:'85vh',overflowY:'auto'}}>"
              "<DialogHeader><DialogTitle>FAQ</DialogTitle><DialogDescription>Quick answers to help you get around PaveLedger.</DialogDescription></DialogHeader>"
              "<div>" + items + "</div></DialogContent></Dialog>\n")
w = swap(w,
  "<Dialog open={contactOpen} onOpenChange={setContactOpen}>",
  faq_dialog + "<Dialog open={contactOpen} onOpenChange={setContactOpen}>",
  'faq dialog insert')

# 6. clearer wording for tickets with no contractor tagged
n_un = w.count("t.contractor||'Unassigned'")
if n_un < 1:
    die("no t.contractor||'Unassigned' found")
w = w.replace("t.contractor||'Unassigned'", "t.contractor||'No contractor'")

# version + changelog
v = read(VERSION)
found = re.findall(r'\d+\.\d+\.\d+', v)
if len(found) != 1:
    die(f'{VERSION}: expected exactly one x.y.z, found {found}')
old_v = found[0]
maj, mnr, pat = map(int, old_v.split('.'))
new_v = f'{maj}.{mnr}.{pat + 1}'
v = v.replace(old_v, new_v)

c = read(CHANGELOG)
m = re.search(r'^## .*$', c, re.M)
if not m:
    die(f'{CHANGELOG}: no "## " heading found to insert before')
print('Top existing changelog heading:', m.group(0))
entry = (f'## {new_v} - {datetime.date.today().isoformat()}\n'
         '- Account menu now has Settings, Notifications, Theme, Help, FAQ and Logout.\n'
         '- New FAQ dialog with 22 entries.\n'
         '- Logout clears stored session state and returns to the start page.\n'
         '- Tickets with no tagged contractor now read "No contractor" instead of "Unassigned".\n\n')
c = c[:m.start()] + entry + c[m.start():]

open(WS, 'w', encoding='utf-8').write(w)
open(VERSION, 'w', encoding='utf-8').write(v)
open(CHANGELOG, 'w', encoding='utf-8').write(c)
print(f'OK: {old_v} -> {new_v} ("Unassigned" replaced {n_un}x). Now run: npm run build')
