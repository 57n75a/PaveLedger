import pathlib, re
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

VERSION = "2.4.1"
TODAY = date.today().isoformat()

# ---------- 1. Module-level constants: capability labels + client-side defaults (mirrors the backend) ----------
replace_once('app/workspace.tsx',
    "const ScopeLocator=dynamic(()=>import('@/components/scope-locator'),{ssr:false,loading:()=><p className=\"muted\">Loading map...</p>});",
    '''const ScopeLocator=dynamic(()=>import('@/components/scope-locator'),{ssr:false,loading:()=><p className="muted">Loading map...</p>});
const CAPABILITIES=[{key:'create',label:'Create tickets'},{key:'comment',label:'Add comments'},{key:'assign',label:'Assign tickets'},{key:'escalate',label:'Escalate tickets'},{key:'archive',label:'Archive directly'},{key:'contracts',label:'Manage contracts'}];
const DEFAULT_CAPS:Record<string,string[]>={Admin:['create','comment','assign','archive','contracts'],'Team lead':['create','comment','assign','escalate','archive'],Analyst:['create','comment'],'Head Analyst':['comment','escalate'],Reviewer:['comment'],Contractor:[],Auditor:[],Vehicle:[],Director:['archive']};''',
    "workspace.tsx: capability labels and client-side defaults")

# ---------- 2. Restructure the Users and Roles page into two tabs, rename member -> user text ----------
OLD_SECTION = '''{view==='Users and Roles'&&<section className="panel"><div className="section-head"><div><h2>Roles and permissions</h2><p>{['Admin','Team lead','Director'].includes(role||'')?'Bind verified accounts, set roles and suspend access.':'Membership shown within your permitted scope.'}</p></div>{role==='Admin'&&<button className="primary" onClick={()=>setMemberOpen(true)}>Add member</button>}</div><Table><TableHeader><TableRow><TableHead>Member</TableHead><TableHead>Role</TableHead><TableHead>Scope</TableHead><TableHead>Access</TableHead><TableHead>Manage</TableHead></TableRow></TableHeader><TableBody>{data.members.map(m=><TableRow key={m.id}><TableCell><strong>{m.name}</strong><small className="block muted">{m.email}</small></TableCell><TableCell>{m.role}</TableCell><TableCell>{(m.teams||[]).join(', ')||m.contractor||'Organization'}</TableCell><TableCell>{{Admin:'Manage organization and all cases','Team lead':'Assign and manage team cases',Analyst:'Investigate assigned cases','Head Analyst':'Oversees team analysts and escalates cases',Reviewer:'Independently verify team repairs',Contractor:'Update assigned repairs',Auditor:'Read permitted records',Vehicle:'Reports detected road defects',Director:'Receives escalated cases across teams'}[m.role]} \u00b7 {isActive(m)?'Active':'Suspended'}</TableCell><TableCell>{['Admin','Team lead','Director'].includes(role||'')&&<button className="secondary" onClick={()=>setEditingMember(m)}>Edit access</button>}</TableCell></TableRow>)}</TableBody></Table><p className="footnote">Server permissions apply to all reads and updates. Role preview is an owner-admin demonstration feature. New memberships also require a verified sign-in account provisioned by your administrator.</p></section>}'''

NEW_SECTION = '''{view==='Users and Roles'&&<section className="panel"><Tabs defaultValue="users"><TabsList><TabsTrigger value="users">Users</TabsTrigger><TabsTrigger value="roles">Roles</TabsTrigger></TabsList><TabsContent value="users"><div className="section-head"><div><h2>Users</h2><p>{['Admin','Team lead','Director'].includes(role||'')?'Bind verified accounts, set roles and suspend access.':'User list shown within your permitted scope.'}</p></div>{role==='Admin'&&<button className="primary" onClick={()=>setMemberOpen(true)}>Add user</button>}</div><Table><TableHeader><TableRow><TableHead>User</TableHead><TableHead>Role</TableHead><TableHead>Scope</TableHead><TableHead>Access</TableHead><TableHead>Manage</TableHead></TableRow></TableHeader><TableBody>{data.members.map(m=><TableRow key={m.id}><TableCell><strong>{m.name}</strong><small className="block muted">{m.email}</small></TableCell><TableCell>{m.role}</TableCell><TableCell>{(m.teams||[]).join(', ')||m.contractor||'Organization'}</TableCell><TableCell>{{Admin:'Manage organization and all cases','Team lead':'Assign and manage team cases',Analyst:'Investigate assigned cases','Head Analyst':'Oversees team analysts and escalates cases',Reviewer:'Independently verify team repairs',Contractor:'Update assigned repairs',Auditor:'Read permitted records',Vehicle:'Reports detected road defects',Director:'Receives escalated cases across teams'}[m.role]} \u00b7 {isActive(m)?'Active':'Suspended'}</TableCell><TableCell>{['Admin','Team lead','Director'].includes(role||'')&&<button className="secondary" onClick={()=>setEditingMember(m)}>Edit access</button>}</TableCell></TableRow>)}</TableBody></Table><p className="footnote">Server permissions apply to all reads and updates. Role preview is an owner-admin demonstration feature. New user accounts also require a verified sign-in account provisioned by your administrator.</p></TabsContent><TabsContent value="roles"><p className="footnote">Configure which day-to-day actions each role can take. Administrator-only safeguards \u2014 granting Administrator access, closing or verifying tickets, deleting teams \u2014 are fixed and cannot be changed here.</p><Table><TableHeader><TableRow><TableHead>Role</TableHead>{CAPABILITIES.map(c=><TableHead key={c.key}>{c.label}</TableHead>)}</TableRow></TableHeader><TableBody>{roles.map(r=>{const caps=data.rolePermissions?.[r]??DEFAULT_CAPS[r]??[];return <TableRow key={r}><TableCell><strong>{r}</strong></TableCell>{CAPABILITIES.map(c=><TableCell key={c.key}><Checkbox checked={caps.includes(c.key)} disabled={role!=='Admin'||busy} onCheckedChange={v=>{const updated:Record<string,string[]>={};roles.forEach(rr=>{updated[rr]=data.rolePermissions?.[rr]??DEFAULT_CAPS[rr]??[]});updated[r]=v?[...caps,c.key]:caps.filter((x:string)=>x!==c.key);mutate({action:'rolePermissions',permissions:updated})}}/></TableCell>)}</TableRow>})}</TableBody></Table></TabsContent></Tabs></section>}'''

