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

VERSION = "2.1.0"
TODAY = date.today().isoformat()

# ---------- 1. Add new state: globalQuery, profileOpen, notifyOpen ----------
replace_once('app/workspace.tsx',
    "const [data,setData]=useState<Data|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[view,setView]=useState('Overview'),[persona,setPersona]=useState('owner'),[q,setQ]=useState(''),[filter,setFilter]=useState('all'),[selected,setSelected]=useState<string|null>(null),[create,setCreate]=useState(false),[memberOpen,setMemberOpen]=useState(false),[teamOpen,setTeamOpen]=useState(false),[editingMember,setEditingMember]=useState<Member|null>(null),[contractOpen,setContractOpen]=useState(false),[contactOpen,setContactOpen]=useState(false);",
    "const [data,setData]=useState<Data|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[view,setView]=useState('Overview'),[persona,setPersona]=useState('owner'),[q,setQ]=useState(''),[filter,setFilter]=useState('all'),[selected,setSelected]=useState<string|null>(null),[create,setCreate]=useState(false),[memberOpen,setMemberOpen]=useState(false),[teamOpen,setTeamOpen]=useState(false),[editingMember,setEditingMember]=useState<Member|null>(null),[contractOpen,setContractOpen]=useState(false),[contactOpen,setContactOpen]=useState(false),[globalQuery,setGlobalQuery]=useState(''),[profileOpen,setProfileOpen]=useState(false),[notifyOpen,setNotifyOpen]=useState(false);",
    "workspace.tsx: add globalQuery, profileOpen, notifyOpen state")

# ---------- 2. Derive global search results (after the filtered ticket list) ----------
replace_once('app/workspace.tsx',
    "const filtered=tickets.filter(t=>(filter==='all'||t.status===filter||(filter==='Urgent'&&t.severity==='Urgent')||(filter==='ReopenedEver'&&t.reopened>0))&&(t.id+' '+t.road+' '+t.title).toLowerCase().includes(q.toLowerCase()));",
    "const filtered=tickets.filter(t=>(filter==='all'||t.status===filter||(filter==='Urgent'&&t.severity==='Urgent')||(filter==='ReopenedEver'&&t.reopened>0))&&(t.id+' '+t.road+' '+t.title).toLowerCase().includes(q.toLowerCase()));\n const gq=globalQuery.trim().toLowerCase();\n const searchTickets=gq.length>=2?tickets.filter(t=>(t.id+' '+t.road+' '+t.title).toLowerCase().includes(gq)).slice(0,5):[];\n const searchContracts=gq.length>=2?(data?.contracts||[]).filter(c=>(c.id+' '+c.contractor+' '+c.road).toLowerCase().includes(gq)).slice(0,5):[];\n const searchEvidence=gq.length>=2?tickets.flatMap(t=>(t.evidence||[]).filter(e=>e.name.toLowerCase().includes(gq)).map(e=>({t,e}))).slice(0,5):[];",
    "workspace.tsx: derive global search results across tickets, contracts, evidence")

# ---------- 3. Add the search bar to the topbar ----------
replace_once('app/workspace.tsx',
    '''<header className="topbar"><div><SidebarTrigger/><span className="breadcrumb">Workspace / <b>{view}</b></span></div><div className="top-actions">''',
    '''<header className="topbar"><div><SidebarTrigger/><span className="breadcrumb">Workspace / <b>{view}</b></span></div><div style={{position:'relative',flex:1,display:'flex',justifyContent:'center'}}><div style={{position:'relative',width:'100%',maxWidth:420}}><input aria-label="Search everything" placeholder="Search investigations, contracts, evidence..." value={globalQuery} onChange={e=>setGlobalQuery(e.target.value)} style={{width:'100%'}}/>{gq.length>=2&&(searchTickets.length||searchContracts.length||searchEvidence.length)?<div style={{position:'absolute',top:'100%',left:0,right:0,background:'#fff',border:'1px solid #ddd',borderRadius:8,marginTop:4,maxHeight:320,overflowY:'auto',zIndex:50}}>{searchTickets.map(t=><button key={'t-'+t.id} className="queue-row" onClick={()=>{setSelected(t.id);setGlobalQuery('')}}><small>{t.id}</small><strong>{t.road}</strong><span>{t.title}</span></button>)}{searchContracts.map(c=><button key={'c-'+c.id} className="queue-row" onClick={()=>{setView('Contracts');setGlobalQuery('')}}><small>{c.id}</small><strong>{c.road}</strong><span>{c.contractor}</span></button>)}{searchEvidence.map(x=><button key={'e-'+x.e.id} className="queue-row" onClick={()=>{setSelected(x.t.id);setGlobalQuery('')}}><small>{x.t.id}</small><strong>{x.e.name}</strong><span>{x.e.purpose}</span></button>)}</div>:null}</div></div><div className="top-actions">''',
    "workspace.tsx: add global search bar to topbar")

