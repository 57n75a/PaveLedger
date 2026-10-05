#!/usr/bin/env python3
"""Custom roles UI + Admin delete user.
  - Roles tab: add / edit / delete custom roles (base role, visibility, allowed actions)
  - User form: custom roles appear in the Role dropdown; Users table shows the custom role name
  - Users table: Admin 'Delete' button (server-side safeguards in lib/actions.ts)
Requires patch_custom_roles_backend.py to have been applied first.
Run from the repo root. Aborts without writing if any anchor is not found exactly once."""
import re, sys, datetime

WS = 'app/workspace.tsx'
ACTIONS = 'lib/actions.ts'
DOMAIN = 'lib/domain.ts'
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

if 'customRoles?:CustomRole[]' not in read(DOMAIN):
    die('lib/domain.ts has no customRoles support. Run patch_custom_roles_backend.py first.')

w = read(WS)
a = read(ACTIONS)

# ---------- lib/actions.ts: memberDelete ----------
DELETE = (
"}else if(action==='memberDelete'){\n"
"  requireRole(['Admin']);if(actual.id!==m.id)throw new AppError('Return to your own identity before changing access.',403);\n"
"  const delId=short.parse(body.memberId);const target=s.members.find(x=>x.id===delId);if(!target)throw new AppError('Member not found.');\n"
"  if(target.id===actual.id||target.id===ownerId)throw new AppError('You cannot delete your own account or the designated owner identity.');\n"
"  if(target.role==='Admin'&&isActive(target)&&s.members.filter(x=>x.role==='Admin'&&isActive(x)).length<=1)throw new AppError('Keep at least one active administrator.');\n"
"  if(s.tickets.some(t=>t.analyst===delId||t.reportedBy===delId||(t.evidence||[]).some(e=>e.uploadedBy===delId)))throw new AppError('This user appears in ticket records. Suspend the account instead of deleting it so the audit trail stays intact.');\n"
"  s.members=s.members.filter(x=>x.id!==delId);s.notifications=s.notifications.filter(n=>n.recipient!==delId);event='Membership deleted: '+target.name;\n"
" "
)
a = swap(a,
  "}else if(action==='member'||action==='memberUpdate'){",
  DELETE + "}else if(action==='member'||action==='memberUpdate'){",
  'memberDelete action')

# ---------- app/workspace.tsx ----------
# member form: role is a string (built-in or custom name); 'base' drives firm/vehicle fields
w = swap(w,
  "const [role,setRole]=useState(initial?.role||'Analyst')",
  "const [role,setRole]=useState<string>(initial?.customRole||initial?.role||'Analyst')",
  'member form role state')
w = swap(w,
  "[active,setActive]=useState(initial?.active!==false);return <form",
  "[active,setActive]=useState(initial?.active!==false),base=(data.customRoles||[]).find(r=>r.name===role)?.base||role;return <form",
  'member form base role')
w = swap(w,
  """<Pick label="Role" value={role} onChange={v=>setRole(v as Member['role'])} items={roles.map(x=>({value:x,label:x}))}/>""",
  """<Pick label="Role" value={role} onChange={v=>setRole(v)} items={[...roles.map(x=>({value:x as string,label:x as string})),...(data.customRoles||[]).map(x=>({value:x.name,label:x.name+' (custom)'}))]}/>""",
  'member form role dropdown')
w = swap(w,
  """{role==='Contractor'&&<Pick label="Firm\"""",
  """{base==='Contractor'&&<Pick label="Firm\"""",
  'member form firm field')

# Users table: show the custom role name; Admin delete button
w = swap(w,
  "<TableCell>{m.role}</TableCell><TableCell>{(m.teams||[]).join(', ')",
  "<TableCell>{m.customRole||m.role}</TableCell><TableCell>{(m.teams||[]).join(', ')",
  'users table role cell')
w = swap(w,
  "onClick={()=>setEditingMember(m)}>Edit access</button>}</TableCell>",
  "onClick={()=>setEditingMember(m)}>Edit access</button>}{role==='Admin'&&m.id!==data.viewer.id&&<button className=\"secondary\" disabled={busy} onClick={()=>{if(confirm('Delete '+m.name+'? This removes their membership permanently. If they appear in ticket records, suspend them instead.'))mutate({action:'memberDelete',memberId:m.id})}}>Delete</button>}</TableCell>",
  'users table delete button')

# Roles tab: custom roles panel under the built-in roles table
w = swap(w,
  "</TableRow>})}</TableBody></Table></TabsContent></Tabs></section>}",
  "</TableRow>})}</TableBody></Table><CustomRolesPanel data={data} isAdmin={role==='Admin'} busy={busy} mutate={mutate}/></TabsContent></Tabs></section>}",
  'roles tab panel mount')

