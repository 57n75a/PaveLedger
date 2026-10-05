#!/usr/bin/env python3
"""Custom roles, backend part (lib/domain.ts + lib/actions.ts).

Model: a custom role has a name, a built-in BASE role (which supplies workflow rules),
a visibility setting (base / own / team / all) and capability checkboxes.
Members keep role = the base role, so every existing role check keeps working,
and carry customRole = the custom role's name.

Run from the repo root. Aborts without writing if any anchor is not found exactly once."""
import re, sys, datetime

DOMAIN = 'lib/domain.ts'
ACTIONS = 'lib/actions.ts'
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

d = read(DOMAIN)
a = read(ACTIONS)

# ---------- lib/domain.ts ----------
d = swap(d,
  "vehicleTag?:string;notifyPrefs?:Record<string,boolean>;",
  "vehicleTag?:string;customRole?:string;visibility?:'own'|'team'|'all';notifyPrefs?:Record<string,boolean>;",
  'Member fields')

d = swap(d,
  "export type State={tickets:Ticket[],members:Member[]",
  "export type CustomRole={name:string,base:Role,visibility:'base'|'own'|'team'|'all',caps:string[]};\n"
  "export type State={tickets:Ticket[],members:Member[]",
  'CustomRole type')

d = swap(d,
  "rolePermissions?:Record<string,string[]>,branding?:",
  "rolePermissions?:Record<string,string[]>,customRoles?:CustomRole[],branding?:",
  'State.customRoles')

# visibility override for custom roles (not applied to Admin or Contractor)
d = swap(d,
  "export function canSee(t:Ticket,m:Member){if(!isActive(m))return false;",
  "export function canSee(t:Ticket,m:Member){if(!isActive(m))return false;"
  "if(m.visibility&&m.role!=='Admin'&&m.role!=='Contractor')return m.visibility==='all'||(m.visibility==='team'&&m.teams.includes(t.team))||(m.visibility==='own'&&(t.analyst===m.id||t.reportedBy===m.id));",
  'canSee override')

# capabilities of a custom role come from its own definition
d = swap(d,
  "export function roleCan(s:State,role:string,cap:Capability):boolean{const perms=s.rolePermissions?.[role];",
  "export function roleCan(s:State,role:string,cap:Capability):boolean{const cr=s.customRoles?.find(r=>r.name===role);if(cr)return cr.caps.includes(cap);const perms=s.rolePermissions?.[role];",
  'roleCan custom roles')

# ---------- lib/actions.ts ----------
# capability checks use the member's custom role when there is one
n_rc = a.count("roleCan(s,m.role,")
if n_rc < 1:
    die('no roleCan(s,m.role, calls found')
a = a.replace("roleCan(s,m.role,", "roleCan(s,m.customRole||m.role,")

# membership: accept a custom role name, store base role + customRole + visibility
a = swap(a,
  "role:z.enum(roles as [typeof roles[number],...typeof roles[number][]])",
  "role:z.string().trim().min(1).max(60)",
  'member role field')

a = swap(a,
  "authUserId:z.string().uuid(),active:z.boolean()}).parse(body);",
  "authUserId:z.string().uuid(),active:z.boolean()}).parse(body);\n"
  "  const cr=(s.customRoles||[]).find(x=>x.name===v.role);if(!cr&&!(roles as readonly string[]).includes(v.role))throw new AppError('Unknown role.');if(cr)v.role=cr.base;",
  'member role resolve')

a = swap(a,
  "const clean={...v,teams:",
  "const clean={...v,role:v.role as Member['role'],customRole:cr?.name,visibility:cr&&cr.visibility!=='base'?cr.visibility:undefined,teams:",
  'member clean object')

a = swap(a,
  "; role ${v.role}; active ${v.active}",
  "; role ${cr?cr.name:v.role}; active ${v.active}",
  'member event text')

# custom role save and delete (Admin only), inserted before the rolePermissions action
CUSTOM = (
"if(action==='customRoleSave'){requireRole(['Admin']);"
"const bases=['Team lead','Analyst','Head Analyst','Reviewer','Contractor','Auditor','Director'] as const;"
"const v=z.object({name:z.string().trim().min(2).max(40).regex(/^[A-Za-z0-9][A-Za-z0-9 _-]*$/,'Use letters, numbers, spaces, - and _ only.'),previous:z.string().trim().max(40).optional(),base:z.enum(bases),visibility:z.enum(['base','own','team','all']),caps:z.array(z.string()).max(20)}).parse(body);"
"if((roles as readonly string[]).some(r=>r.toLowerCase()===v.name.toLowerCase()))throw new AppError('That name is used by a built-in role.');"
"const list=s.customRoles||[];const prev=v.previous?list.find(r=>r.name===v.previous):undefined;if(v.previous&&!prev)throw new AppError('Role not found.');"
"if(list.some(r=>r!==prev&&r.name.toLowerCase()===v.name.toLowerCase()))throw new AppError('A custom role with that name already exists.');"
"if(!prev&&list.length>=20)throw new AppError('Limit of 20 custom roles reached.');"
"if(prev&&prev.base!==v.base&&s.members.some(x=>x.customRole===prev.name))throw new AppError('Reassign the members using this role before changing its base role.');"
"const def={name:v.name,base:v.base,visibility:(v.base==='Contractor'?'base':v.visibility) as 'base'|'own'|'team'|'all',caps:v.caps.filter(c=>(CAPABILITIES as readonly string[]).includes(c))};"
"s.customRoles=prev?list.map(r=>r===prev?def:r):[...list,def];"
"for(const x of s.members){if(x.customRole===(prev?prev.name:v.name)){x.customRole=def.name;x.role=def.base;x.visibility=def.visibility==='base'?undefined:def.visibility}}"
"event='Custom role saved: '+def.name;s.events.unshift({at:now,actor,action:event});return}"
"if(action==='customRoleDelete'){requireRole(['Admin']);const name=short.parse(body.name);const list=s.customRoles||[];if(!list.some(r=>r.name===name))throw new AppError('Role not found.');"
"const used=s.members.filter(x=>x.customRole===name).length;if(used)throw new AppError(`Reassign the ${used} member(s) using this role before deleting it.`);"
"s.customRoles=list.filter(r=>r.name!==name);event='Custom role deleted: '+name;s.events.unshift({at:now,actor,action:event});return}\n  "
)
a = swap(a,
  "if(action==='rolePermissions'){requireRole(['Admin']);",
  CUSTOM + "if(action==='rolePermissions'){requireRole(['Admin']);",
  'custom role actions')

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
         '- Custom roles (backend): Admin can create, edit and delete roles with a base role, a visibility setting (base, own, team, all) and capability checkboxes.\n'
         '- Memberships can be assigned a custom role; the member keeps the base role for workflow rules.\n'
         '- Capability checks (create, comment, assign, escalate, archive, contracts) now use the custom role when a member has one.\n\n')
c = c[:h.start()] + entry + c[h.start():]

open(DOMAIN, 'w', encoding='utf-8').write(d)
open(ACTIONS, 'w', encoding='utf-8').write(a)
open(VERSION, 'w', encoding='utf-8').write(v)
open(CHANGELOG, 'w', encoding='utf-8').write(c)
print(f'OK: {old_v} -> {new_v} (roleCan call sites updated: {n_rc}). Now run: npm run build')