# ---------- 4. Session timeout: 24h for everyone except Vehicle ----------
replace_once('app/workspace.tsx',
    "async function mutate(body:any){if(!data||busy)return false;setBusy(true);try{const r=await authorizedFetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,revision:data.revision})});const d:any=await r.json();if(!r.ok){if(r.status===409)await load();throw new Error(d.error)}setData(d);toast.success('Workspace updated');return true}catch(e){toast.error((e as Error).message);return false}finally{setBusy(false)}}",
    "async function mutate(body:any){if(!data||busy)return false;setBusy(true);try{const r=await authorizedFetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,revision:data.revision})});const d:any=await r.json();if(!r.ok){if(r.status===409)await load();throw new Error(d.error)}setData(d);toast.success('Workspace updated');return true}catch(e){toast.error((e as Error).message);return false}finally{setBusy(false)}}\nuseEffect(()=>{if(!data)return;if(data.viewer.role==='Vehicle')return;const key='paveledger-login-at';const stored=localStorage.getItem(key);const now=Date.now();if(!stored){localStorage.setItem(key,String(now));return}if(now-Number(stored)>24*60*60*1000){localStorage.removeItem(key);browserClient().auth.signOut()}},[data?.viewer.role]);",
    "workspace.tsx: 24h session timeout, Vehicle exempt")

# ---------- 5. Clear the session timestamp on manual sign-out ----------
replace_once('app/workspace.tsx',
    '''onClick={async()=>{const {error}=await browserClient().auth.signOut();if(error)toast.error("Could not sign out. Please retry.")}}>Sign out</button>''',
    '''onClick={async()=>{localStorage.removeItem('paveledger-login-at');const {error}=await browserClient().auth.signOut();if(error)toast.error("Could not sign out. Please retry.")}}>Sign out</button>''',
    "workspace.tsx: clear session timestamp on manual sign-out")

# ---------- 6. Make the sidebar profile clickable, opens the profile dialog ----------
replace_once('app/workspace.tsx',
    '''<SidebarFooter><div className="profile"><span className="avatar">{data?.viewer.name.slice(0,1)||'P'}</span><div><strong>{data?.viewer.name||'PaveLedger'}</strong><small>{role||'Private workspace'}</small></div></div></SidebarFooter>''',
    '''<SidebarFooter><div className="profile" role="button" tabIndex={0} style={{cursor:'pointer'}} onClick={()=>setProfileOpen(true)}><span className="avatar">{data?.viewer.name.slice(0,1)||'P'}</span><div><strong>{data?.viewer.name||'PaveLedger'}</strong><small>{role||'Private workspace'}</small></div></div></SidebarFooter>''',
    "workspace.tsx: sidebar profile opens profile dialog")

# ---------- 7. Preferences button on the Notifications view ----------
replace_once('app/workspace.tsx',
    '''{view==='Notifications'&&<section className="panel"><div className="section-head"><div><h2>Your notifications</h2><p>Assignment alerts for your current role</p></div></div>{!data.notifications.length?''',
    '''{view==='Notifications'&&<section className="panel"><div className="section-head"><div><h2>Your notifications</h2><p>Assignment alerts for your current role</p></div><button className="secondary" onClick={()=>setNotifyOpen(true)}>Preferences</button></div>{!data.notifications.length?''',
    "workspace.tsx: add Preferences button to Notifications view")

# ---------- 8. Teams & access: Team lead / Director can also edit access ----------
replace_once('app/workspace.tsx',
    '''<p>{role==='Admin'?'Bind verified accounts, set roles and suspend access.':'Membership shown within your permitted scope.'}</p>''',
    '''<p>{['Admin','Team lead','Director'].includes(role||'')?'Bind verified accounts, set roles and suspend access.':'Membership shown within your permitted scope.'}</p>''',
    "workspace.tsx: Teams & access description for Team lead/Director")