PANEL = r"""
function CustomRolesPanel({data,isAdmin,busy,mutate}:{data:Data,isAdmin:boolean,busy:boolean,mutate:(b:any)=>Promise<boolean>}){
const BASES=['Team lead','Analyst','Head Analyst','Reviewer','Contractor','Auditor','Director'];
const VIS:Record<string,string>={base:'Same as base role',own:'Own tickets only',team:"Own teams' tickets",all:'All tickets'};
const [draft,setDraft]=useState<null|{previous:string,name:string,base:string,visibility:string,caps:string[]}>(null);
const list=data.customRoles||[];
const usedBy=(n:string)=>data.members.filter(m=>m.customRole===n).length;
return <div style={{marginTop:28}}>
<div className="section-head"><div><h2>Custom roles</h2><p>Create your own roles. Each one is based on a built-in role, which sets the workflow rules, and has its own visibility and allowed actions.</p></div>{isAdmin&&!draft&&<button className="primary" onClick={()=>setDraft({previous:'',name:'',base:'Analyst',visibility:'base',caps:['comment']})}>Add role</button>}</div>
{!list.length&&!draft&&<p className="muted">No custom roles yet.</p>}
{!!list.length&&<Table><TableHeader><TableRow><TableHead>Role</TableHead><TableHead>Based on</TableHead><TableHead>Visibility</TableHead><TableHead>Allowed actions</TableHead><TableHead>Users</TableHead><TableHead/></TableRow></TableHeader><TableBody>{list.map(r=><TableRow key={r.name}><TableCell><strong>{r.name}</strong></TableCell><TableCell>{r.base}</TableCell><TableCell>{VIS[r.visibility]||r.visibility}</TableCell><TableCell>{CAPABILITIES.filter(c=>r.caps.includes(c.key)).map(c=>c.label).join(', ')||'None'}</TableCell><TableCell>{usedBy(r.name)}</TableCell><TableCell>{isAdmin&&<div className="button-row"><button className="secondary" disabled={busy} onClick={()=>setDraft({previous:r.name,name:r.name,base:r.base,visibility:r.visibility,caps:[...r.caps]})}>Edit</button><button className="secondary" disabled={busy} onClick={()=>{if(confirm('Delete custom role "'+r.name+'"?'))mutate({action:'customRoleDelete',name:r.name})}}>Delete</button></div>}</TableCell></TableRow>)}</TableBody></Table>}
{draft&&<form className="form" onSubmit={async e=>{e.preventDefault();if(await mutate({action:'customRoleSave',name:draft.name,previous:draft.previous||undefined,base:draft.base,visibility:draft.visibility,caps:draft.caps}))setDraft(null)}}>
<label>Role name<input required minLength={2} maxLength={40} value={draft.name} onChange={e=>setDraft({...draft,name:e.target.value})} placeholder="e.g. Field inspector"/></label>
<p className="footnote">Based on (sets which stages this role can move tickets between)</p>
<Pick label="Based on" value={draft.base} onChange={v=>setDraft({...draft,base:v})} items={BASES.map(x=>({value:x,label:x}))}/>
<p className="footnote">Which tickets this role can see (does not apply when based on Contractor)</p>
<Pick label="Visibility" value={draft.visibility} onChange={v=>setDraft({...draft,visibility:v})} items={Object.entries(VIS).map(([value,label])=>({value,label}))}/>
<div className="form"><p className="footnote">Allowed actions</p>{CAPABILITIES.map(c=><label className="check" key={c.key}><Checkbox checked={draft.caps.includes(c.key)} onCheckedChange={v=>setDraft({...draft,caps:v?[...draft.caps,c.key]:draft.caps.filter(x=>x!==c.key)})}/>{c.label}</label>)}</div>
<div className="button-row"><button className="primary" disabled={busy}>Save role</button><button type="button" className="secondary" onClick={()=>setDraft(null)}>Cancel</button></div>
</form>}
<p className="footnote">A role cannot be deleted, or have its base role changed, while users are assigned to it. Administrator-only safeguards still apply to every role.</p>
</div>}
"""
w = swap(w,
  "\nfunction EvidencePanel(",
  PANEL + "function EvidencePanel(",
  'custom roles panel definition')

# ---------- version + changelog ----------
v = read(VERSION)
found = re.findall(r'\d+\.\d+\.\d+', v)
if len(found) != 1:
    die(f'{VERSION}: expected exactly one x.y.z, found {found}')
old_v = found[0]
maj, mnr, pat = map(int, old_v.split('.'))
new_v = f'{maj}.{mnr}.{pat + 1}'
v = v.replace(old_v, new_v)

c = read(CHANGELOG)
h = re.search(r'^## .*$', c, re.M)
if not h:
    die(f'{CHANGELOG}: no "## " heading found to insert before')
print('Top existing changelog heading:', h.group(0))
entry = (f'## {new_v} - {datetime.date.today().isoformat()}\n'
         '- Roles tab: Admin can add, edit and delete custom roles (base role, visibility, allowed actions).\n'
         '- User form: custom roles appear in the Role dropdown; the Users table shows the custom role name.\n'
         '- Users: Admin can delete a user. Blocked for yourself, the owner identity, the last active Admin, and anyone who appears in ticket records (suspend them instead).\n\n')
c = c[:h.start()] + entry + c[h.start():]

open(WS, 'w', encoding='utf-8').write(w)
open(ACTIONS, 'w', encoding='utf-8').write(a)
open(VERSION, 'w', encoding='utf-8').write(v)
open(CHANGELOG, 'w', encoding='utf-8').write(c)
print(f'OK: {old_v} -> {new_v}. Now run: npm run build')