replace_once('app/workspace.tsx', OLD_SECTION, NEW_SECTION, "workspace.tsx: two-tab Users/Roles page with live capability matrix")

# ---------- 3. Rename member -> user text elsewhere (dialogs, forms) ----------
replace_once('app/workspace.tsx',
    '<DialogTitle>Add member</DialogTitle><DialogDescription>Set access for a verified sign-in email. No invitation is sent.</DialogDescription>',
    '<DialogTitle>Add user</DialogTitle><DialogDescription>Set access for a verified sign-in email. No invitation is sent.</DialogDescription>',
    "workspace.tsx: Add member dialog -> Add user")

replace_once('app/workspace.tsx',
    '<DialogTitle>Edit member access</DialogTitle>',
    '<DialogTitle>Edit user access</DialogTitle>',
    "workspace.tsx: Edit member access dialog -> Edit user access")

replace_once('app/workspace.tsx',
    "{initial?'Save access':'Add membership'}",
    "{initial?'Save access':'Add user'}",
    "workspace.tsx: MemberForm submit button -> Add user")

replace_once('app/workspace.tsx',
    '<DialogTitle>Manage {managingTeam}</DialogTitle><DialogDescription>Add or remove members from this team.</DialogDescription>',
    '<DialogTitle>Manage {managingTeam}</DialogTitle><DialogDescription>Add or remove users from this team.</DialogDescription>',
    "workspace.tsx: team management dialog description")

replace_once('app/workspace.tsx',
    '<h3>Current members</h3>',
    '<h3>Current users</h3>',
    "workspace.tsx: 'Current members' -> 'Current users'")

replace_once('app/workspace.tsx',
    "<p className=\"muted\">No members in this team yet.</p>",
    "<p className=\"muted\">No users in this team yet.</p>",
    "workspace.tsx: 'No members' -> 'No users'")

replace_once('app/workspace.tsx',
    '<h3>Add a member</h3>',
    '<h3>Add a user</h3>',
    "workspace.tsx: 'Add a member' -> 'Add a user'")

replace_once('app/workspace.tsx',
    "<button className=\"secondary\" onClick={()=>setManagingTeam(team)}>Manage members</button>",
    "<button className=\"secondary\" onClick={()=>setManagingTeam(team)}>Manage users</button>",
    "workspace.tsx: 'Manage members' -> 'Manage users' button")

replace_once('app/workspace.tsx',
    "<small style={{fontSize:13,color:'#6b7280'}}>{count} active member{count===1?'':'s'}</small>",
    "<small style={{fontSize:13,color:'#6b7280'}}>{count} active user{count===1?'':'s'}</small>",
    "workspace.tsx: team card 'active member(s)' -> 'active user(s)' (if present)")

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
- "Users and Roles" is now two tabs: Users (the member list, renamed from "members" throughout) and Roles (the new live capability matrix)
- Admin can toggle role capabilities directly in the Roles tab; changes save immediately per checkbox
"""
if changelog_path.exists():
    existing = changelog_path.read_text()
    if f"## {VERSION}" not in existing:
        changelog_path.write_text(entry + "\n" + existing)
        print(f"OK: prepended {VERSION} entry to CHANGELOG.md")

print("\nDone. Now run:")
print("  npm run build")