replace_once('app/workspace.tsx',
    '''<TableCell>{role==='Admin'&&<button className="secondary" onClick={()=>setEditingMember(m)}>Edit access</button>}</TableCell>''',
    '''<TableCell>{['Admin','Team lead','Director'].includes(role||'')&&<button className="secondary" onClick={()=>setEditingMember(m)}>Edit access</button>}</TableCell>''',
    "workspace.tsx: show Edit access button for Team lead/Director")

# ---------- 9. Profile dialog + Notification preferences dialog ----------
replace_once('app/workspace.tsx',
    '<Dialog open={teamOpen} onOpenChange={setTeamOpen}>',
    '''<Dialog open={profileOpen} onOpenChange={setProfileOpen}><DialogContent><DialogHeader><DialogTitle>My profile</DialogTitle><DialogDescription>Update your display name or password. Email cannot be changed here.</DialogDescription></DialogHeader><form className="form" onSubmit={async e=>{e.preventDefault();const f=new FormData(e.currentTarget);const name=String(f.get('name')||'').trim();const pw=String(f.get('password')||'');const pw2=String(f.get('password2')||'');if(name&&name!==data?.viewer.name){await mutate({action:'selfProfile',name})}if(pw){if(pw!==pw2){toast.error('Passwords do not match');return}if(pw.length<8){toast.error('Password must be at least 8 characters');return}const {error}=await browserClient().auth.updateUser({password:pw});if(error)toast.error(error.message);else toast.success('Password updated')}setProfileOpen(false)}}><label>Display name<input name="name" defaultValue={data?.viewer.name} required/></label><label>Email<input value={data?.viewer.email||''} disabled/></label><label>New password (leave blank to keep current)<input name="password" type="password" minLength={8}/></label><label>Confirm new password<input name="password2" type="password" minLength={8}/></label><button className="primary" disabled={busy}>Save changes</button></form></DialogContent></Dialog>
<Dialog open={notifyOpen} onOpenChange={setNotifyOpen}><DialogContent><DialogHeader><DialogTitle>Notification preferences</DialogTitle><DialogDescription>Choose which alerts you want. Assignment and status-change alerts are on by default.</DialogDescription></DialogHeader><form className="form" onSubmit={async e=>{e.preventDefault();const body=new FormData(e.currentTarget);if(await mutate({action:'notifyPrefs',assignment:body.has('assignment'),statusChange:body.has('statusChange'),manualEdit:body.has('manualEdit')}))setNotifyOpen(false)}}><label className="check"><input type="checkbox" name="assignment" defaultChecked={data?.viewer.notifyPrefs?.assignment!==false}/>Notify me when a ticket is assigned to me</label><label className="check"><input type="checkbox" name="statusChange" defaultChecked={data?.viewer.notifyPrefs?.statusChange!==false}/>Notify me when a ticket's status changes</label><label className="check"><input type="checkbox" name="manualEdit" defaultChecked={data?.viewer.notifyPrefs?.manualEdit===true}/>Notify me when someone edits my ticket (notes, priority)</label><button className="primary" disabled={busy}>Save preferences</button></form></DialogContent></Dialog>
<Dialog open={teamOpen} onOpenChange={setTeamOpen}>''',
    "workspace.tsx: add Profile and Notification preferences dialogs")

# ---------- version + changelog ----------
version_path = pathlib.Path('lib/version.ts')
if version_path.exists():
    version_path.write_text(f"export const APP_VERSION='{VERSION}';\n")
    print(f"OK: bumped lib/version.ts to {VERSION}")

replace_once('package.json', '"version": "2.0.9",', f'"version": "{VERSION}",', "package.json: bump version field")

changelog_path = pathlib.Path('CHANGELOG.md')
entry = f"""## {VERSION} - {TODAY}
- Added a global search bar in the top header covering investigations, contracts, and evidence
- Added a "My profile" dialog: edit display name and change password (email locked)
- Added a 24-hour session timeout for all roles except Vehicle, which never expires
- Added a Notification preferences dialog under Notifications
- Team lead and Director can now see and edit any member's access from the Teams & access page (except granting/modifying Administrator access)
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
